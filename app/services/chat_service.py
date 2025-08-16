import os
import json
import threading
import asyncio
import aiofiles
from uuid import uuid4
from typing import Dict, List, Optional, AsyncGenerator

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from app.core.config import settings
from app.core.database import async_session
from app.core.knowledge import get_retriever
from app.api.v1.schemas.chat import UserIntent
from app.core.prompts import (
    SUGGESTED_QUESTIONS_PROMPT_TEMPLATE,
    INTENT_CLASSIFICATION_PROMPT_TEMPLATE,
    CONTEXTUALIZE_Q_SYSTEM_PROMPT,
)
from app.crud import crud_conversation
from app.api.v1.schemas.analytics import ConversationCreate
from app.services.stream_manager import _ChatStreamManager

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static')
AUDIO_DIR = os.path.join(STATIC_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

class ChatService:
    """
    Asynchronous service to handle chat logic using a RAG pipeline.
    Delegates stream processing to _ChatStreamManager for cleaner execution.
    """
    def __init__(self):
        self.store: Dict[str, ChatMessageHistory] = {}
        self._store_lock: threading.RLock = threading.RLock()

        self.chain_cache: Dict[str, RunnableWithMessageHistory] = {}
        self._chain_cache_lock: threading.RLock = threading.RLock()

        self._session_locks: Dict[str, asyncio.Lock] = {}
        self._session_locks_guard: threading.RLock = threading.RLock()

        self.UserIntent = UserIntent

        self.llm = None
        self.retriever = None
        self.helper_llm = None

        if settings.GOOGLE_API_KEY:
            # The main, powerful LLM for generating high-quality answers
            self.llm = ChatGoogleGenerativeAI(
                model=settings.MAIN_LLM_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0.3,
            )
            # A separate, faster LLM for simple, internal tasks
            self.helper_llm = ChatGoogleGenerativeAI(
                model=settings.HELPER_LLM_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0,
            )
            try:
                self.retriever = get_retriever()
            except Exception as e:
                print(f"Error initializing retriever: {e}")
        else:
            self.llm = None
            self.helper_llm = None
            self.retriever = None

    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        with self._store_lock:
            if session_id not in self.store:
                self.store[session_id] = ChatMessageHistory()
            return self.store[session_id]

    def get_session_lock(self, session_id: str) -> asyncio.Lock:
        """Return an asyncio lock that serializes access to a session's chat history."""
        with self._session_locks_guard:
            lock = self._session_locks.get(session_id)
            if lock is None:
                lock = asyncio.Lock()
                self._session_locks[session_id] = lock
            return lock

    def _build_rag_chain(self, system_prompt: str) -> RunnableWithMessageHistory:
        """
        Constructs the complete LangChain RAG chain using a direct multilingual retriever.
        """
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", CONTEXTUALIZE_Q_SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, contextualize_q_prompt
        )

        qa_prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt), MessagesPlaceholder("chat_history"), ("human", "{input}")]
        )
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        return RunnableWithMessageHistory(
            rag_chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

    def get_rag_chain(self, system_prompt: str) -> RunnableWithMessageHistory:
        """Returns a cached RAG chain for the given system prompt."""
        if not self.llm or not self.retriever:
            raise RuntimeError("LLM or retriever not initialized")
        chain = self.chain_cache.get(system_prompt)
        if chain is not None:
            return chain
        with self._chain_cache_lock:
            chain = self.chain_cache.get(system_prompt)
            if chain is None:
                chain = self._build_rag_chain(system_prompt)
                self.chain_cache[system_prompt] = chain
            return chain

    def _basic_intent_classification(self, message: str) -> UserIntent:
        msg = message.lower()
        if "email" in msg:
            return UserIntent.CREATE_EMAIL
        if any(keyword in msg for keyword in ["hire", "hiring", "recruiter", "role", "position"]):
            return UserIntent.RECRUITER
        return UserIntent.GENERAL_INQUIRY

    async def _get_user_intent(self, message: str) -> UserIntent:
        # Use the faster helper_llm for this task
        if not self.helper_llm:
            return self._basic_intent_classification(message)

        prompt = ChatPromptTemplate.from_template(INTENT_CLASSIFICATION_PROMPT_TEMPLATE)
        chain = prompt | self.helper_llm
        try:
            response = await chain.ainvoke({"question": message})
            intent_str = response.content.strip().lower()
            if "create_email" in intent_str:
                return UserIntent.CREATE_EMAIL
            if "recruiter" in intent_str:
                return UserIntent.RECRUITER
            return UserIntent.GENERAL_INQUIRY
        except Exception as e:
            print(f"Error classifying user intent: {e}")
            return self._basic_intent_classification(message)

    async def _generate_suggested_questions(self, question: str, answer: str) -> Optional[List[str]]:
        if not self.helper_llm:
            return None

        prompt = ChatPromptTemplate.from_template(SUGGESTED_QUESTIONS_PROMPT_TEMPLATE)
        chain = prompt | self.helper_llm
        try:
            response = await chain.ainvoke({"question": question, "answer": answer})
            content = response.content
            cleaned_content = content.strip().lstrip("```json").lstrip("```").rstrip("```")
            suggestions = json.loads(cleaned_content)
            if isinstance(suggestions, list) and all(isinstance(q, str) for q in suggestions):
                return suggestions
            return None
        except Exception as e:
            print(f"Error parsing suggested questions JSON: {e}")
            return None

    async def log_conversation_task(
        self,
        session_id: str,
        user_message: str,
        ai_response: str,
        suggested_questions: Optional[List[str]],
        mailto: Optional[str] = None,
        user_audio_bytes: Optional[bytes] = None,
        ai_audio_bytes: Optional[bytes] = None,
    ):
        """
        This background task saves audio files and logs the full conversation to the DB.
        """
        user_audio_path = None
        ai_audio_path = None

        async def save_audio(content: bytes, extension: str) -> str:
            """Saves audio content to a file and returns its relative path."""
            filename = f"{session_id}_{uuid4()}.{extension}"
            file_path = os.path.join(AUDIO_DIR, filename)
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)
            return os.path.join("audio", filename)

        try:
            save_tasks = []
            if user_audio_bytes:
                save_tasks.append(save_audio(user_audio_bytes, "wav"))
            if ai_audio_bytes:
                save_tasks.append(save_audio(ai_audio_bytes, "mp3"))
            
            results = await asyncio.gather(*save_tasks)
            
            path_idx = 0
            if user_audio_bytes:
                user_audio_path = results[path_idx]
                path_idx += 1
            if ai_audio_bytes:
                ai_audio_path = results[path_idx]

            conversation_data = ConversationCreate(
                session_id=session_id,
                user_message=user_message,
                ai_response=ai_response,
                suggested_questions=suggested_questions,
                mailto=mailto,
                user_audio_path=user_audio_path,
                ai_audio_path=ai_audio_path,
            )
            async with async_session() as db:
                await crud_conversation.create_conversation(db, conversation_data)
        except Exception as e:
            print(f"Error in background logging task: {e}")

    async def stream_response(
        self,
        session_id: str,
        message: str,
    ) -> AsyncGenerator[str, None]:
        """
        Initializes and runs the stream manager for a chat request.
        Logging is now handled by a background task in the API endpoint.
        """
        manager = _ChatStreamManager(self, session_id, message)
        async for event in manager.process():
            yield event


chat_service = ChatService()

def get_chat_service() -> ChatService:
    return chat_service
