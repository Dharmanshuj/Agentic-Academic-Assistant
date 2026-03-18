from langchain.tools import tool

from database.db import get_connection

from security.validator import validate_query
from security.filter import filter_records
from security.masking import apply_masking
from security.audit_logger import log_tool_usage, log_security_event


@tool
def get_employee_info(department: str):
    """Query employees information and return sanitized JSON records."""

    # validate_query(department)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT name, dept, designation, account_no
        FROM employees

        """,
    )

    rows = cursor.fetchall()

    records = []

    for r in rows:

        records.append({
            "name": r[0],
            "department": r[1],
            "designation": r[2],
            "account_no": r[3]
        })

    records = filter_records(records)

    records = [apply_masking(r) for r in records]

    #log_tool_usage("query_employee_department", department)

    return str(records)