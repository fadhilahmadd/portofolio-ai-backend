# **Portfolio AI Chatbot Backend**

This repository contains the backend for a personal portfolio AI chatbot. Built with FastAPI and powered by Google's Gemini and Speech-to-Text APIs through the LangChain framework, this chatbot uses a Retrieval-Augmented Generation (RAG) pipeline to answer questions based on a custom knowledge base.

The application is fully asynchronous, supports multilingual voice conversations (English and Indonesian), and features a robust, production-ready architecture using **PostgreSQL** for scalability, along with security and rate limiting.

## **✨ Features**

  * **Bilingual Conversational AI**: Engages users in natural conversations about Fadhil Ahmad Hidayat's skills and experience in both **English** and **Indonesian**.
  * **Speech-to-Text (ASR/STT)**: Users can send voice messages (WAV format), which are transcribed into text using Google's Speech-to-Text API.
  * **Text-to-Speech (TTS)**: The AI's text responses can be converted into natural-sounding speech (MP3 format) using Google's Text-to-Speech API.
  * **Enhanced ASR**: Utilizes automatic language detection (`en-US`, `id-ID`) and phrase boosting for key technical terms and names, significantly improving transcription accuracy.
  * **Multilingual RAG**: Employs a powerful multilingual embedding model (`text-embedding-004`) that understands queries in one language and retrieves relevant information from a knowledge base written in another.
  * **Streaming & Multipart Responses**: Delivers text-only responses via a token-by-token stream (SSE) and voice responses via a `multipart/mixed` payload containing both JSON and audio data.
  * **Proactive "Hiring Manager" Mode**: Detects if the user is a recruiter and proactively asks clarifying questions and highlights relevant skills.
  * **Conversation & Audio Logging**: Logs all conversation details to a **PostgreSQL** database for analytics and history.
  * **Secure & Production-Ready**:
      * **Rate Limiting**: Protects the main chat endpoint from abuse (15 requests/minute).
      * **Secure Analytics**: The analytics endpoint is protected and requires an API key for access.
      * **Scalable Backend**: Runs on a production-ready stack with Gunicorn and PostgreSQL, managed by Docker Compose.
  * **Fully Asynchronous**: Built with FastAPI, `asyncpg`, and `aiosqlite` for high performance and fully non-blocking I/O.

## **🛠️ Technology Stack**

  * **Backend**: FastAPI
  * **LLM Framework**: LangChain
  * **Language Models**: Google Gemini (Pro & Flash), Google Speech-to-Text, Google Text-to-Speech
  * **Vector Store**: FAISS with Multilingual Embeddings (`text-embedding-004`)
  * **Database**: **PostgreSQL** with SQLAlchemy and `asyncpg`
  * **Security**: `slowapi` for rate limiting
  * **Testing**: `pytest`, `pytest-asyncio`

## **🚀 Getting Started**

### **1. Prerequisites**

  * Python 3.8+
  * **Docker and Docker Compose**
  * A Google API Key with the following APIs enabled:
      * Generative Language API (for Gemini)
      * Cloud Speech-to-Text API
      * Cloud Text-to-Speech API

### **2. Clone the Repository**

```bash
git clone https://github.com/fadhilahmadd/portofolio-ai-backend.git
cd portofolio-ai-backend
```

### **3. Configure Environment Variables**

Create a `.env` file by copying the example: `cp example.env .env`. Then, open the `.env` file and add your keys and a secure password:

```
GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"
ANALYTICS_API_KEY="YOUR_SUPER_SECRET_ANALYTICS_KEY"

# PostgreSQL Settings
POSTGRES_SERVER=db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=YOUR_NEW_SECURE_PASSWORD_HERE
POSTGRES_DB=app
```

### **4. Running Locally for Development**

For local development, you can run the database in Docker and the Python application directly on your machine.

**Step 1: Start the Database Container**

```bash
docker-compose up -d db
```

**Step 2: Modify `.env` for Local Connection**
Temporarily change `POSTGRES_SERVER` in your `.env` file to `localhost`:

```
POSTGRES_SERVER=localhost
```

**Step 3: Set Up a Virtual Environment & Install Dependencies**

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Step 4: Run the FastAPI Server**

```bash
uvicorn app.main:app --reload
```

The application will be running at `http://127.0.0.1:8000`. Remember to change `POSTGRES_SERVER` back to `db` before deploying.

### **5. Production Deployment with Docker Compose**

To build and run the entire application stack (API and Database) in a production-like environment, use Docker Compose.

```bash
docker-compose up -d --build
```

## **📚 API Endpoints**

Interactive API documentation (Swagger UI) is available at `http://127.0.0.1:8000/docs`.

### **Chat Endpoint**

  * **URL**: `/api/v1/chat/`
  * **Method**: `POST`
  * **Description**: Handles all chat interactions, supporting text and voice.
  * **Content-Type**: `multipart/form-data`

### **Clear History Endpoint (New)**

  * **URL**: `/api/v1/chat/clear_history/{session_id}`
  * **Method**: `POST`
  * **Description**: Clears the conversation history for a given `session_id`.

### **Analytics Endpoint (Private & Secured)**

  * **URL**: `/api/v1/analytics/`
  * **Method**: `GET`
  * **Description**: Retrieves conversation logs. **This endpoint is protected.**
  * **Authentication**: Requires a valid API key passed in the `X-API-Key` request header.

## **🧠 Customizing the Knowledge Base**

The chatbot's knowledge is sourced from `app/core/knowledge_sources.py`.

1.  **Add Files**: Place PDF or TXT files inside the `static/docs/` directory.
2.  **Update Configuration**: Add the new file or web link to the `KNOWLEDGE_SOURCES` list in `app/core/knowledge_sources.py`.
3.  **Re-create Vector Store**: **Delete the `static/faiss_index` directory.** The application will automatically rebuild it on the next startup.

## **📄 License**

This project is licensed under the MIT License. See the LICENSE file for details.

-----

*Last Updated: August 17, 2025*