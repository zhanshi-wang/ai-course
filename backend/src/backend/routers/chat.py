import asyncio
import os
import uuid
import jwt
from typing import Annotated, Any
from fastapi import (
    APIRouter,
    WebSocket,
    status,
    Depends,
    WebSocketDisconnect,
)

from backend.database import db_dependency
from backend.routers.auth import get_user, TokenData
from backend.routers.auth import SECRET_KEY, ALGORITHM
from backend.models import User
from backend.chroma import search_vector_db
from openai import AsyncOpenAI
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(
        self, websocket: WebSocket, code: int = status.WS_1000_NORMAL_CLOSURE
    ):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            try:
                await websocket.close(code=code)
            except RuntimeError:
                # WebSocket already closed
                pass

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_json(self, data: Any, websocket: WebSocket):
        await websocket.send_json(data)

    async def send_full_message(self, message: str, websocket: WebSocket):
        message_id = str(uuid.uuid4())
        await websocket.send_json(
            {
                "message_id": message_id,
                "type": "start",
            }
        )
        await websocket.send_json(
            {
                "message_id": message_id,
                "type": "chunk",
                "content": message,
            }
        )
        await websocket.send_json(
            {
                "message_id": message_id,
                "type": "end",
            }
        )


manager = ConnectionManager()


async def ws_get_current_user(
    websocket: WebSocket,
    db: db_dependency,
):
    auth_token = websocket.cookies.get("auth_token")
    print(auth_token)
    if not auth_token:
        await manager.disconnect(websocket, status.WS_1008_POLICY_VIOLATION)
        return None

    try:
        payload = jwt.decode(auth_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        print(username)
        if username is None:
            await manager.disconnect(websocket, status.WS_1008_POLICY_VIOLATION)
            return None
        token_data = TokenData(username=username)
    except jwt.InvalidTokenError:
        await manager.disconnect(websocket, status.WS_1008_POLICY_VIOLATION)
        return None

    user = get_user(db, token_data.username)
    if user is None:
        await manager.disconnect(websocket, status.WS_1008_POLICY_VIOLATION)
        return None

    return user


async def get_context_from_files(query: str, user_id: uuid.UUID) -> str:
    """Retrieve relevant context from user's files based on query"""
    try:
        # Search vector DB for relevant context
        search_results = await search_vector_db(query=query, top_k=5, user_id=user_id)
        logger.info(f"Search results: {search_results}")
        # Format the results as context
        if not search_results:
            return ""

        context_parts = []
        for i, result in enumerate(search_results):
            metadata = result["metadata"]
            file_name = metadata.get("file_name", "Unknown")
            context_parts.append(
                f"Document: {file_name}\n" f"Content: {result['content']}\n"
            )

        context = "\n---\n".join(context_parts)
        return context
    except Exception as e:
        logger.error(f"Error retrieving context: {str(e)}")
        return ""


@router.websocket("/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    current_user: Annotated[User | None, Depends(ws_get_current_user)],
):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()

            # Get relevant context from files
            await manager.send_full_message("Getting context from files...", websocket)
            context = await get_context_from_files(data, current_user.id)
            await manager.send_full_message(f"Context retrieved: {context}", websocket)

            # Prepare messages with context if available
            sys_msg = "You are a helpful assistant with access to files."
            messages = [
                {"role": "system", "content": sys_msg},
            ]

            if context:
                context_intro = "Here is relevant information from documents:"
                system_context = f"{context_intro}\n{context}"
                messages.append({"role": "system", "content": system_context})

            messages.append({"role": "user", "content": data})

            stream = await openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=messages,
                stream=True,
            )

            message_id = str(uuid.uuid4())

            await manager.send_json(
                {
                    "message_id": message_id,
                    "type": "start",
                },
                websocket,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    logger.info(chunk.choices[0].delta.content)
                    content = chunk.choices[0].delta.content
                    await manager.send_json(
                        {
                            "message_id": message_id,
                            "type": "chunk",
                            "content": content,
                        },
                        websocket,
                    )
                    await asyncio.sleep(0.01)

            await manager.send_json(
                {
                    "message_id": message_id,
                    "type": "end",
                },
                websocket,
            )

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
