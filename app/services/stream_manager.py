import json
import asyncio
from typing import TYPE_CHECKING, AsyncGenerator, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.core.prompts import (
    CONTEXTUALIZE_Q_SYSTEM_PROMPT,
    HIRING_MANAGER_SYSTEM_PROMPT_TEMPLATE,
    SYSTEM_PROMPT_TEMPLATE
)

if TYPE_CHECKING:
    from app.services.chat_service import ChatService


class _ChatStreamManager:
    """
    Manages the state and execution flow for a single chat stream request.
    This encapsulates the logic for streaming, suggestion generation, and logging.
    """
    def __init__(self, service: 'ChatService', session_id: str, message: str, db: AsyncSession):
        self.service = service
        self.session_id = session_id
        self.message = message
        self.db = db
        self.full_answer = ""
        self.suggested_questions: Optional[List[str]] = None

    async def process(self) -> AsyncGenerator[str, None]:
        """
        Main processing generator that yields SSE events.
        """
        try:
            user_intent = await self.service._get_user_intent(self.message)
            system_prompt = HIRING_MANAGER_SYSTEM_PROMPT_TEMPLATE if user_intent == self.service.UserIntent.RECRUITER else SYSTEM_PROMPT_TEMPLATE

            conversational_rag_chain = self._build_rag_chain(system_prompt)

            async for token in self._stream_answer(conversational_rag_chain):
                yield token
            
            self.suggested_questions = await self.service._generate_suggested_questions(self.message, self.full_answer)

            asyncio.create_task(
                self.service._log_conversation(
                    self.db,
                    self.session_id,
                    self.message,
                    self.full_answer,
                    self.suggested_questions
                )
            )

            final_data = json.dumps({"suggested_questions": self.suggested_questions})
            yield f"event: final\ndata: {final_data}\n\n"

        except Exception as e:
            print(f"An error occurred during the stream processing: {e}")
            error_data = json.dumps({"error": "An error occurred while processing your request."})
            yield f"event: error\ndata: {error_data}\n\n"

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
            self.service.llm, self.service.retriever, contextualize_q_prompt
        )
        
        question_answer_chain = create_stuff_documents_chain(self.service.llm, qa_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        return RunnableWithMessageHistory(
            rag_chain,
            self.service.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

    async def _stream_answer(self, chain: RunnableWithMessageHistory) -> AsyncGenerator[str, None]:
        """Streams the main response from the RAG chain."""
        async for chunk in chain.astream(
            {"input": self.message},
            config={"configurable": {"session_id": self.session_id}},
        ):
            if answer_chunk := chunk.get("answer"):
                self.full_answer += answer_chunk
                data = json.dumps({"token": answer_chunk})
                yield f"event: token\ndata: {data}\n\n"
