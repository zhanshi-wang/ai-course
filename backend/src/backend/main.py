import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import auth, chat
from backend.routers import users
from backend.routers import files
from backend.routers import ws


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/")
async def health_check():
    logger.info("Health check endpoint called")
    return "ok"


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(files.router)
app.include_router(ws.router)
app.include_router(chat.router)
