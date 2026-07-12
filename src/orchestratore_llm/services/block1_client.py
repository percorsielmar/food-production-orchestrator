from __future__ import annotations

import logging
import math
import random
import statistics

import httpx

from ..schemas.prediction import PredictionRequest, PredictionResponse

logger = logging.getLogger(__name__)


CATEGORY_NAME_MAP = {
    "pinse": "Basi Pinsa",
    "fritti": "Fritti",
    "quarta_gamma": "4ª Gamma",
}


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

        try:
            response = await self.http_client.post(url, json=payload, headers=headers)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 409:
                logger.info("Modello Blocco 1 non addestrato, avvio training di default")
                await self._ensure_trained(request.n_features)
                response = await self.http_client.post(url, json=payload, headers=headers)
                response.raise_for_status()
            else:
                raise

        data = response.json()
        logger.info("Risposta Blocco 1: %s", data)
        return self._to_prediction_response(data, request)

    async def _ensure_trained(self, n_features: int) -> None:
        """Addestra un modello di default se Blocco 1 non ha ancora un checkpoint."""
        url = f"{self.base_url}/api/v1/train"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        rng = random.Random(42)
        base = 1000.0
        n_samples = 100
        samples = [
            [base + rng.gauss(0.0, 100.0) for _ in range(n_features)]
            for _ in range(n_samples)
        ]

        nodes = [max(n_features, 8), max(n_features // 2, 4), max(n_features // 4, 2)]

        payload = {
            "samples": samples,
            "hyperparams": {
                "n_epochs": 500,
                "batch_size": 4,
                "patience": 500,
                "nodes": nodes,
            },
            "nodes_central": 2,
        }

        logger.info("Training Blocco 1 di default: %s", payload)
        response = await self.http_client.post(
            url, json=payload, headers=headers, timeout=120.0
        )
        response.raise_for_status()
        logger.info("Training Blocco 1 completato: %s", response.json())

    def _to_prediction_response(
        self, data: dict[str, object], request: PredictionRequest
    ) -> PredictionResponse:
        """Converte la risposta grezza di Blocco 1 in PredictionResponse."""
        selected_name = CATEGORY_NAME_MAP[request.categoria_prodotto]
        scenarios = data.get("scenarios", [])

        values: list[float] = []
        for scenario in scenarios:
            if not isinstance(scenario, dict):
                continue
            cat_values = scenario.get(selected_name, [])
            if not cat_values:
                continue
            # Media dei valori per la categoria selezionata (n_samples * n_indices)
            values.append(float(sum(cat_values)) / len(cat_values))

        if not values:
            raise ValueError("Nessun valore di scenario trovato per la categoria selezionata")

        baseline = request._baseline()
        n = len(values)

        stockout_count = sum(1 for v in values if v > baseline)
        waste_count = sum(1 for v in values if v < baseline)
        expected_shortfall = sum(max(0.0, v - baseline) for v in values) / n
        expected_excess = sum(max(0.0, baseline - v) for v in values) / n

        mean = statistics.mean(values)
        std = statistics.pstdev(values) if n >= 1 else 0.0
        min_val = min(values)
        max_val = max(values)
        p5 = _percentile(values, 5.0)
        p95 = _percentile(values, 95.0)

        stockout_risk = (stockout_count / n) * 100.0
        waste_risk = (waste_count / n) * 100.0

        message = (
            f"Simulazione per {request.cliente} - {selected_name}: "
            f"rischio stock-out {stockout_risk:.1f}%, "
            f"rischio spreco/scadenza {waste_risk:.1f}%, "
            f"shortfall medio {expected_shortfall:.1f} unita', "
            f"eccesso medio {expected_excess:.1f} unita'."
        )

        return PredictionResponse(
            stockout_risk_percent=round(stockout_risk, 2),
            waste_risk_percent=round(waste_risk, 2),
            expected_shortfall_units=round(expected_shortfall, 2),
            expected_excess_units=round(expected_excess, 2),
            distribution_summary={
                "mean": round(mean, 2),
                "std": round(std, 2),
                "min": round(min_val, 2),
                "max": round(max_val, 2),
                "p5": round(p5, 2),
                "p95": round(p95, 2),
            },
            message=message,
        )

    async def close(self) -> None:
        await self.http_client.aclose()


def _percentile(values: list[float], percentile: float) -> float:
    """Calcola un percentile con interpolazione lineare."""
    sorted_values = sorted(values)
    n = len(sorted_values)
    if n == 1:
        return sorted_values[0]
    idx = (n - 1) * (percentile / 100.0)
    lower = math.floor(idx)
    upper = math.ceil(idx)
    if lower == upper:
        return sorted_values[int(idx)]
    weight = idx - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight
