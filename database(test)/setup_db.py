import sqlite3

conn = sqlite3.connect("company.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name TEXT,
    department TEXT,
    role TEXT,
    email TEXT,
    salary INTEGER
)
""")

cursor.execute("""
INSERT INTO employees (name, department, role, email, salary)
VALUES
('John Doe', 'HR', 'Manager', 'john@company.com', 100000),
('Lisa Smith', 'HR', 'Recruiter', 'lisa@company.com', 90000),
('Mike Brown', 'Engineering', 'Developer', 'mike@company.com', 120000)
""")

conn.commit()
conn.close()