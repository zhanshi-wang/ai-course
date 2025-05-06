import asyncio
import os
import uuid
from agents import Agent, ModelSettings, Runner, function_tool
from backend.routers.chat import list_session_messages, save_message
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
from backend.models import ChatMessage, User
from backend.chroma import search_vector_db
from openai import AsyncOpenAI
from openai.types.shared import Reasoning
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

    async def send_message(self, message: ChatMessage, websocket: WebSocket):
        # Convert ChatMessage to a serializable dictionary
        message_dict = {
            "id": str(message.id),
            "session_id": str(message.session_id),
            "content": message.content,
            "created_at": (
                message.created_at.isoformat() if message.created_at else None
            ),
        }
        await websocket.send_json(message_dict)


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


@function_tool
async def get_context_from_files(query: str, user_id: str) -> str:
    """
    From user's queries, retrieve relevant context from user's files.

    Args:
        query (str): The input query to search for
        user_id (str): The user's ID

    Returns:
        str: The context
    """
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


@router.websocket("/chat/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: uuid.UUID,
    db: db_dependency,
    current_user: Annotated[User | None, Depends(ws_get_current_user)],
):
    await manager.connect(websocket)
    try:
        while True:
            agent = Agent(
                name="Assistant",
                instructions=f"""You are a helpful assistant that can answer
                questions and help with tasks for user with id
                `{current_user.id}`. Use get_context_from_files tool to
                get additional information.""",
                tools=[get_context_from_files],
                model="o3",
                model_settings=ModelSettings(
                    reasoning=Reasoning(
                        effort="medium",
                        summary="detailed",
                    ),
                ),
            )

            messages = await list_session_messages(session_id, db)
            input_items = [message.content for message in messages]

            while True:
                user_message_text = await websocket.receive_text()
                user_message = {
                    "type": "message",
                    "role": "user",
                    "content": user_message_text,
                }

                input_items.append(user_message)
                await save_message(session_id, user_message, db)

                result = Runner.run_streamed(agent, input=input_items)
                async for event in result.stream_events():
                    if event.type == "run_item_stream_event":
                        input_items.append(event.item.to_input_item())
                        chat_message = await save_message(
                            session_id, event.item.to_input_item(), db
                        )
                        await manager.send_message(chat_message, websocket)

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
