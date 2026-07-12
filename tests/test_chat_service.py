from __future__ import annotations

import json

import httpx
import pytest

from orchestratore_llm.chat_service import ChatService
from orchestratore_llm.llm import ToolExecutor
from orchestratore_llm.llm.client import MockLLMClient
from orchestratore_llm.services.block1_client import Block1Client


def _mock_block1_handler(request: httpx.Request):
    body = json.loads(request.content)
    return httpx.Response(
        200,
        json={
            "stockout_risk_percent": 10.0,
            "waste_risk_percent": 2.0,
            "categoria_prodotto": body["categoria_prodotto"],
            "message": "ok",
        },
    )


@pytest.mark.asyncio
async def test_chat_service_invokes_tool():
    http_client = httpx.AsyncClient(transport=httpx.MockTransport(_mock_block1_handler))
    block1_client = Block1Client(base_url="http://block1.test", http_client=http_client)
    tool_executor = ToolExecutor(dependencies={"block1_client": block1_client})
    llm_client = MockLLMClient(max_tool_turns=5)
    chat_service = ChatService(llm_client=llm_client, tool_executor=tool_executor)

    response, history = await chat_service.handle(
        "Cosa succede se Carrefour aumenta l'ordine di pinse del 20%?",
        [],
    )

    assert "stock-out" in response.lower() or "spreco" in response.lower()
    assert len(history) > 2

    await block1_client.close()


@pytest.mark.asyncio
async def test_chat_service_greeting():
    block1_client = Block1Client(base_url="http://block1.test")
    tool_executor = ToolExecutor(dependencies={"block1_client": block1_client})
    llm_client = MockLLMClient(max_tool_turns=5)
    chat_service = ChatService(llm_client=llm_client, tool_executor=tool_executor)

    response, history = await chat_service.handle("Ciao", [])
    assert "consulente" in response.lower() or "aiutarti" in response.lower()

    await block1_client.close()
