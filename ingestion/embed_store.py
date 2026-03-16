from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
import os

load_dotenv()

def create_vector_store(chunks):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key="AIzaSyCXI59XKDTY_ZmajdHfjG53KdTTNqgcE1I"
    )

    store = FAISS.from_documents(
        chunks,
        embeddings
    )

    store.save_local("vector_store")
    return store