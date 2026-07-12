from __future__ import annotations

import json

import httpx
import pytest

from orchestratore_llm.schemas.prediction import PredictionRequest
from orchestratore_llm.services.block1_client import Block1Client


def _mock_handler(request: httpx.Request):
    body = json.loads(request.content)
    assert body["cliente"] == "Carrefour"
    response = {
        "stockout_risk_percent": 12.5,
        "waste_risk_percent": 3.0,
        "expected_shortfall_units": 30.0,
        "message": "ok",
    }
    return httpx.Response(200, json=response)


@pytest.mark.asyncio
async def test_predict_success():
    client = Block1Client(
        base_url="http://block1.test",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(_mock_handler)),
    )
    request = PredictionRequest(
        cliente="Carrefour",
        categoria_prodotto="pinse",
        variazione_ordine_percentuale=20.0,
    )
    response = await client.predict(request)
    assert response.stockout_risk_percent == 12.5
    assert response.waste_risk_percent == 3.0
    await client.close()
