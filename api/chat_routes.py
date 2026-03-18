from database.db import get_connection
from dotenv import load_dotenv
load_dotenv()
import uuid
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from agents.agents import run_salary_agent
from services.security_service import get_current_user
from services.auth_services import hash_password, verify_password, create_access_token

router = APIRouter()

# --- Schemas ---
class QueryRequest(BaseModel):
    query: str  
    employee_id: str

class UserCredentials(BaseModel):
    username: str
    password: str

class RegisterRequest(UserCredentials):
    emp_id: str

# --- Mock DB ---
users_db = get_connection()

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

@router.post("/register")
async def register(request: RegisterRequest):
    if request.username in users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    
    users_db[request.username] = {
        "hashed_password": hash_password(request.password),
        "emp_id": request.emp_id
    }
    return {"message": "User registered successfully"}

@router.post("/login")
# Change the argument to use OAuth2PasswordRequestForm
async def login(credentials: OAuth2PasswordRequestForm = Depends()):
    # Swagger sends 'username' and 'password' inside the 'credentials' object
    user = users_db.get(credentials.username)
    
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate token using the stored emp_id
    token = create_access_token(user["emp_id"], credentials.username)
    
    return {"access_token": token, "token_type": "bearer"}

@router.post("/ask-me/stream")
async def ask_payroll_stream(
    request: QueryRequest, 
    user: dict = Depends(get_current_user)
):
    if request.employee_id != user.get("emp_id"):
        raise HTTPException(status_code=403, detail="Unauthorized access to this employee ID")

    session_id = str(uuid.uuid4())
    
    async def stream_generator():
        async for chunk in run_salary_agent(request.query, request.employee_id, session_id):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")