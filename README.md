# **Portfolio AI Chatbot Backend**

This repository contains the backend for a personal portfolio AI chatbot. Built with FastAPI and powered by Google's Gemini and Speech-to-Text APIs through the LangChain framework, this chatbot uses a Retrieval-Augmented Generation (RAG) pipeline to answer questions based on a custom knowledge base.

The application is fully asynchronous, supports multilingual voice conversations (English and Indonesian), and features a robust, production-ready architecture with security and rate limiting.

## **✨ Features**

  * **Bilingual Conversational AI**: Engages users in natural conversations about Fadhil Ahmad Hidayat's skills and experience in both **English** and **Indonesian**.
  * **Speech-to-Text (ASR/STT)**: Users can send voice messages (WAV format), which are transcribed into text using Google's Speech-to-Text API.
  * **Text-to-Speech (TTS)**: The AI's text responses can be converted into natural-sounding speech (MP3 format) using Google's Text-to-Speech API.
  * **Enhanced ASR**: Utilizes automatic language detection (`en-US`, `id-ID`) and phrase boosting for key technical terms and names, significantly improving transcription accuracy.
  * **Multilingual RAG**: Employs a powerful multilingual embedding model (`text-embedding-004`) that understands queries in one language and retrieves relevant information from a knowledge base written in another.
  * **Streaming & Multipart Responses**: Delivers text-only responses via a token-by-token stream (SSE) and voice responses via a `multipart/mixed` payload containing both JSON and audio data.
  * **Proactive "Hiring Manager" Mode**: Detects if the user is a recruiter and proactively asks clarifying questions and highlights relevant skills.
  * **Conversation & Audio Logging**: Logs all conversation details, including paths to the saved user and AI audio files, to a SQLite database for analytics and history.
  * **Secure & Production-Ready**:
      * **Rate Limiting**: Protects the main chat endpoint from abuse (15 requests/minute).
      * **Secure Analytics**: The analytics endpoint is protected and requires an API key for access.
  * **Fully Asynchronous**: Built with FastAPI and `aiosqlite` for high performance and fully non-blocking request handling.

## **🛠️ Technology Stack**

  * **Backend**: FastAPI
  * **LLM Framework**: LangChain
  * **Language Models**: Google Gemini (Flash), Google Speech-to-Text, Google Text-to-Speech
  * **Vector Store**: FAISS with Multilingual Embeddings (`text-embedding-004`)
  * **Database**: SQLite with SQLAlchemy and `aiosqlite`
  * **Security**: `slowapi` for rate limiting
  * **Testing**: `pytest`, `pytest-asyncio`

## **🚀 Getting Started**

### **1. Prerequisites**

  * Python 3.8+
  * A Google API Key with the following APIs enabled:
      * Generative Language API (for Gemini)
      * Cloud Speech-to-Text API
      * Cloud Text-to-Speech API
  * (Recommended) A Google Cloud Service Account JSON key for authentication.

### **2. Clone the Repository**

```bash
git clone https://github.com/fadhilahmadd/portofolio-ai-backend.git
cd portofolio-ai-backend
```

### **3. Set Up a Virtual Environment**

```bash
# For Windows
python -m venv venv
venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### **4. Install Dependencies**

```bash
pip install -r requirements.txt
```

### **5. Configure Environment Variables**

Create a `.env` file by copying the example: `cp example.env .env`. Then, open the `.env` file and add your keys:

```
GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"
ANALYTICS_API_KEY="YOUR_SUPER_SECRET_ANALYTICS_KEY"
```

### **6. Running the Application**

Run the application using `uvicorn`. The app will create the database and vector store on the first run.

```bash
uvicorn app.main:app --reload
```

The application will be running at `http://127.0.0.1:8000`.

## **📚 API Endpoints**

Interactive API documentation (Swagger UI) is available at `http://127.0.0.1:8000/docs`.

### **Chat Endpoint**

  * **URL**: `/api/v1/chat/`
  * **Method**: `POST`
  * **Description**: Handles all chat interactions, supporting text and voice.
  * **Content-Type**: `multipart/form-data`
  * **Request Form Fields**:
      * `session_id` (UUID, required): A unique ID for the conversation.
      * `message` (string, optional): The user's text message.
      * `audio_file` (file, optional): The user's voice message as a WAV file.
      * `language` (string, optional, default: `en-US`): The language code (`en-US` or `id-ID`).
      * `include_audio_response` (boolean, optional, default: `false`): Set to `true` to receive a voice response.
  * **Success Responses**:
      * **JSON Response** (`include_audio_response=false`): A standard JSON object with the AI's text response and suggested questions.
        ```json
        {
          "ai_response": "Fadhil has worked on several key projects...",
          "suggested_questions": ["Tell me more about NutriChef.", "What technologies were used in LawBot?"],
          "mailto": null
        }
        ```
      * **Multipart Response** (`include_audio_response=true`): A `multipart/mixed` response containing two parts:
        1.  The JSON data (as above).
        2.  The MP3 audio data for the AI's response.

### **Analytics Endpoint (Private & Secured)**

  * **URL**: `/api/v1/analytics/`
  * **Method**: `GET`
  * **Description**: Retrieves conversation logs. **This endpoint is protected.**
  * **Authentication**: Requires a valid API key passed in the `X-API-Key` request header.
  * **Success Response**: A JSON array of conversation log objects.

## **🧠 Customizing the Knowledge Base**

The chatbot's knowledge is sourced from `app/core/knowledge_sources.py`.

1.  **Add Files**: Place PDF or TXT files inside the `static/docs/` directory.
2.  **Update Configuration**: Add the new file or web link to the `KNOWLEDGE_SOURCES` list in `app/core/knowledge_sources.py`.
3.  **Re-create Vector Store**: **Delete the `static/faiss_index` directory.** The application will automatically rebuild it on the next startup using the new multilingual model.

## **📄 License**

This project is licensed under the MIT License. See the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.

-----

*Last Updated: August 16, 2025*