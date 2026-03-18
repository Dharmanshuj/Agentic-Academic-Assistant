from .database_tool import get_employee_info
from .document_tool import search_documents


def get_tools():

    return [
        get_employee_info,
        search_documents
    ]