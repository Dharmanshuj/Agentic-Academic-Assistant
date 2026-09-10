from services.auth_services import hash_password
from database.db import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("SHOW COLUMNS FROM students LIKE 'hashed_password'")
has_hashed_password = cursor.fetchone() is not None

if not has_hashed_password:
    raise RuntimeError(
        "Column 'hashed_password' not found in 'students'. "
        "Run: ALTER TABLE students ADD COLUMN hashed_password VARCHAR(255) NULL;"
    )

cursor.execute("SELECT roll_no, hashed_password FROM students")
rows = cursor.fetchall()

for roll_number, plain_pw in rows:
    if not plain_pw:
        continue

    if not plain_pw.startswith("$argon2"):
        hashed = hash_password(plain_pw)

        cursor.execute(
            "UPDATE students SET hashed_password = %s WHERE roll_no = %s",
            (hashed, roll_number)
        )

conn.commit()
conn.close()