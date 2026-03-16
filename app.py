from ingestion.loader import load_documents
from ingestion.chunker import chunk_documents
from ingestion.embed_store import create_vector_store

docs = load_documents("documents/policies.pdf")

chunks = chunk_documents(docs)

create_vector_store(chunks)

print("Vector database created successfully")