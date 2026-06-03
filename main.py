from fastapi import FastAPI, APIRouter
from app.items.views import authenticated_router, public_router
from pathlib import Path
from os import getenv
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI()

api_router = APIRouter(prefix='/api')
api_router.include_router(public_router)
api_router.include_router(authenticated_router)

app.include_router(api_router)

# Configure CORS so your frontend can communicate with your backend
app.add_middleware(
    CORSMiddleware,
    # 👈 Change to your specific frontend URL in production
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # 👈 Allows POST, OPTIONS, GET, etc.
    allow_headers=["*"],  # 👈 Allows Content-Type, Authorization, etc.
)


@app.get("/")
def root():
    return "Home"
