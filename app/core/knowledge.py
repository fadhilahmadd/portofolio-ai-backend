import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from app.core.config import settings

# Path to the static directory and the resume file
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static')
RESUME_PATH = os.path.join(STATIC_DIR, 'Fadhil_Ahmad_Hidayat_Resume.pdf')
VECTOR_STORE_PATH = os.path.join(STATIC_DIR, "faiss_index")

def get_retriever():
    """
    Creates and returns a retriever for the personal knowledge base.
    If the vector store already exists, it loads it. Otherwise, it creates it.
    """
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001", 
        google_api_key=settings.GOOGLE_API_KEY
    )

    if os.path.exists(VECTOR_STORE_PATH):
        vector_store = FAISS.load_local(VECTOR_STORE_PATH, embeddings, allow_dangerous_deserialization=True)
    else:
        if not os.path.exists(RESUME_PATH):
            raise FileNotFoundError(f"Resume PDF not found at {RESUME_PATH}")
            
        loader = PyPDFLoader(file_path=RESUME_PATH)
        documents = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        docs = text_splitter.split_documents(documents)
        
        vector_store = FAISS.from_documents(docs, embeddings)
        vector_store.save_local(VECTOR_STORE_PATH)

    return vector_store.as_retriever()

retriever = get_retriever()
