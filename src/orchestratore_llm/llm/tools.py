from __future__ import annotations

from typing import Any, Awaitable, Callable

from ..schemas.prediction import PredictionRequest
from ..services.block1_client import Block1Client


class Tool:
    """Definizione di un tool disponibile per l'LLM."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: Callable[[dict[str, Any], dict[str, Any]], Awaitable[str]],
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler

    def to_anthropic(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }

    def to_openai(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


async def _simulate_scenario_handler(
    arguments: dict[str, Any], dependencies: dict[str, Any]
) -> str:
    """Esegue la simulazione chiamando il microservizio analitico (Blocco 1)."""
    request = PredictionRequest(**arguments)
    block1_client: Block1Client = dependencies["block1_client"]
    response = await block1_client.predict(request)
    return response.model_dump_json()


SIMULATE_SCENARIO_SCHEMA = {
    "type": "object",
    "properties": {
        "cliente": {
            "type": "string",
            "description": "Cliente o canale di vendita coinvolto (es. Carrefour, Conad, punto vendio)",
        },
        "categoria_prodotto": {
            "type": "string",
            "enum": ["pinse", "fritti", "quarta_gamma"],
            "description": "Categoria prodotto oggetto della simulazione",
        },
        "variazione_ordine_percentuale": {
            "type": "number",
            "description": "Variazione percentuale dell'ordine. Esempio: 20 per +20%, -15 per -15%.",
        },
        "orizzonte_giorni": {
            "type": "integer",
            "default": 7,
            "description": "Orizzonte temporale in giorni per la simulazione",
        },
        "volume_ordine_corrente": {
            "type": "number",
            "description": "Volume ordine corrente in unità (opzionale)",
            "default": None,
        },
        "note": {
            "type": "string",
            "description": "Note aggiuntive per la simulazione (opzionale)",
            "default": None,
        },
    },
    "required": ["cliente", "categoria_prodotto", "variazione_ordine_percentuale"],
}


TOOLS: list[Tool] = [
    Tool(
        name="simulate_scenario",
        description=(
            "Esegue una simulazione Semi-Monte Carlo sul piano di produzione alimentare. "
            "Utilizza questo strumento per qualsiasi domanda di scenario, simulazione o "
            "'cosa succede se...'. Non inventare numeri: chiama sempre questo tool per ottenere "
            "dati probabilistici."
        ),
        parameters=SIMULATE_SCENARIO_SCHEMA,
        handler=_simulate_scenario_handler,
    )
]


class ToolExecutor:
    """Esegue i tool registrati risolvendo le dipendenze."""

    def __init__(self, dependencies: dict[str, Any] | None = None):
        self._tools = {tool.name: tool for tool in TOOLS}
        self._dependencies = dependencies or {}

    async def execute(self, name: str, arguments: dict[str, Any]) -> str:
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Tool non trovato: {name}")
        return await tool.handler(arguments, self._dependencies)
