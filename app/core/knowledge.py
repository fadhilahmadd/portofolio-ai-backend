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
    """
    if not settings.GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY is required to build the retriever.")

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        task_type="retrieval_query",
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

        document_embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            task_type="retrieval_document",
            google_api_key=settings.GOOGLE_API_KEY
        )
        vector_store = FAISS.from_documents(docs, document_embeddings)
        vector_store.save_local(VECTOR_STORE_PATH)
        print("Vector store created successfully.")

    return vector_store.as_retriever()