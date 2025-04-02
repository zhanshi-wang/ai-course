from backend.database import init_db
from backend.routers import auth
from backend.routers import users
from fastapi import FastAPI


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/")
async def health_check():
    return "ok"


app.include_router(auth.router)
app.include_router(users.router)
