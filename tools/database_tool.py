from langchain.tools import tool

@tool
def get_employee_info(emp_id: str, department: str = None) -> dict: # Changed return type to dict
    """
    Returns employee information for payroll calculation.
    """
    # Mocking the database record for ID 101
    return {
        "emp_id": emp_id,
        "base": 50000.0,
        "total": 30,
        "present": 20,
        "department": department
    }