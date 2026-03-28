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

def create_access_token(empno: str, username: str):
    expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=expire_minutes)
    role = "ADMIN" if empno == "ADMIN" else "EMPLOYEE"
    payload = {
        "sub": username,
        "name": username,
        "emp_id": empno,
        "empno": empno,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
