from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
import os

def create_vector_store(chunks):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embeddings-001",
        google_api_key=os.getenv("GEMINI_API_KEY")
    )

    store = FAISS.from_documents(
        chunks,
        embeddings
    )

    store.save_local("vector_store")
    return store