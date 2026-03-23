from langchain.tools import tool
from typing import Optional

from database.db import get_connection

from security.validator import validate_query
from security.filter import filter_records
from security.masking import apply_masking
from security.audit_logger import log_tool_usage, log_security_event

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


@tool
def admin_get_monthly_metrics(month: Optional[int] = None, year: Optional[int] = None):
    """Admin tool to get attendance and salary payments for all employees across a given month."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # If no month/year is specified, fetch the most recent global month deployed
    if not month or not year:
        cursor.execute("SELECT MAX(month), MAX(year) FROM attendance")
        res = cursor.fetchone()
        if res and res[0] and res[1]:
            month, year = res[0], res[1]
        else:
            month, year = 3, 2026 # ultimate fallback
            
    query = """
        SELECT e.empno, e.name, a.total_days, a.present_days, a.absent_days, s.inhand_net_pay
        FROM employees e
        LEFT JOIN attendance a ON e.empno = a.empno AND a.month = %s AND a.year = %s
        LEFT JOIN salary_payments s ON a.id = s.attendance_id
    """
    cursor.execute(query, (month, year))
    rows = cursor.fetchall()
    
    records = []
    for r in rows:
        records.append({
            "empno": r[0],
            "name": r[1],
            "total_days": r[2],
            "present_days": r[3],
            "absent_days": r[4],
            "inhand_net_pay": r[5],
            "month": month,
            "year": year
        })
    conn.close()
    return records

@tool
def get_employee_by_id(emp_id: str):
    """Query employee by ID and return sanitized JSON record.
    emp_id is taken as input which is str and is employee id"""

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
def get_attendance(emp_id: str, month: Optional[int] = None, year: Optional[int] = None):
    """
    Get attendance for employee for a specific month or year.
    """
    conn = get_connection()
    cursor = conn.cursor()

    if month and year:
        cursor.execute(
            """
            SELECT id, total_days, present_days, absent_days, month, year
            FROM attendance
            WHERE empno = %s AND month = %s AND year = %s
            """,
            (emp_id, month, year)
        )
    else:
        cursor.execute(
            """
            SELECT id, total_days, present_days, absent_days, month, year
            FROM attendance
            WHERE empno = %s
            ORDER BY year DESC, month DESC
            LIMIT 1
            """,
            (emp_id,)
        )

    r = cursor.fetchone()
    conn.close()

    if not r:
        return None

    return {
        "attendance_id": r[0],
        "total_days": r[1],
        "present_days": r[2],
        "absent_days": r[3],
        "month_recorded": r[4],
        "year_recorded": r[5]
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

@tool
def get_all_attendance_for_employee(emp_id: str):
    """
    Get all attendance records for an employee across all months and years.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, total_days, present_days, absent_days, month, year
        FROM attendance
        WHERE empno = %s
        ORDER BY year DESC, month DESC
        """,
        (emp_id,)
    )

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return []

    records = []
    for r in rows:
        records.append({
            "attendance_id": r[0],
            "total_days": r[1],
            "present_days": r[2],
            "absent_days": r[3],
            "month": r[4],
            "year": r[5]
        })

    return records
