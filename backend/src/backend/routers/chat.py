import datetime
import uuid
from typing import Annotated, Any
from fastapi import APIRouter, Depends
from backend.models import ChatMessage, ChatSession
from backend.database import db_dependency
from backend.routers.auth import get_current_user
from backend.models import User

router = APIRouter(prefix="/chat", tags=["chat"])


async def save_message(
    session_id: uuid.UUID,
    content: Any,
    db: db_dependency,
):
    message = ChatMessage(session_id=session_id, content=content)
    db.add(message)
    db.commit()
    return message


async def list_session_messages(
    session_id: uuid.UUID,
    db: db_dependency,
):
    return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()


@router.post("/sessions")
async def create_session(
    current_user: Annotated[User | None, Depends(get_current_user)],
    db: db_dependency,
):
    session = ChatSession(
        user_id=current_user.id,
        name=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    db.add(session)
    db.commit()
    return session


@router.get("/sessions")
async def list_sessions(
    current_user: Annotated[User | None, Depends(get_current_user)],
    db: db_dependency,
):
    return db.query(ChatSession).filter(ChatSession.user_id == current_user.id).all()


@router.post("/sessions/{session_id}/messages")
async def create_message(
    session_id: uuid.UUID,
    content: Any,
    db: db_dependency,
):
    messages = await save_message(session_id, content, db)
    return messages


@router.get("/sessions/{session_id}/messages")
async def list_messages(
    session_id: uuid.UUID,
    db: db_dependency,
):
    return await list_session_messages(session_id, db)
