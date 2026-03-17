from .database_tool import query_employee_department
from .document_tool import search_documents


def get_tools():

    return [
        query_employee_department,
        search_documents
    ]