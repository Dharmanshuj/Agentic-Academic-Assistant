from .database_tool import get_student_by_id
from .document_tool import search_documents


def get_tools():

    return [
        get_student_by_id,
        search_documents
    ]