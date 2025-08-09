import os
import glob
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from app.core.config import settings

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static')
VECTOR_STORE_PATH = os.path.join(STATIC_DIR, "faiss_index")

def get_retriever():
    """
    Creates and returns a retriever for the personal knowledge base from all PDFs in the static folder.
    If the vector store already exists, it loads it. Otherwise, it creates it from all found PDFs.
    """
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001", 
        google_api_key=settings.GOOGLE_API_KEY
    )

    if os.path.exists(VECTOR_STORE_PATH):
        vector_store = FAISS.load_local(VECTOR_STORE_PATH, embeddings, allow_dangerous_deserialization=True)
    else:
        pdf_files = glob.glob(os.path.join(STATIC_DIR, "*.pdf"))

        if not pdf_files:
            raise FileNotFoundError(f"No PDF files found in the directory: {STATIC_DIR}")

        all_documents = []
        for pdf_path in pdf_files:
            try:
                loader = PyPDFLoader(file_path=pdf_path)
                all_documents.extend(loader.load())
            except Exception as e:
                print(f"Warning: Could not load or process {pdf_path}. Error: {e}")

        if not all_documents:
             raise ValueError("Could not load any content from the PDF files found.")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        docs = text_splitter.split_documents(all_documents)
        
        vector_store = FAISS.from_documents(docs, embeddings)
        vector_store.save_local(VECTOR_STORE_PATH)

    return vector_store.as_retriever()

retriever = get_retriever()
