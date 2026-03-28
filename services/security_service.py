import os
from dotenv import load_dotenv # New Import
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt

# Load variables from .env file
load_dotenv() 

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Fetch from environment variable with a fallback (optional)
SECRET_KEY = os.getenv("SECRET_KEY") 

if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set in your .env file!")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        empno = payload.get("empno") or payload.get("emp_id")
        if not empno:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is missing employee number")

        role = payload.get("role") or ("ADMIN" if empno == "ADMIN" else "EMPLOYEE")
        name = payload.get("name") or payload.get("sub") or empno

        return {
            "empno": empno,
            "emp_id": empno,
            "name": name,
            "role": role,
            "token_claims": payload,
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

