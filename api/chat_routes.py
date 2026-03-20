from database.db import get_connection
from dotenv import load_dotenv
load_dotenv()
import uuid
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from database.db import get_connection

from agents.agents import run_salary_agent
from services.security_service import get_current_user
from services.auth_services import hash_password, verify_password, create_access_token

router = APIRouter()

# --- Schemas ---
class QueryRequest(BaseModel):
    query: str  

class UserCredentials(BaseModel):
    empno: str
    password: str

class RegisterRequest(UserCredentials):
    empno: str
    password: str

# --- Mock DB ---

# Check if employee exists
    # users_db.execute(
    #     "SELECT empno, hashed_password FROM employees WHERE empno = ?",
    #     (request.emp_id,)
    # )
    # employee = users_db.fetchone()
# --- Endpoints ---
@router.get("/debug-routes")
def get_routes():
    return [route.path for route in router.routes]


# @app.get("/chat")
# def chat(query: str):
#     result = chatbot_agent.invoke({
#         "messages": [("user", query)]
#     })

#     return {
#         "response": result["messages"][-1].content
#     }

# @router.post("/register")
# async def register(request: RegisterRequest):
#     conn = get_connection()
#     users_db = conn.cursor()

#     # Check if employee exists
#     users_db.execute(
#         "SELECT empno, hashed_password FROM employees WHERE empno = ?",
#         (request.emp_id,)
#     )
#     employee = users_db.fetchone()

#     if not employee:
#         raise HTTPException(status_code=404, detail="Employee not found")

#     # if request.username in users_db:
#     #     raise HTTPException(status_code=400, detail="User already exists")
#     # Store hashed password
#     hashed_pw = hash_password(request.password)

#     users_db.execute(
#         "UPDATE employees SET hashed_password = ? WHERE empno = ?",
#         (hashed_pw, request.emp_id)
#     )
#     # users_db[request.username] = {
#     #     "hashed_password": hash_password(request.password),
#     #     "emp_id": request.emp_id
#     # }

#     conn.commit()
#     conn.close()
#     return {"message": "User registered successfully"}

@router.post("/login")
# Change the argument to use OAuth2PasswordRequestForm
async def login(credentials: OAuth2PasswordRequestForm = Depends()):
    conn = get_connection()
    users_db = conn.cursor()

    users_db.execute(
        "SELECT empno, hashed_password FROM employees WHERE empno = %s",
        (credentials.username,)
    )

    user = users_db.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid employee ID")

    empno, hashed_password_db = user

    if not hashed_password_db:
        raise HTTPException(status_code=400, detail="User not registered")

    if not verify_password(credentials.password, hashed_password_db):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(empno, empno)

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

    session_id = str(uuid.uuid4())
    
    async def stream_generator():
        async for chunk in run_salary_agent(request.query, user.get("emp_id"), session_id):
            payload = json.dumps({"text": chunk})
            yield f"data: {payload}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")