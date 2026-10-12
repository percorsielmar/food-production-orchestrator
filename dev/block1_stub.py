"""Stub locale del microservizio analitico (Blocco 1) per testare l'orchestratore.

Espone lo stesso contratto del Blocco 1 reale (`blocco1-backend/main.py`):
`POST /api/v1/train` e `POST /api/v1/predict` con `samples`, `n_scenarios`,
`noise_std`, `category_map` -> `{"scenarios": [{categoria: [valori]}]}`.
"""

from __future__ import annotations

import random

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Blocco 1 Stub - Semi-Monte Carlo")

DEFAULT_CATEGORY_MAP = {"Basi Pinsa": [0], "Fritti": [1], "4ª Gamma": [2]}


class TrainRequest(BaseModel):
    samples: list[list[float]]


class PredictRequest(BaseModel):
    samples: list[list[float]] = Field(..., min_length=1)
    n_scenarios: int = Field(default=100, ge=1, le=10000)
    noise_std: float = Field(default=0.1, ge=0.0)
    category_map: dict[str, list[int]] | None = None


@app.exception_handler(RequestValidationError)
async def validation_handler(request, exc):
    return JSONResponse({"detail": str(exc)}, status_code=422)


@app.post("/api/v1/train")
async def train(request: TrainRequest) -> dict[str, object]:
    return {"status": "trained", "n_samples": len(request.samples)}


@app.post("/api/v1/predict")
async def predict(request: PredictRequest) -> dict[str, object]:
    """Scenari euristici: ogni scenario ricostruisce i campioni attorno alla
    media di colonna con rumore relativo `noise_std`."""
    n_features = len(request.samples[0])
    means = [sum(row[i] for row in request.samples) / len(request.samples) for i in range(n_features)]
    category_map = request.category_map or DEFAULT_CATEGORY_MAP

    scenarios = []
    for _ in range(request.n_scenarios):
        reconstructed = [
            [max(0.0, means[i] * (1.0 + random.gauss(0.0, request.noise_std))) for i in range(n_features)]
            for _ in request.samples
        ]
        scenarios.append(
            {
                name: [row[i] for row in reconstructed for i in indices if i < n_features]
                for name, indices in category_map.items()
            }
        )

    return {"scenarios": scenarios, "n_scenarios": request.n_scenarios}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7000)
