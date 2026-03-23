from langchain.tools import tool

from database.db import get_connection

from security.validator import validate_query
from security.filter import filter_records
from security.masking import apply_masking
from security.audit_logger import log_tool_usage, log_security_event


@tool
def get_employee_by_id(emp_id: str):
    """Query employee by ID and return sanitized JSON record."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM employees
        WHERE empno = %s
        """,
        (emp_id,)
    )

    r = cursor.fetchone()

    if not r:
        log_security_event("Unauthorized access attempt to employee data", details={"emp_id": emp_id})
        return "Employee not found."

    record = {
        "name": r[1],
        "department": r[2],
        "designation": r[3],
        "bank_name": r[4],
        "account_no": r[5],
        "basic_salary": r[6],
        "hra": r[7],
        "conveyance": r[8],
        "medical": r[9],
        "special": r[10],
        "gross_salary": r[11],
        "epf": r[12],
        "health_insurance": r[13],
        "professional_tax": r[14],
        "tds": r[15],
        "total_deductions": r[16],
        "net_pay": r[17]

    }

    #record = validate_query(record)
    record = filter_records([record])[0]

    record = apply_masking(record)

    # log_tool_usage("query_employee_by_id", details={"emp_id": emp_id})

    conn.close()

    return record

@tool
def get_all_employees_data():
    """Query data for all employees. ONLY allowed for ADMIN user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT empno, name, dept, designation, net_pay
        FROM employees
    """)
    rows = cursor.fetchall()
    records = [{"empno": r[0], "name": r[1], "dept": r[2], "designation": r[3], "net_pay": r[4]} for r in rows]
    conn.close()
    return records