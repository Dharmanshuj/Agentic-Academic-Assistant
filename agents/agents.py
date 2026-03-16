from langgraph.prebuilt import create_react_agent
from config import get_llm

from tools.document_tool import search_documents
from tools.database_tool import get_employee_info

llm = get_llm()

tools = [
    search_documents,
    get_employee_info
]

chatbot_agent = create_react_agent(
    model=llm,
    tools=tools
)