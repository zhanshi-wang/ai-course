import datetime
import uuid
from typing import Annotated, Any, List
from fastapi import APIRouter, Depends
from backend.models import ChatMessage, ChatSession
from backend.database import db_dependency
from backend.routers.auth import get_current_user
from backend.models import User
from backend.schemas import ChatSessionResponse, ChatMessageResponse

router = APIRouter(prefix="/chat", tags=["chat"])


async def save_message(
    session_id: uuid.UUID,
    content: Any,
    db: db_dependency,
):
    message = ChatMessage(session_id=session_id, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


async def list_session_messages(
    session_id: uuid.UUID,
    db: db_dependency,
):
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .all()
    )


@router.post("/sessions", response_model=ChatSessionResponse)
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
    db.refresh(session)

    return session


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_sessions(
    current_user: Annotated[User | None, Depends(get_current_user)],
    db: db_dependency,
):
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )

    return sessions


@router.post(
    "/sessions/{session_id}/messages", response_model=ChatMessageResponse
)
async def create_message(
    session_id: uuid.UUID,
    content: Any,
    db: db_dependency,
):
    message = await save_message(session_id, content, db)
    return message


@router.get(
    "/sessions/{session_id}/messages", response_model=List[ChatMessageResponse]
)
async def list_messages(
    session_id: uuid.UUID,
    db: db_dependency,
):
    messages = await list_session_messages(session_id, db)
    return messages
