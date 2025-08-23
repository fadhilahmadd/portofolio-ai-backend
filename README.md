⚠️ Under Development, please be patient, i hava problem on WebRTC STURN and TURN :)

# **Portofolio AI Chatbot Backend**

This repository contains the backend for a personal portofolio AI chatbot, featuring both a standard text-based interface and an advanced, real-time voice agent. Built with FastAPI and powered by Google's Gemini and Speech-to-Text APIs through the LangChain framework, this application showcases a sophisticated, event-driven architecture.

The project is fully asynchronous, supports multilingual voice conversations, and features a robust, production-ready architecture using **PostgreSQL** for scalability, along with security and rate limiting.

## **✨ Features**

  * **Dual Chat Modes**:
    * **Text Chat**: A classic, Server-Sent Events (SSE) based endpoint for efficient, streaming text conversations.
    * **Real-Time Voice Agent**: An advanced, low-latency voice interface using WebRTC for natural, real-time conversations.
* **Advanced Voice Capabilities**:
    * **Stateful Conversation**: The agent tracks its state (`LISTENING`, `THINKING`, `SPEAKING`) and communicates it to the client.
    * **Interrupt Handling**: Users can interrupt the agent while it's speaking for a more fluid conversation.
    * **Tool & Function Calling**: The voice agent can use tools to perform actions, such as fetching the current time or searching the knowledge base.
* **Retrieval-Augmented Generation (RAG)**: Both chat modes use a RAG pipeline to answer questions based on a custom knowledge base (resumes, web pages, etc.).
* **Speech-to-Text & Text-to-Speech**: Integrates Google's APIs for accurate transcription and natural-sounding speech.
* **Secure & Production-Ready**:
    * **Rate Limiting**: Protects endpoints from abuse.
    * **Secure Analytics**: The analytics endpoint is protected by an API key.
    * **Scalable Backend**: Runs on a production-ready stack with Gunicorn and PostgreSQL, managed by Docker Compose.
* **Clean Architecture**:
    * **Separation of Concerns**: The simple RAG chat logic (`ChatService`) is completely separate from the advanced agent logic (`AgentService`).
    * **Fully Asynchronous**: Built with FastAPI and `asyncpg` for high performance.

## **🛠️ Technology Stack**

  * **Backend**: FastAPI
  * **Real-Time Communication**: WebSockets, WebRTC (`aiortc`)
  * **LLM Framework**: LangChain (Agents and RAG chains)
  * **Language Models**: Google Gemini (Pro & Flash), Google Speech-to-Text, Google Text-to-Speech
  * **Vector Store**: FAISS with Multilingual Embeddings
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
POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD_HERE
POSTGRES_DB=app
```

### **4. Running Locally for Development**

For local development, you can run the database in Docker and the Python application directly on your machine.

**Step 1: Start the Database Container**

```bash
docker compose up -d db
```

**Step 2: Modify `.env` for Local Connection**
Temporarily change `POSTGRES_SERVER` in your `.env` file to `localhost`:

```
POSTGRES_SERVER=localhost
```

**Step 3: Set Up a Virtual Environment & Install Dependencies**

```bash
# For Windows
python -m venv venv
venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Use a service account key file**

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/ee-email1-sa.json
```

**Step 4: Run the FastAPI Server**

```bash
uvicorn app.main:app --reload
```

The application will be running at `http://127.0.0.1:8000`. Remember to change `POSTGRES_SERVER` back to `db` before deploying.

### **5. Production Deployment with Docker Compose**

To build and run the entire application stack (API and Database) in a production-like environment, use Docker Compose.

```bash
docker compose up -d --build
```

## **📚 API Endpoints**

Interactive API documentation (Swagger UI) is available at `http://127.0.0.1:8000/docs`.

### **Chat Endpoint**

  * **URL**: `/api/v1/chat/`
  * **Method**: `POST`
  * **Description**: Handles all chat interactions, supporting text and voice.
  * **Content-Type**: `multipart/form-data`

### **Analytics Endpoint (Private & Secured)**

  * **URL**: `/api/v1/analytics/`
  * **Method**: `GET`
  * **Description**: Retrieves conversation logs. **This endpoint is protected.**
  * **Authentication**: Requires a valid API key passed in the `X-API-Key` request header.

## **🧠 Customizing the Knowledge Base**

The chatbot's knowledge is sourced dynamically from local files and a configured list of web pages.

1.  **Add Local Documents**: To add local knowledge, simply place your PDF (`.pdf`) or text (`.txt`) files inside the `static/docs/` directory. The application will automatically find and load them.
2.  **Add Web Pages**: To add web-based knowledge, open `app/core/knowledge_sources.py` and add the URL to the `KNOWLEDGE_SOURCES` list.
3.  **Rebuild the Vector Store**: After adding, updating, or removing any knowledge sources (local files or web links), you **must delete the `static/faiss_index` directory.** The application will automatically rebuild the knowledge base from all sources on the next startup.

## **📄 License**

This project is licensed under the MIT License. See the [LICENSE](https://opensource.org/licenses/MIT) for details.

-----

*Last Updated: August 17, 2025*
