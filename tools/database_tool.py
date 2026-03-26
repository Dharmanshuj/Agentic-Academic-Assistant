from langchain.tools import tool
from typing import Optional

from database.db import get_connection

from security.validator import validate_query
from security.filter import filter_records
from security.masking import apply_masking
from security.audit_logger import log_tool_usage, log_security_event

@tool
def get_all_employees_data() -> list:
    """
    Fetch a directory of ALL employees in the company.
    Use this when: the admin asks about 'all employees', 'everyone's salary', 'how many employees',
    'list all staff', or any question requiring a company-wide overview.
    Returns: A list of dicts with keys: empno, name, dept, designation, net_pay.
    """
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
def admin_get_monthly_metrics(month: Optional[int] = None, year: Optional[int] = None) -> list:
    """
    Get attendance and in-hand salary data for ALL employees for a specific month/year.
    Use this when: the admin asks about 'attendance in March', 'who was absent in January 2026',
    'net pay for all employees this month', or any period-specific cross-employee question.
    - month: integer 1-12 (e.g. 3 for March). Pass None if not specified.
    - year: integer (e.g. 2026). Pass None if not specified.
    Returns: A list of dicts with: empno, name, total_days, present_days, absent_days, inhand_net_pay, month, year.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if month and year:
        query = """
            SELECT e.empno, e.name, a.total_days, a.present_days, a.absent_days, s.inhand_net_pay, a.month, a.year
            FROM employees e
            LEFT JOIN attendance a ON e.empno = a.empno AND a.month = %s AND a.year = %s
            LEFT JOIN salary_payments s ON a.id = s.attendance_id
        """
        cursor.execute(query, (month, year))
    elif year:
        query = """
            SELECT e.empno, e.name, a.total_days, a.present_days, a.absent_days, s.inhand_net_pay, a.month, a.year
            FROM employees e
            LEFT JOIN attendance a ON e.empno = a.empno AND a.year = %s
            LEFT JOIN salary_payments s ON a.id = s.attendance_id
        """
        cursor.execute(query, (year,))
    else:
        query = """
            SELECT e.empno, e.name, a.total_days, a.present_days, a.absent_days, s.inhand_net_pay, a.month, a.year
            FROM employees e
            LEFT JOIN attendance a ON e.empno = a.empno AND a.year = 2026
            LEFT JOIN salary_payments s ON a.id = s.attendance_id
        """
        cursor.execute(query)
            
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
            "month": r[6],
            "year": r[7]
        })
    conn.close()
    return records


@tool
def get_employee_by_id(emp_id: str) -> dict:
    """
    Fetch the complete salary structure for a single employee by their employee ID.
    Use this when: a user asks about their own salary, allowances, deductions, EPF, TDS, HRA,
    gross salary, net pay, or bank details. Also use this as the FIRST step before calculating
    prorated salary, since it provides basic_salary needed for the formula.
    - emp_id: the employee's unique ID string (e.g. 'EMP001').
    Returns: A dict with keys: name, department, designation, bank_name, account_no, basic_salary,
             hra, conveyance, medical, special, gross_salary, epf, health_insurance,
             professional_tax, tds, total_deductions, net_pay.
    """
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
        return {"error": "Employee not found."}

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

    record = filter_records([record])[0]
    record = apply_masking(record)
    conn.close()
    return record


@tool
def get_attendance(emp_id: str, month: Optional[int] = None, year: Optional[int] = None) -> dict:
    """
    Fetch attendance data for a specific employee for a given month and year.
    Use this when: a user asks about their present days, absent days, or how many days they worked
    in a specific month. Also call this BEFORE get_salary_payment, since you need the attendance_id.
    If month/year not specified, returns the employee's most recent attendance record.
    - emp_id: the employee's unique ID string.
    - month: integer 1-12. Pass None if the user didn't specify a month.
    - year: integer (e.g. 2026). Pass None if the user didn't specify a year.
    Returns: A dict with: attendance_id, total_days, present_days, absent_days, month_recorded, year_recorded.
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
        return {"error": "No attendance record found."}

    return {
        "attendance_id": r[0],
        "total_days": r[1],
        "present_days": r[2],
        "absent_days": r[3],
        "month_recorded": r[4],
        "year_recorded": r[5]
    }


@tool
def get_salary_payment(attendance_id: int) -> dict:
    """
    Fetch the finalized in-hand net salary that was actually PAID for a specific attendance period.
    Use this when: the user asks 'how much did I receive' or 'what was my actual salary paid' for a month.
    You MUST call get_attendance first to obtain the attendance_id before calling this tool.
    - attendance_id: the integer ID from get_attendance's result.
    Returns: A dict with key: final_salary (the actual amount credited to the employee).
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
        return {"error": "No salary payment record found for this attendance period."}

    return {"final_salary": r[0]}


@tool
def get_all_attendance_for_employee(emp_id: str, year: Optional[int] = None) -> list:
    """
    Fetch ALL monthly attendance records for a single employee across the whole year.
    Use this when: the user asks for an attendance summary, yearly overview, 'how many times was I absent
    this year', or when you need to loop through multiple months to calculate cumulative metrics.
    - emp_id: the employee's unique ID string.
    - year: integer. If None, returns ALL available records for the employee.
    Returns: A list of dicts with: attendance_id, total_days, present_days, absent_days, month, year.
    """
    conn = get_connection()
    cursor = conn.cursor()

    if year:
        cursor.execute(
            """
            SELECT id, total_days, present_days, absent_days, month, year
            FROM attendance
            WHERE empno = %s AND year = %s
            ORDER BY year DESC, month DESC
            """,
            (emp_id, year)
        )
    else:
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

    return [
        {
            "attendance_id": r[0],
            "total_days": r[1],
            "present_days": r[2],
            "absent_days": r[3],
            "month": r[4],
            "year": r[5]
        }
        for r in rows
    ]
