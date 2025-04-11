from backend.routers import auth
from backend.routers import users
from backend.routers import files
from fastapi import FastAPI


app = FastAPI()


@app.get("/")
async def health_check():
    return "ok"


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(files.router)
