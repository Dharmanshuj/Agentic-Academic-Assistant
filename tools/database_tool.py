from langchain.tools import tool

from database.db import get_connection

from security.validator import validate_query
from security.filter import filter_records
from security.masking import apply_masking
from security.audit_logger import log_tool_usage, log_security_event


# @tool
# def get_employee_info():
#     """Query employees and return sanitized JSON records."""

#     # validate_query(department)

#     conn = get_connection()
#     cursor = conn.cursor()

#     cursor.execute(
#         """
#         SELECT name, dept, designation, bank_name, account_no
#         FROM employees
#         """,
#         ()
#     )

#     rows = cursor.fetchall()

#     records = []

#     for r in rows:

#         records.append({
#             "name": r[0],
#             "department": r[1],
#             "designation": r[2],
#             "bank_name": r[3],
#             "account_no": r[4]
#         })

#     records = filter_records(records)

#     records = [apply_masking(r) for r in records]

#     # log_tool_usage("query_employee")

#     conn.close()

#     return str(records)

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
def get_attendance(emp_id: str, month: int, year: int):
    """
    Get attendance for employee for a specific month.
    Use this when user asks about presence, absence, or working days.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, total_days, present_days, absent_days
        FROM attendance
        WHERE empno = %s AND month = %s AND year = %s
        """,
        (emp_id, month, year)
    )

    r = cursor.fetchone()

    conn.close()

    if not r:
        return None

    return {
        "attendance_id": r[0],
        "total_days": r[1],
        "present_days": r[2],
        "absent_days": r[3]
    }
    
@tool
def get_salary_payment(attendance_id: int):
    """
    Fetch final in-hand salary based on attendance ID.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT inhand_net_pay
        FROM salary_payments
        WHERE attendance_id = %s
        """,
        (attendance_id,)
    )

    r = cursor.fetchone()
    conn.close()

    if not r:
        return None

    return {
        "final_salary": r[0]
    }
