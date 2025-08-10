# **Portfolio AI Chatbot Backend**

This repository contains the backend for a personal portfolio AI chatbot. Built with FastAPI and powered by Google's Gemini through the LangChain framework, this chatbot uses a Retrieval-Augmented Generation (RAG) pipeline to answer questions based on a custom knowledge base, including resumes, LinkedIn profiles, and other documents.

The application is fully asynchronous, streaming responses token-by-token for a modern, responsive user experience, and features an intelligent, multi-layered architecture for clean and maintainable code.

## **✨ Features**

  * **Conversational AI**: Engages users in a natural conversation about Fadhil Ahmad Hidayat's skills, projects, and experience.
  * **Streaming Responses (SSE)**: Delivers responses token-by-token using Server-Sent Events, providing a dynamic and interactive user experience.
  * **Rich Markdown Formatting**: Generates well-structured, readable answers using markdown for headings, lists, and bold text, making the information clear and easy for a frontend to render.
  * **Retrieval-Augmented Generation (RAG)**: The chatbot doesn't just rely on its pre-trained knowledge. It retrieves information from a custom knowledge base (PDFs, websites) to provide accurate and context-specific answers.
  * **Conversational Memory**: Remembers the context of the current conversation, allowing for follow-up questions and a more natural chat flow. Each user session is tracked by a unique UUID `session_id`.
  * **Proactive "Hiring Manager" Mode**: Detects if the user is a recruiter and proactively asks clarifying questions, highlights relevant skills, and guides the conversation toward a hiring outcome.
  * **Analytics and Insights**: Logs all conversations to a local SQLite database, allowing for analysis of user interaction patterns. The logging is performed as a non-blocking background task to ensure a fast user response.
  * **Suggested Follow-up Questions**: After providing an answer, the AI suggests relevant follow-up questions to guide the conversation and showcase key qualifications.
  * **Custom Knowledge Base**: Easily extend the chatbot's knowledge by adding or updating documents (PDFs, text files) or web links in the `app/core/knowledge_sources.py` file.
  * **Fully Asynchronous**: Built with FastAPI and `aiosqlite` for high performance and fully non-blocking request handling.
  * **Automated Testing**: Includes a suite of tests using `pytest` to ensure code quality and reliability.

## **🛠️ Technology Stack**

  * **Backend**: FastAPI
  * **LLM Framework**: LangChain
  * **Language Model**: Google Gemini (Flash)
  * **Vector Store**: FAISS (for efficient similarity search)
  * **Database**: SQLite with SQLAlchemy and `aiosqlite`
  * **Testing**: `pytest`, `pytest-asyncio`
  * **Dependencies**: `pydantic`, `langchain-google-genai`, `uvicorn`, `python-dotenv`

## **🚀 Getting Started**

Follow these instructions to set up and run the project locally.

### **1. Prerequisites**

  * Python 3.8+
  * A Google API Key with the "Generative Language API" enabled. You can get one from the [Google AI Studio](https://aistudio.google.com/app/apikey).

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

Create a `.env` file in the root directory by copying the example file.

```bash
cp example.env .env
```

Now, open the `.env` file and add your Google API key:

```
GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"
```

### **6. Running the Application**

Once the setup is complete, you can run the application using `uvicorn`. The application will initialize the database on the first run.

```bash
uvicorn app.main:app --reload
```

The `--reload` flag enables hot-reloading, which automatically restarts the server whenever you make changes to the code. The application will be running at `http://127.0.0.1:8000`.

## **🧪 Running Tests**

This project uses `pytest` for automated testing. To run the tests, first install the testing dependencies:

```bash
pip install pytest pytest-asyncio
```

Then, run the tests from the root directory of the project:

```bash
pytest
```

## **📚 API Endpoints**

You can access the interactive API documentation (provided by Swagger UI) by navigating to `http://12.0.0.1:8000/docs`.

### **Chat Endpoint**

  * **URL**: `/api/v1/chat/`
  * **Method**: `POST`
  * **Description**: Handles chat interactions by streaming a response. The client should generate a UUID v4 for the `session_id` and send it with every request for a given conversation.
  * **Request Body**:
    ```json
    {
      "session_id": "123e4567-e89b-12d3-a456-426614174000",
      "message": "What projects has Fadhil worked on?"
    }
    ```
  * **Success Response (Streaming)**:
    A stream of Server-Sent Events (SSE). The client should listen for three event types:
      * `event: token`: The `data` field contains a JSON object like `{"token": "some text"}`. Append these tokens to form the full response.
      * `event: final`: Sent once at the end of the stream. The `data` field contains a JSON object with metadata, like `{"suggested_questions": ["question 1", "question 2"]}`.
      * `event: error`: Sent if an error occurs during the stream. The `data` field contains a JSON object like `{"error": "An error message"}`.

### **Analytics Endpoint (Private)**

  * **URL**: `/api/v1/analytics/`
  * **Method**: `GET`
  * **Description**: Retrieves conversation logs for analysis.
  * **Success Response**:
    ```json
    [
        {
            "session_id": "123e4567-e89b-12d3-a456-426614174000",
            "user_message": "What projects has Fadhil worked on?",
            "ai_response": "Fadhil has worked on several projects, including NutriChef...",
            "suggested_questions": [
                "Can you tell me more about the NutriChef project?",
                "What was the technology stack for LawBot?"
            ],
            "id": 1,
            "timestamp": "2025-08-10T13:08:00.000Z"
        }
    ]
    ```

## **🧠 Customizing the Knowledge Base**

The chatbot's knowledge is sourced from the files and links specified in `app/core/knowledge_sources.py`.

To add your own data:

1.  **For PDF or Text files**: Place your file inside the `static/docs/` directory.
2.  **Update the configuration**: Open `app/core/knowledge_sources.py` and add a new dictionary to the `KNOWLEDGE_SOURCES` list.
    ```python
    KNOWLEDGE_SOURCES = [
         # ... existing sources
         {"type": "pdf", "path": "my_new_document.pdf"},
         {"type": "web", "path": "https://my-blog-post.com/about-me"},
     ]
    ```
3.  **Re-create the Vector Store**: Delete the `static/faiss_index` directory. The next time you start the application, it will automatically process the new sources and create a new vector store.

## **📄 License**

This project is licensed under the MIT License. See the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.

-----

*Last Updated: August 10, 2025*