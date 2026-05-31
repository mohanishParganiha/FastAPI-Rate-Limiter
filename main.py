from fastapi import FastAPI, APIRouter
from app.items.views import authenticated_router, public_router
from dotenv import load_dotenv
from pathlib import Path
from os import getenv

if not getenv("DATABASE_URL"):
    load_dotenv()

app = FastAPI()

api_router = APIRouter(prefix='/api')
api_router.include_router(public_router)
api_router.include_router(authenticated_router)

app.include_router(api_router)


@app.get("/")
def root():
    return "Home"
