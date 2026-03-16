from langchain.tools import tool

@tool
def get_employee_info(department: str) -> str:
    """
    Returns employee information for a department
    """

    # temporary mock response
    return f"Employee data for department: {department}"