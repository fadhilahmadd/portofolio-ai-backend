import json
from typing import Dict, List, Optional, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from app.core.config import settings
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


class ChatService:
    """
    Asynchronous service to handle chat logic using a RAG pipeline.
    Delegates stream processing to _ChatStreamManager for cleaner execution.
    """
    def __init__(self):
        self.store: Dict[str, ChatMessageHistory] = {}
        self.UserIntent = UserIntent

        self.llm = None
        self.retriever = None
        self.chain_cache: Dict[str, RunnableWithMessageHistory] = {}
        if settings.GOOGLE_API_KEY:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0.3,
            )
            try:
                self.retriever = get_retriever()
            except Exception as e:
                print(f"Error initializing retriever: {e}")
        else:
            # Defer full initialization to runtime if key is provided later
            self.llm = None
            self.retriever = None

    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]

    def _build_rag_chain(self, system_prompt: str) -> RunnableWithMessageHistory:
        """Constructs the complete LangChain RAG chain."""
        qa_prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt), MessagesPlaceholder("chat_history"), ("human", "{input}")]
        )

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
        if system_prompt not in self.chain_cache:
            self.chain_cache[system_prompt] = self._build_rag_chain(system_prompt)
        return self.chain_cache[system_prompt]

    def _basic_intent_classification(self, message: str) -> UserIntent:
        msg = message.lower()
        if "email" in msg:
            return UserIntent.CREATE_EMAIL
        if any(keyword in msg for keyword in ["hire", "hiring", "recruiter", "role", "position"]):
            return UserIntent.RECRUITER
        return UserIntent.GENERAL_INQUIRY

    async def _get_user_intent(self, message: str) -> UserIntent:
        if not self.llm:
            return self._basic_intent_classification(message)

        prompt = ChatPromptTemplate.from_template(INTENT_CLASSIFICATION_PROMPT_TEMPLATE)
        chain = prompt | self.llm
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
        if not self.llm:
            return None

        prompt = ChatPromptTemplate.from_template(SUGGESTED_QUESTIONS_PROMPT_TEMPLATE)
        chain = prompt | self.llm
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

    async def _log_conversation(
        self,
        db: AsyncSession,
        session_id: str,
        user_message: str,
        ai_response: str,
        suggested_questions: Optional[List[str]],
        mailto: Optional[str] = None
    ):
        """
        Asynchronously logs the complete conversation details to the database.
        """
        conversation_data = ConversationCreate(
            session_id=session_id,
            user_message=user_message,
            ai_response=ai_response,
            suggested_questions=suggested_questions,
            mailto=mailto
        )
        await crud_conversation.create_conversation(db, conversation_data)

    async def stream_response(
        self,
        session_id: str,
        message: str,
        db: AsyncSession
    ) -> AsyncGenerator[str, None]:
        """
        Initializes and runs the stream manager for a chat request.
        """
        manager = _ChatStreamManager(self, session_id, message, db)
        async for event in manager.process():
            yield event


chat_service = ChatService()

def get_chat_service() -> ChatService:
    return chat_service
