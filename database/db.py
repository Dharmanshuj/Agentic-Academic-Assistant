import mysql.connector
import os

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="mynameis",
        database="company"
    )