from database.db import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT name, dept FROM employees")

for row in cursor.fetchall():
    print(row)

conn.close()