import json
import asyncio
from typing import TYPE_CHECKING, AsyncGenerator, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.runnables.history import RunnableWithMessageHistory

from app.core.prompts import (
    HIRING_MANAGER_SYSTEM_PROMPT_TEMPLATE,
    SYSTEM_PROMPT_TEMPLATE,
)
from app.core.utils import create_mailto_link

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
        self.mailto_link: Optional[str] = None

    async def process(self) -> AsyncGenerator[str, None]:
        """
        Main processing generator that yields SSE events.
        """
        try:
            session_lock = self.service.get_session_lock(self.session_id)
            async with session_lock:
                user_intent = await self.service._get_user_intent(self.message)
            
            if user_intent == self.service.UserIntent.CREATE_EMAIL:
                self.full_answer = "Great! I've prepared an email for you. Please click the link to open it in your email client."
                self.mailto_link = create_mailto_link(
                    email="fadhilhidayat27@gmail.com",
                    subject="Job Opportunity Discussion",
                    body="Hello Fadhil,\n\nI came across your portfolio and would like to discuss a potential opportunity. Are you available for a brief chat next week?\n\nBest regards,"
                )
                yield f"event: token\ndata: {json.dumps({'token': self.full_answer})}\n\n"
            else:
                system_prompt = (
                    HIRING_MANAGER_SYSTEM_PROMPT_TEMPLATE
                    if user_intent == self.service.UserIntent.RECRUITER
                    else SYSTEM_PROMPT_TEMPLATE
                )
                conversational_rag_chain = self.service.get_rag_chain(system_prompt)
                # streaming can proceed without holding the lock, but chain uses
                # per-session history internally which is accessed through
                # ChatService.get_session_history guarded by our lock on writes
                async for token in self._stream_answer(conversational_rag_chain):
                    yield token
            
            if not self.mailto_link:
                self.suggested_questions = await self.service._generate_suggested_questions(self.message, self.full_answer)

            final_questions = self.suggested_questions if self.suggested_questions is not None else []

            asyncio.create_task(
                self.service._log_conversation(
                    self.session_id,
                    self.message,
                    self.full_answer,
                    final_questions,
                    self.mailto_link
                )
            )

            final_data = {
                "suggested_questions": final_questions,
                "mailto": self.mailto_link
            }
            yield f"event: final\ndata: {json.dumps(final_data)}\n\n"

        except Exception as e:
            print(f"An error occurred during the stream processing: {e}")
            error_data = json.dumps({"error": "An error occurred while processing your request."})
            yield f"event: error\ndata: {error_data}\n\n"

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
