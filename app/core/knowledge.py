import os
import glob
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from app.core.config import settings
from app.core.knowledge_sources import KNOWLEDGE_SOURCES

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static')
DOCS_DIR = os.path.join(STATIC_DIR, "docs")
VECTOR_STORE_PATH = os.path.join(STATIC_DIR, "faiss_index")

os.makedirs(DOCS_DIR, exist_ok=True)

def get_retriever():
    """
    Creates a knowledge base from multiple sources and returns a retriever.
    If a vector store exists, it's loaded. Otherwise, it's created from the sources.
    """
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001", 
        google_api_key=settings.GOOGLE_API_KEY
    )

    if os.path.exists(VECTOR_STORE_PATH):
        vector_store = FAISS.load_local(VECTOR_STORE_PATH, embeddings, allow_dangerous_deserialization=True)
    else:
        print("Creating new vector store from knowledge sources...")
        all_documents = []

        for source in KNOWLEDGE_SOURCES:
            source_type = source["type"].lower()
            source_path = source["path"]
            
            try:
                print(f"-> Loading from {source_type}: {source_path}")
                if source_type == 'pdf':
                    loader = PyPDFLoader(file_path=os.path.join(DOCS_DIR, source_path))
                    all_documents.extend(loader.load())
                elif source_type == 'web':
                    loader = WebBaseLoader(web_path=source_path)
                    all_documents.extend(loader.load())
                elif source_type == 'text':
                    loader = TextLoader(file_path=os.path.join(DOCS_DIR, source_path))
                    all_documents.extend(loader.load())
            except Exception as e:
                print(f"Warning: Could not load source {source_path}. Error: {e}")

        if not all_documents:
             raise ValueError("Could not load any content from the configured knowledge sources.")
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = text_splitter.split_documents(all_documents)
        
        vector_store = FAISS.from_documents(docs, embeddings)
        vector_store.save_local(VECTOR_STORE_PATH)
        print("Vector store created successfully.")

    return vector_store.as_retriever()

retriever = get_retriever()
