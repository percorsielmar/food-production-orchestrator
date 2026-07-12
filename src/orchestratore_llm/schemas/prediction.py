from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class PredictionRequest(BaseModel):
    """Richiesta per il microservizio analitico (Blocco 1)."""

    model_config = ConfigDict(extra="ignore")

    cliente: str = Field(..., description="Cliente o canale di vendita (es. Carrefour)")
    categoria_prodotto: Literal["pinse", "fritti", "quarta_gamma"] = Field(
        ..., description="Categoria prodotto coinvolta"
    )
    variazione_ordine_percentuale: float = Field(
        ..., ge=-100.0, le=1000.0, description="Variazione percentuale ordine"
    )
    orizzonte_giorni: int = Field(
        default=7, ge=1, le=365, description="Orizzonte temporale in giorni"
    )
    volume_ordine_corrente: float | None = Field(
        default=None, ge=0, description="Volume ordine corrente in unità"
    )
    note: str | None = Field(default=None, description="Note aggiuntive")

    def to_block1_payload(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True, by_alias=False)


class PredictionResponse(BaseModel):
    """Risposta probabilistica del microservizio analitico (Blocco 1)."""

    model_config = ConfigDict(extra="allow")

    stockout_risk_percent: float = Field(
        ..., ge=0.0, le=100.0, description="Rischio di stock-out per pinse/fritti (%)"
    )
    waste_risk_percent: float = Field(
        ..., ge=0.0, le=100.0, description="Rischio di spreco/scadenza per 4ª gamma (%)"
    )
    expected_shortfall_units: float | None = None
    expected_excess_units: float | None = None
    distribution_summary: dict[str, float] | None = None
    message: str | None = None
