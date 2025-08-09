import google.generativeai as genai
from app.core.config import settings

class ChatService:
    """
    Service to handle the chat logic and interaction with the Gemini API.
    """
    def __init__(self):
        try:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.chat_session = self._initialize_chat_session()
        except Exception as e:
            # In a real app, you'd want more robust logging here
            print(f"Error initializing Gemini model: {e}")
            self.chat_session = None

    def _initialize_chat_session(self):
        """
        Starts a new chat session with an initial prompt.
        """
        initial_prompt = """
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
        return self.model.start_chat(history=[
            {"role": "user", "parts": [initial_prompt]},
            {"role": "model", "parts": ["Great! I'm ready to help. What would you like to know?"]}
        ])

    def get_response(self, message: str) -> str:
        """
        Sends a message to the chat session and gets the response.

        Args:
            message: The user's message.

        Returns:
            The model's response text.
        
        Raises:
            ValueError: If the chat session is not initialized.
            Exception: For errors during message sending.
        """
        if not self.chat_session:
            raise ValueError("Chat model is not initialized.")
        
        try:
            response = self.chat_session.send_message(message)
            return response.text
        except Exception as e:
            # Handle potential API errors
            print(f"An error occurred with the AI service: {str(e)}")
            raise

chat_service = ChatService()

def get_chat_service():
    """
    Dependency injector for the ChatService.
    """
    return chat_service
