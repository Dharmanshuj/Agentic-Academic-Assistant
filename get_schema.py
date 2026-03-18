from database.db import get_connection

conn = get_connection()
cursor = conn.cursor()
cursor.execute("SHOW TABLES")
print("Tables:", cursor.fetchall())

cursor.execute("DESCRIBE employees")
print("employees schema:", cursor.fetchall())

try:
    cursor.execute("DESCRIBE users")
    print("users schema:", cursor.fetchall())
except Exception as e:
    print("users table error:", e)

conn.close()
