from fastapi import FastAPI
from app.items.views import router


app = FastAPI()

app.include_router(router)


@app.get("/")
def root():
    return "Home"
