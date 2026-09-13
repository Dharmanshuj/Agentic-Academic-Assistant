from database.db import get_connection
from dotenv import load_dotenv
load_dotenv()
import hmac
import os
import uuid
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from database.db import get_connection

from agents.agents import run_student_agent
from services.security_service import get_current_user
from services.auth_services import hash_password, verify_password, create_access_token

router = APIRouter()

# --- Schemas ---
class QueryRequest(BaseModel):
    query: str  

class UserCredentials(BaseModel):
    empno: str
    password: str

# --- Endpoints ---
@router.get("/debug-routes")
def get_routes():
    return [route.path for route in router.routes]

@router.post("/login")
# Change the argument to use OAuth2PasswordRequestForm
async def login(credentials: OAuth2PasswordRequestForm = Depends()):
    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if (
        admin_username
        and admin_password
        and hmac.compare_digest(credentials.username, admin_username)
        and hmac.compare_digest(credentials.password, admin_password)
    ):
        token = create_access_token("ADMIN", "Administrator")
        return {"access_token": token, "token_type": "bearer"}

    conn = get_connection()
    users_db = conn.cursor()
    try:
        users_db.execute(
            """
            SELECT
                roll_no,
                TRIM(CONCAT(first_name, ' ', COALESCE(last_name, ''))),
                hashed_password
            FROM students
            WHERE roll_no = %s
            """,
            (credentials.username,)
        )
    except Exception as exc:
        conn.close()
        raise HTTPException(
            status_code=500,
            detail=f"Login schema mismatch: ensure table 'students' has column 'hashed_password'. ({exc})",
        )

    user = users_db.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid student ID")

    roll_number, name, hashed_password_db = user

    if not hashed_password_db:
        raise HTTPException(status_code=400, detail="User not registered")

    if not verify_password(credentials.password, hashed_password_db):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(roll_number, name)

    return {"access_token": token, "token_type": "bearer"}

    # # Swagger sends 'username' and 'password' inside the 'credentials' object
    # user = users_db.get(credentials.username)
    
    # if not user or not verify_password(credentials.password, user["hashed_password"]):
    #     raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # # Generate token using the stored emp_id
    # token = create_access_token(user["emp_id"], credentials.username)
    
    # return {"access_token": token, "token_type": "bearer"}

@router.post("/ask-me/stream")
async def ask_payroll_stream(
    request: QueryRequest, 
    user: dict = Depends(get_current_user)
):
    import json
    
    # if request.employee_id != user.get("empno"):
    #     raise HTTPException(status_code=403, detail="Unauthorized access to this employee ID")

    empno = user.get("empno")
    if not empno:
        raise HTTPException(status_code=401, detail="Unable to determine roll number from token")

    session_id = empno
    
    async def stream_generator():
        async for chunk in run_student_agent(request.query, empno, session_id):
            payload = json.dumps({"text": chunk})
            yield f"data: {payload}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")
