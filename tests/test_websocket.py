from __future__ import annotations

import json

import httpx
from fastapi.testclient import TestClient

from orchestratore_llm.main import app
from orchestratore_llm.services.block1_client import Block1Client


def _mock_block1_handler(request: httpx.Request):
    return httpx.Response(
        200,
        json={
            "stockout_risk_percent": 8.0,
            "waste_risk_percent": 1.5,
            "message": "ok",
        },
    )


def test_websocket_chat_simulation(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("BLOCK1_BASE_URL", "http://block1.test")

    mock_http = httpx.AsyncClient(transport=httpx.MockTransport(_mock_block1_handler))
    mock_block1 = Block1Client(base_url="http://block1.test", http_client=mock_http)

    with TestClient(app) as client:
        client.app.state.chat_service.tool_executor = __import__(
            "orchestratore_llm.llm.tools", fromlist=["ToolExecutor"]
        ).ToolExecutor(dependencies={"block1_client": mock_block1})

        with client.websocket_connect("/ws/chat") as ws:
            ws.send_text(
                json.dumps(
                    {
                        "message": "Cosa succede se Carrefour aumenta l'ordine di pinse del 20%?"
                    }
                )
            )
            data = ws.receive_json()

    assert data["type"] == "text"
    assert "stock-out" in data["content"].lower() or "spreco" in data["content"].lower()


def test_websocket_invalid_json(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    with TestClient(app) as client:
        with client.websocket_connect("/ws/chat") as ws:
            ws.send_text("not-json")
            data = ws.receive_json()

    assert data["type"] == "error"


def test_websocket_missing_message(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    with TestClient(app) as client:
        with client.websocket_connect("/ws/chat") as ws:
            ws.send_text(json.dumps({"foo": "bar"}))
            data = ws.receive_json()

    assert data["type"] == "error"
