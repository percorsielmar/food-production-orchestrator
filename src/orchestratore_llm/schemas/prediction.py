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
        default=None, ge=0, description="Volume ordine corrente in unita'"
    )
    note: str | None = Field(default=None, description="Note aggiuntive")

    # Parametri tecnici del modello (default ragionevoli per l'integrazione)
    n_features: int = Field(default=3, ge=1, exclude=True)
    n_scenarios: int = Field(default=200, ge=1, le=10000, exclude=True)
    noise_std: float | None = Field(default=None, ge=0.0, exclude=True)

    def _selected_category_index(self) -> int:
        return {"pinse": 0, "fritti": 1, "quarta_gamma": 2}[self.categoria_prodotto]

    def _baseline(self) -> float:
        return self.volume_ordine_corrente if self.volume_ordine_corrente is not None else 1000.0

    def _target(self) -> float:
        return self._baseline() * (1.0 + self.variazione_ordine_percentuale / 100.0)

    def _compute_noise_std(self) -> float:
        if self.noise_std is not None:
            return self.noise_std
        return 0.1 + min(0.4, self.orizzonte_giorni / 60.0)

    def to_block1_payload(self) -> dict[str, Any]:
        """Trasforma la richiesta utente nel formato atteso da Blocco 1."""
        baseline = self._baseline()
        target = self._target()
        selected = self._selected_category_index()

        sample = [target if i == selected else baseline for i in range(self.n_features)]

        category_map = {
            "Basi Pinsa": [0],
            "Fritti": [1],
            "4ª Gamma": [2],
        }

        return {
            "samples": [sample],
            "n_scenarios": self.n_scenarios,
            "noise_std": self._compute_noise_std(),
            "category_map": category_map,
        }


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
