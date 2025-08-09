from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from app.core.config import settings
from app.core.knowledge import retriever
from typing import Dict

class ChatService:
    """
    Asynchronous service to handle chat logic using a RAG pipeline with a defined persona.
    """
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3
        )
        self.store: Dict[str, ChatMessageHistory] = {}
        self.retriever = retriever

        system_prompt = (
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
        
        qa_prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt), MessagesPlaceholder("chat_history"), ("human", "{input}")]
        )
        
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
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
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]

    async def get_response(self, session_id: str, message: str) -> str:
        response = await self.conversational_chain.ainvoke(
            {"input": message},
            config={"configurable": {"session_id": session_id}},
        )
        return response.get("answer", "I'm sorry, I encountered an issue and couldn't process your request.")

chat_service = ChatService()

def get_chat_service():
    return chat_service
