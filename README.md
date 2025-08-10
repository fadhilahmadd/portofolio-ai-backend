# **Portfolio AI Chatbot Backend**

This repository contains the backend for a personal portfolio AI chatbot. Built with FastAPI and powered by Google's Gemini Pro through the LangChain framework, this chatbot uses a Retrieval-Augmented Generation (RAG) pipeline to answer questions based on a custom knowledge base, including resumes, LinkedIn profiles, and other documents.

## **✨ Features**

* **Conversational AI**: Engages users in a natural conversation about Fadhil Ahmad Hidayat's skills, projects, and experience.  
* **Retrieval-Augmented Generation (RAG)**: The chatbot doesn't just rely on its pre-trained knowledge. It retrieves information from a custom knowledge base (PDFs, websites) to provide accurate and context-specific answers.  
* **Conversational Memory**: Remembers the context of the current conversation, allowing for follow-up questions and a more natural chat flow. Each user session is tracked by a unique session\_id.  
* **Suggested Follow-up Questions**: After providing an answer, the AI suggests relevant follow-up questions that a user, especially a recruiter, might want to ask. This helps guide the conversation and showcases key qualifications.  
* **Custom Knowledge Base**: Easily extend the chatbot's knowledge by adding or updating documents (PDFs, text files) or web links in the app/core/knowledge\_sources.py file.  
* **Resume Download**: Provides a dedicated API endpoint (/api/v1/resume/download) to serve a downloadable PDF version of the resume.  
* **Asynchronous API**: Built with FastAPI for high performance and asynchronous request handling.

## **🛠️ Technology Stack**

* **Backend**: FastAPI  
* **LLM Framework**: LangChain  
* **Language Model**: Google Gemini Pro  
* **Vector Store**: FAISS (for efficient similarity search)  
* **Dependencies**: ```pydantic, langchain-google-genai, uvicorn, python-dotenv```

## **🚀 Getting Started**

Follow these instructions to set up and run the project locally.

### **1\. Prerequisites**

* Python 3.8+  
* A Google API Key with the "Generative Language API" enabled. You can get one from the [Google AI Studio](https://aistudio.google.com/app/apikey).

### **2\. Clone the Repository**
```bash
git clone https://github.com/fadhilahmadd/portofolio-ai-backend.git
cd portofolio-ai-backend
```
### **3\. Set Up a Virtual Environment**

It's highly recommended to use a virtual environment to manage project dependencies.
```bash
# For Windows  
python -m venv venv  
venv\\Scripts\\activate
```
```bash
# For macOS/Linux  
python3 -m venv venv  
source venv/bin/activate
```
### **4\. Install Dependencies**

Install all the required Python packages using the requirements.txt file.
```bash
pip install -r requirements.txt
```
### **5\. Configure Environment Variables**

Create a .env file in the root directory of the project by copying the example file.
```bash
cp example.env .env
```
Now, open the .env file and add your Google API key:

GOOGLE\_API\_KEY="YOUR\_GOOGLE\_API\_KEY\_HERE"

### **6\. Running the Application**

Once the setup is complete, you can run the application using uvicorn.
```bash
uvicorn app.main:app --reload
```
The --reload flag enables hot-reloading, which automatically restarts the server whenever you make changes to the code.

The application will be running at http://127.0.0.1:8000.

## **📚 API Endpoints**

You can access the interactive API documentation (provided by Swagger UI) by navigating to http://127.0.0.1:8000/api/v1/docs.

### **Chat Endpoint**

* **URL**: /api/v1/chat/  
* **Method**: POST  
* **Description**: Handles chat interactions.  
* **Request Body**:
  ```bash  
  {  
    "session_id": "some-unique-session-id",  
    "message": "What projects has Fadhil worked on?"  
  }
  ```
* **Success Response**:  
  ```bash
  {  
    "response": "Fadhil has worked on several projects, including NutriChef, an Android app for recipe recommendations, and LawBot, a legal chatbot for Indonesian law. Would you like to know more about a specific project?",  
    "suggested_questions": [  
      "Can you tell me more about the NutriChef project?",  
      "What was the technology stack for LawBot?",  
      "Where can I find his projects?"  
    ]  
  }
  ```

### **Resume Download Endpoint**

* **URL**: /api/v1/resume/download  
* **Method**: GET  
* **Description**: Downloads Fadhil Ahmad Hidayat's resume as a PDF file.

## **🧠 Customizing the Knowledge Base**

The chatbot's knowledge is sourced from the files and links specified in app/core/knowledge\_sources.py.

To add your own data:

1. **For PDF or Text files**: Place your file inside the static/docs/ directory.  
2. **Update** the **configuration**: Open app/core/knowledge\_sources.py and add a new dictionary to the KNOWLEDGE\_SOURCES list.  
  ```bash
  KNOWLEDGE_SOURCES = [  
       # ... existing sources  
       {"type": "pdf", "path": "my\_new\_document.pdf"},  
       {"type": "web", "path": "\[https://my-blog-post.com/about-me\](https://my-blog-post.com/about-me)"},  
   ]
  ```

3. **Re-create the Vector Store**: Delete the static/faiss_index directory. The next time you start the application, it will automatically process the new sources and create a new vector store.

## **📄 License**

This project is licensed under the MIT License. See the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.