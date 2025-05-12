from datetime import datetime
import uuid
from pydantic import BaseModel


class ChatSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Enables ORM mode for SQLAlchemy models


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    created_at: datetime
    content: dict

    class Config:
        from_attributes = True  # Enables ORM mode for SQLAlchemy models
