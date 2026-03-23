from langchain.tools import tool

from rag.retriever import get_retriever
from security.audit_logger import log_tool_usage


retriever = get_retriever()


@tool
def search_documents(query: str):
    """
    Search relevant documents based on the user query.
    """

    docs = retriever.invoke(query)

    results = []

    for doc in docs:
        results.append(doc.page_content)

    log_tool_usage("search_documents", query)

    return "\n".join(results)