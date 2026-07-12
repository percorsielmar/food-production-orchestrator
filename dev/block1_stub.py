"""Stub locale del microservizio analitico (Blocco 1) per testare l'orchestratore."""

from __future__ import annotations

import random
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Rende importabili il package src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from orchestratore_llm.schemas.prediction import PredictionRequest, PredictionResponse

app = FastAPI(title="Blocco 1 Stub - Semi-Monte Carlo")


@app.exception_handler(RequestValidationError)
async def validation_handler(request, exc):
    return JSONResponse({"detail": str(exc)}, status_code=422)


@app.post("/api/v1/predict")
async def predict(request: PredictionRequest) -> PredictionResponse:
    """Restituisce una risposta probabilistica euristica per test."""
    var = request.variazione_ordine_percentuale
    horizon = request.orizzonte_giorni

    # Euristica: aumento ordine -> maggiore rischio stock-out se var negativa;
    # maggiore rischio spreco se var eccessivamente positiva per 4a gamma.
    base_stockout = max(0.0, min(100.0, 50.0 - var * 1.5 + (100 - horizon) * 0.1))
    base_waste = max(0.0, min(100.0, 10.0 + var * 0.8 + (horizon - 7) * 0.5))

    # Piccola variazione pseudo-casuale per simulare probabilità
    stockout = round(max(0.0, min(100.0, base_stockout + random.uniform(-3, 3))), 2)
    waste = round(max(0.0, min(100.0, base_waste + random.uniform(-2, 2))), 2)

    return PredictionResponse(
        stockout_risk_percent=stockout,
        waste_risk_percent=waste,
        expected_shortfall_units=round(base_stockout * 2.5, 0)
        if request.categoria_prodotto in ("pinse", "fritti")
        else None,
        expected_excess_units=round(base_waste * 1.5, 0)
        if request.categoria_prodotto == "quarta_gamma"
        else None,
        distribution_summary={
            "p10_stockout": round(max(0.0, stockout - 15), 2),
            "p50_stockout": stockout,
            "p90_stockout": round(min(100.0, stockout + 15), 2),
            "p10_waste": round(max(0.0, waste - 10), 2),
            "p50_waste": waste,
            "p90_waste": round(min(100.0, waste + 10), 2),
        },
        message="Simulazione Semi-Monte Carlo eseguita con dati campione.",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7000)
