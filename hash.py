from services.auth_services import hash_password
from database.db import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT empno, hashed_password FROM employees")
rows = cursor.fetchall()

for empno, plain_pw in rows:
    if not plain_pw.startswith("$argon2"):
        hashed = hash_password(plain_pw)

        cursor.execute(
            "UPDATE employees SET hash_password = %s WHERE empno = %s",
            (hashed, empno)
        )

conn.commit()
conn.close()