from __future__ import annotations

import logging

import httpx

from ..schemas.prediction import PredictionRequest, PredictionResponse

logger = logging.getLogger(__name__)


class Block1Client:
    """Client per il microservizio analitico (Blocco 1)."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.http_client = http_client or httpx.AsyncClient(timeout=30.0)

    async def predict(self, request: PredictionRequest) -> PredictionResponse:
        url = f"{self.base_url}/api/v1/predict"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = request.to_block1_payload()
        logger.info("Chiamata Blocco 1: %s con payload %s", url, payload)

        response = await self.http_client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        logger.info("Risposta Blocco 1: %s", data)
        return PredictionResponse.model_validate(data)

    async def close(self) -> None:
        await self.http_client.aclose()
