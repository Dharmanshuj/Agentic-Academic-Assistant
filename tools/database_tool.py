from langchain.tools import tool

from database.db import get_connection

from security.validator import validate_query
from security.filter import filter_records
from security.masking import apply_masking
from security.audit_logger import log_tool_usage, log_security_event


@tool
def get_employee_info(department: str):
    """Query employees by department and return sanitized JSON records."""

    validate_query(department)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT name, department, role, email
        FROM employees
        WHERE department = ?
        """,
        (department,)
    )

    rows = cursor.fetchall()

    records = []

    for r in rows:

        records.append({
            "name": r[0],
            "department": r[1],
            "role": r[2],
            "email": r[3]
        })

    records = filter_records(records)

    records = [apply_masking(r) for r in records]

    log_tool_usage("query_employee_department", department)

    return str(records)