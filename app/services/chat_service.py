from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.memory import ChatMessageHistory
from app.core.config import settings
from typing import Dict

class ChatService:
    """
    Asynchronous service to handle chat logic using LangChain's RunnableWithMessageHistory.
    Manages multiple conversation histories based on session IDs.
    """
    def __init__(self):
        # Initialize the language model
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
        )
        
        # In-memory store for session histories.
        # For production, you would replace this with a persistent store like Redis.
        self.store: Dict[str, ChatMessageHistory] = {}
        
        # Define the system prompt text
        system_prompt_text = """
        You are a friendly and helpful chatbot for my personal portfolio website.
        My name is Fadhil Ahmad Hidayat.
        I am an Informatics Engineer with experience in Artificial Intelligence.
        My resume is available at https://resume-fadhil-ahmad.tiiny.site.
        You can find my projects on my GitHub: https://github.com/fadhilahmadd.
        My social media links are:
        - LinkedIn: https://www.linkedin.com/in/fadhil-ahmad-hidayat-604623139/
        - Twitter: https://x.com/fadhil_ahmadd

        When someone asks about me, my projects, or my skills, use this information to answer their questions.
        Be conversational and engaging.
        """

        # Create a ChatPromptTemplate. The `MessagesPlaceholder` is where the history is injected.
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt_text),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ])

        # Create the main runnable chain
        runnable = prompt | self.llm

        # Wrap the runnable with history management
        self.conversational_chain = RunnableWithMessageHistory(
            runnable,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="history",
        )

    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        """
        Retrieves the message history for a given session ID,
        or creates a new one if it doesn't exist.
        """
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]

    async def get_response(self, session_id: str, message: str) -> str:
        """
        Asynchronously gets a response from the language model for a given session.

        Args:
            session_id: The unique identifier for the conversation session.
            message: The user's input message.

        Returns:
            The model's asynchronous response as a string.
        """
        # Invoke the chain with the user's input and the session_id in the config.
        # The config tells the RunnableWithMessageHistory which history to use.
        response = await self.conversational_chain.ainvoke(
            {"input": message},
            config={"configurable": {"session_id": session_id}}
        )
        return response.content

# Singleton instance of the service
chat_service = ChatService()

def get_chat_service():
    """
    Dependency injector for the ChatService.
    """
    return chat_service
