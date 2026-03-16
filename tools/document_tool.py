from langchain.tools import tool
from rag.retriever import get_retriever

retriever = get_retriever()

@tool
def search_documents(query: str) -> str:
    """Search documents using RAG retriever"""

    docs = retriever.invoke(query)

    return "\n\n".join([doc.page_content for doc in docs])