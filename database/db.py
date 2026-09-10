import mysql.connector
import os
from dotenv import load_dotenv  
load_dotenv()
def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS"), # Matches the .env file
        database=os.getenv("DB_NAME", "nitj_student_assistant")
    )