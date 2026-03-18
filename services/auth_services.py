from passlib.context import CryptContext
import jwt
import datetime
import os

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(emp_id: str, username: str):
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    return jwt.encode({"sub": username, "emp_id": emp_id, "exp": expire}, SECRET_KEY, algorithm="HS256")