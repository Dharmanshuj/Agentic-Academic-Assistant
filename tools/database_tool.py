from langchain.tools import tool
from typing import Optional
 
from database.db import get_connection
 
from security.validator import validate_query
from security.filter import filter_records
from security.masking import apply_masking
from security.audit_logger import log_tool_usage, log_security_event
 
@tool
def get_all_students_data():
    """Query data for all students. ONLY allowed for ADMIN user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            s.roll_no,
            TRIM(CONCAT(s.first_name, ' ', COALESCE(s.last_name, ''))) AS name,
            s.department,
            s.semester,
            ap.cgpa
        FROM students s
        LEFT JOIN academic_performance ap
            ON ap.student_id = s.student_id
            AND ap.semester = s.semester
    """)
    rows = cursor.fetchall()
    records = [{"roll_no": r[0], "name": r[1], "department": r[2], "semester": r[3], "cgpa": r[4]} for r in rows]
    conn.close()
    return records
 
 
@tool
def admin_get_semester_metrics(semester: Optional[int] = None, year: Optional[int] = None):
    """Admin tool to get attendance and academic metrics for all students in a given semester."""
    conn = get_connection()
    cursor = conn.cursor()
    if semester:
        query = """
            SELECT
                s.roll_no,
                TRIM(CONCAT(s.first_name, ' ', COALESCE(s.last_name, ''))) AS name,
                s.department,
                s.semester,
                ap.sgpa,
                ap.cgpa,
                ROUND(
                    CASE WHEN SUM(a.total_classes) > 0
                        THEN (SUM(a.attended_classes) * 100.0 / SUM(a.total_classes))
                        ELSE 0
                    END,
                    2
                ) AS attendance_percentage
            FROM students s
            LEFT JOIN attendance a ON s.student_id = a.student_id
            LEFT JOIN academic_performance ap ON s.student_id = ap.student_id AND ap.semester = s.semester
            WHERE s.semester = %s
            GROUP BY s.student_id, s.roll_no, s.first_name, s.last_name, s.department, s.semester, ap.sgpa, ap.cgpa
        """
        cursor.execute(query, (semester,))
    else:
        query = """
            SELECT
                s.roll_no,
                TRIM(CONCAT(s.first_name, ' ', COALESCE(s.last_name, ''))) AS name,
                s.department,
                s.semester,
                ap.sgpa,
                ap.cgpa,
                ROUND(
                    CASE WHEN SUM(a.total_classes) > 0
                        THEN (SUM(a.attended_classes) * 100.0 / SUM(a.total_classes))
                        ELSE 0
                    END,
                    2
                ) AS attendance_percentage
            FROM students s
            LEFT JOIN attendance a ON s.student_id = a.student_id
            LEFT JOIN academic_performance ap ON s.student_id = ap.student_id AND ap.semester = s.semester
            GROUP BY s.student_id, s.roll_no, s.first_name, s.last_name, s.department, s.semester, ap.sgpa, ap.cgpa
        """
        cursor.execute(query)
    rows = cursor.fetchall()
    records = []
    for r in rows:
        records.append({
            "roll_no": r[0],
            "name": r[1],
            "department": r[2],
            "semester": r[3],
            "sgpa": r[4],
            "cgpa": r[5],
            "attendance_percentage": r[6]
        })
    conn.close()
    return records
 
