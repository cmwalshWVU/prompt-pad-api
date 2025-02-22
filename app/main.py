from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health, hello, openai_api

app = FastAPI(title="FastAPI with Supabase and OpenAI")

# Configure CORS (adjust allow_origins as needed for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend URL(s) in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the routers
app.include_router(health.router)
app.include_router(hello.router)
app.include_router(openai_api.router)

# For local development, run with: uvicorn app.main:app --reload
