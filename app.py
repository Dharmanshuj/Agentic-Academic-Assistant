from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.chat_routes import router as chat_router

app = FastAPI()

# 1. Define allowed origins (your React dev server)
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5174",
    "http://localhost:3000"
]

# 2. Add the Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # This allows OPTIONS, POST, GET, etc.
    allow_headers=["*"],  # This allows Authorization, Content-Type, etc.
)

# 3. Include Routers AFTER middleware
app.include_router(chat_router)