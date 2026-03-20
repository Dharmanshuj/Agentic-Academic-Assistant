from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.chat_routes import router

app = FastAPI(
    title="AI Payroll Chatbot"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)