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
from app.core.knowledge import retriever


_SYSTEM_PROMPT_TEMPLATE = (
    "You are a friendly and helpful chatbot assistant for Fadhil Ahmad Hidayat's personal portfolio website."
    "Your goal is to be conversational and engaging. Here is some key information about Fadhil:"
    "\n\n"
    "--- General Information ---\n"
    "My name is Fadhil Ahmad Hidayat.\n"
    "I am an Informatics Engineering Graduate with experience in Artificial Intelligence, Mobile, and Website Development.\n"
    "My projects are on my GitHub: https://github.com/fadhilahmadd.\n"
    "My social media links are:\n"
    "- LinkedIn: https://www.linkedin.com/in/fadhil-ahmad-hidayat-604623139/\n"
    "- Twitter: https://x.com/fadhil_ahmadd\n"
    "\n"
    "--- Your Task ---\n"
    "1.  **Answer questions about my skills, experience, and projects using the context provided below.** Do not mention that you are using a resume or context, just answer the questions naturally.\n"
    "2.  **If the user asks for my resume, CV, or a download link, you MUST provide them with this exact link:** `https://resume-fadhil-ahmad.tiiny.site`.\n"
    "3.  For general chat or questions about my social media, use the information above.\n"
    "4.  If you don't know the answer from the context, say that you don't have that specific information.\n"
    "\n"
    "--- Retrieved Context from Knowledge Base ---\n"
    "{context}"
)

_CONTEXTUALIZE_Q_SYSTEM_PROMPT = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)

_SUGGESTED_QUESTIONS_PROMPT_TEMPLATE = (
    "Based on the following question and answer, generate three relevant follow-up questions a recruiter or user might ask. "
    "Return the questions as a JSON list of strings. For example: [\"Can you tell me more about Project X?\", \"What was your role in that team?\", \"What technologies did you use?\"]\n\n"
    "Question: {question}\n"
    "Answer: {answer}"
)


class ChatService:
    """
    Asynchronous service to handle chat logic using a RAG pipeline.
    It generates a response and suggests follow-up questions.
    """
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3
        )
        self.store: Dict[str, ChatMessageHistory] = {}
        self.retriever = retriever

        # --- Build the RAG Chain ---
        
        qa_prompt = ChatPromptTemplate.from_messages(
            [("system", _SYSTEM_PROMPT_TEMPLATE), MessagesPlaceholder("chat_history"), ("human", "{input}")]
        )
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", _CONTEXTUALIZE_Q_SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, contextualize_q_prompt
        )
        
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        self.conversational_chain = RunnableWithMessageHistory(
            rag_chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        """Retrieves or creates a chat history for a given session ID."""
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]

    async def _generate_suggested_questions(self, question: str, answer: str) -> Optional[List[str]]:
        """
        Asynchronously generates relevant follow-up questions using a separate LLM call.
        """
        prompt = ChatPromptTemplate.from_template(_SUGGESTED_QUESTIONS_PROMPT_TEMPLATE)
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
        except Exception as e:
            print(f"An unexpected error occurred while generating suggested questions: {e}")
        
        return None

    async def get_response(self, session_id: str, message: str) -> Dict[str, Any]:
        """
        Asynchronously gets the main RAG response and then generates suggested questions.
        """
        main_response = await self.conversational_chain.ainvoke(
            {"input": message},
            config={"configurable": {"session_id": session_id}},
        )
        answer = main_response.get("answer", "I'm sorry, I couldn't process your request.")

        suggested_questions = await self._generate_suggested_questions(question=message, answer=answer)

        return {
            "answer": answer,
            "suggested_questions": suggested_questions,
        }

chat_service = ChatService()

def get_chat_service() -> ChatService:
    return chat_service
