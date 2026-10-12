from __future__ import annotations

import json

import httpx
import pytest

from orchestratore_llm.schemas.prediction import PredictionRequest
from orchestratore_llm.services.block1_client import Block1Client


def _mock_handler(request: httpx.Request):
    body = json.loads(request.content)
    assert request.url.path == "/api/v1/predict"
    assert body["samples"] == [[1200.0, 1000.0, 1000.0]]
    assert body["category_map"]["Basi Pinsa"] == [0]
    scenarios = [{"Basi Pinsa": [v]} for v in (1100.0, 1100.0, 1100.0, 900.0)]
    return httpx.Response(200, json={"scenarios": scenarios})


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
    assert response.stockout_risk_percent == 75.0
    assert response.waste_risk_percent == 25.0
    await client.close()