@tool
def get_student_by_id(student_id: str):
    """Query student by ID and return sanitized JSON record.
    student_id is taken as input which is str and is student roll number"""
 
    conn = get_connection()
    cursor = conn.cursor()
 
    cursor.execute(
        """
        SELECT
            student_id,
            roll_no,
            TRIM(CONCAT(first_name, ' ', COALESCE(last_name, ''))) AS name,
            department,
            program,
            semester,
            section,
            batch_year,
            admission_year,
            hostel_name,
            room_no,
            email,
            phone,
            guardian_name,
            guardian_phone,
            address
        FROM students
        WHERE roll_no = %s OR student_id = %s
        LIMIT 1
        """,
        (student_id, student_id)
    )
 
    r = cursor.fetchone()
 
    if not r:
        log_security_event("Unauthorized access attempt to student data", details={"student_id": student_id})
        return "Student not found."
 
    record = {
        "student_id": r[0],
        "roll_no": r[1],
        "name": r[2],
        "department": r[3],
        "program": r[4],
        "semester": r[5],
        "section": r[6],
        "batch_year": r[7],
        "admission_year": r[8],
        "hostel_name": r[9],
        "room_no": r[10],
        "email": r[11],
        "phone": r[12],
        "guardian_name": r[13],
        "guardian_phone": r[14],
        "address": r[15],
    }
 
    record = filter_records([record])[0]
    record = apply_masking(record)
 
    conn.close()
 
    return record
 
@tool
def get_attendance(student_id: str, month: Optional[int] = None, year: Optional[int] = None):
    """
    Get attendance for student for a specific month or year.
    """
    conn = get_connection()
    cursor = conn.cursor()
 
    cursor.execute(
        """
        SELECT
            MIN(a.attendance_id) AS attendance_id,
            COALESCE(SUM(a.total_classes), 0) AS total_classes,
            COALESCE(SUM(a.attended_classes), 0) AS attended_classes,
            ROUND(
                CASE WHEN SUM(a.total_classes) > 0
                    THEN (SUM(a.attended_classes) * 100.0 / SUM(a.total_classes))
                    ELSE 0
                END,
                2
            ) AS attendance_percentage
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        WHERE s.roll_no = %s OR s.student_id = %s
        """,
        (student_id, student_id)
    )
 
    r = cursor.fetchone()
    conn.close()
 
    if not r:
        return None
 
    return {
        "attendance_id": r[0],
        "total_classes": r[1],
        "attended_classes": r[2],
        "attendance_percentage": r[3],
        # Compatibility aliases for existing prompts/UI
        "total_days": r[1],
        "present_days": r[2],
        "absent_days": max((r[1] or 0) - (r[2] or 0), 0),
    }

@tool
def get_semester_results(attendance_id: int):
    """
    Fetch semester results/SGPA based on attendance ID.
    """
    conn = get_connection()
    cursor = conn.cursor()
 
    cursor.execute(
        """
        SELECT
            ap.semester,
            ap.sgpa,
            ap.cgpa,
            ap.backlogs,
            ap.academic_year
        FROM attendance a
        JOIN academic_performance ap ON ap.student_id = a.student_id
        WHERE a.attendance_id = %s
        ORDER BY ap.semester DESC
        LIMIT 1
        """,
        (attendance_id,)
    )
 
    r = cursor.fetchone()
    conn.close()
 
    if not r:
        return None
 
    return {
        "semester": r[0],
        "sgpa": r[1],
        "cgpa": r[2],
        "backlogs": r[3],
        "academic_year": r[4]
    }
 
@tool
def get_all_attendance_for_student(student_id: str, year: Optional[int] = None):
    """
    Get all attendance records for a student across all months for a specific year.
    """
    conn = get_connection()
    cursor = conn.cursor()
 
    cursor.execute(
        """
        SELECT
            a.attendance_id,
            a.subject_id,
            sub.subject_name,
            a.total_classes,
            a.attended_classes,
            a.attendance_percentage
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        LEFT JOIN subjects sub ON a.subject_id = sub.subject_id
        WHERE s.roll_no = %s OR s.student_id = %s
        ORDER BY a.attendance_id DESC
        """,
        (student_id, student_id)
    )
 
    rows = cursor.fetchall()
    conn.close()
 
    if not rows:
        return []
 
    records = []
    for r in rows:
        records.append({
            "attendance_id": r[0],
            "subject_id": r[1],
            "subject_name": r[2],
            "total_classes": r[3],
            "attended_classes": r[4],
            "attendance_percentage": r[5],
            # Compatibility aliases
            "total_days": r[3],
            "present_days": r[4],
            "absent_days": max((r[3] or 0) - (r[4] or 0), 0),
        })
 
    return records