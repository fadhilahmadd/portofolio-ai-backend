import json
import asyncio
from typing import Dict, List, Optional, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from app.core.config import settings
from app.core.knowledge import get_retriever
from app.api.v1.schemas.chat import UserIntent
from app.core.prompts import (
    SYSTEM_PROMPT_TEMPLATE,
    CONTEXTUALIZE_Q_SYSTEM_PROMPT,
    SUGGESTED_QUESTIONS_PROMPT_TEMPLATE,
    HIRING_MANAGER_SYSTEM_PROMPT_TEMPLATE,
    INTENT_CLASSIFICATION_PROMPT_TEMPLATE
)

class ChatService:
    """
    Asynchronous service to handle chat logic using a RAG pipeline.
    It generates a response, suggests follow-up questions, and can
    operate in a proactive "Hiring Manager" mode.
    """
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3
        )
        self.store: Dict[str, ChatMessageHistory] = {}
        self.retriever = get_retriever()

    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        """Retrieves or creates a chat history for a given session ID."""
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]

    async def _get_user_intent(self, message: str) -> UserIntent:
        """
        Asynchronously classifies the user's intent using an LLM call.
        """
        prompt = ChatPromptTemplate.from_template(INTENT_CLASSIFICATION_PROMPT_TEMPLATE)
        chain = prompt | self.llm
        
        try:
            response = await chain.ainvoke({"question": message})
            intent = response.content.strip().lower()
            if "recruiter" in intent:
                return UserIntent.RECRUITER
            return UserIntent.GENERAL_INQUIRY
        except Exception as e:
            print(f"Error classifying user intent: {e}")
            return UserIntent.GENERAL_INQUIRY

    async def _generate_suggested_questions(self, question: str, answer: str) -> Optional[List[str]]:
        """
        Asynchronously generates relevant follow-up questions.
        """
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
        except (json.JSONDecodeError, TypeError, AttributeError) as e:
            print(f"Error parsing suggested questions JSON: {e}")
            return None

    async def get_response(self, session_id: str, message: str) -> Dict[str, Any]:
        """
        Asynchronously gets the main RAG response and then generates suggested questions.
        """
        user_intent = await self._get_user_intent(message)

        if user_intent == UserIntent.RECRUITER:
            system_prompt = HIRING_MANAGER_SYSTEM_PROMPT_TEMPLATE
        else:
            system_prompt = SYSTEM_PROMPT_TEMPLATE

        qa_prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt), MessagesPlaceholder("chat_history"), ("human", "{input}")]
        )
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        
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
        
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        conversational_chain = RunnableWithMessageHistory(
            rag_chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

        main_response_task = conversational_chain.ainvoke(
            {"input": message},
            config={"configurable": {"session_id": session_id}},
        )
        
        main_response = await main_response_task
        answer = main_response.get("answer", "I'm sorry, I couldn't process your request.")

        suggested_questions_task = self._generate_suggested_questions(question=message, answer=answer)
        
        suggested_questions = await suggested_questions_task

        return {
            "answer": answer,
            "suggested_questions": suggested_questions,
        }

chat_service = ChatService()

def get_chat_service() -> ChatService:
    return chat_service

def create_mailto_link(email: str, subject: str, body: str) -> str:
    """
    Creates a mailto link.
    """
    import urllib.parse
    return f"mailto:{email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"