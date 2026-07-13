from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .chat_service import ChatService
from .config import Settings
from .llm import get_llm_client
from .llm.client import ChatMessage
from .llm.tools import ToolExecutor
from .services import Block1Client

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inizializza e rilascia le risorse del servizio."""
    settings = Settings()
    logging.basicConfig(
        level=getattr(logging, settings.app_log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    block1_client = Block1Client(
        base_url=settings.block1_base_url,
        api_key=settings.block1_api_key,
    )
    llm_client = get_llm_client(settings)
    tool_executor = ToolExecutor(dependencies={"block1_client": block1_client})
    chat_service = ChatService(
        llm_client=llm_client,
        tool_executor=tool_executor,
    )

    app.state.settings = settings
    app.state.block1_client = block1_client
    app.state.llm_client = llm_client
    app.state.chat_service = chat_service

    yield

    await llm_client.close()
    await block1_client.close()


app = FastAPI(
    title="Orchestratore LLM - Produzione Alimentare",
    description="Ponte tra chat utente e microservizio analitico (Blocco 1).",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """Endpoint WebSocket per la conversazione in tempo reale."""
    await websocket.accept()
    chat_service: ChatService = websocket.app.state.chat_service
    history: list[ChatMessage] = []

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {
                        "type": "error",
                        "content": "JSON non valido. Invia {'message': '...'}",
                    }
                )
                continue

            user_message = payload.get("message")
            if not isinstance(user_message, str) or not user_message.strip():
                await websocket.send_json(
                    {
                        "type": "error",
                        "content": "Campo 'message' mancante o non valido.",
                    }
                )
                continue

            response, history = await chat_service.handle(user_message, history)
            await websocket.send_json({"type": "text", "content": response})

    except WebSocketDisconnect:
        logger.info("Client WebSocket disconnesso")
    except Exception as exc:
        logger.exception("Errore WebSocket")
        try:
            await websocket.send_json(
                {"type": "error", "content": f"Errore interno: {exc}"}
            )
        except RuntimeError:
            pass
