from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any

import httpx
from pydantic import BaseModel

from ..config import Settings
from .tools import Tool, ToolExecutor

logger = logging.getLogger(__name__)


class ToolCall(BaseModel):
    """Chiamata a tool restituita dall'LLM."""

    id: str
    name: str
    arguments: dict[str, Any]


class ChatMessage(BaseModel):
    """Messaggio di conversazione in formato provider-agnostic."""

    role: str  # user, assistant, tool
    content: str = ""
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] | None = None


class AssistantOutput(BaseModel):
    """Output grezzo del modello linguistico."""

    content: str = ""
    tool_calls: list[ToolCall] = []


class LLMClient(ABC):
    """Client astratto per l'interazione con LLM e tool use."""

    def __init__(self, max_tool_turns: int = 5):
        self.max_tool_turns = max_tool_turns

    async def run_conversation(
        self,
        messages: list[ChatMessage],
        system_prompt: str,
        tools: list[Tool],
        executor: ToolExecutor,
    ) -> tuple[str, list[ChatMessage]]:
        """Gestisce il loop di tool calling e restituisce la risposta finale."""
        current_messages = list(messages)

        for _ in range(self.max_tool_turns):
            output = await self._complete(current_messages, system_prompt, tools)

            assistant_message = ChatMessage(
                role="assistant",
                content=output.content,
                tool_calls=output.tool_calls if output.tool_calls else None,
            )
            current_messages.append(assistant_message)

            if not output.tool_calls:
                return output.content, current_messages

            for tool_call in output.tool_calls:
                try:
                    result = await executor.execute(tool_call.name, tool_call.arguments)
                except Exception as exc:  # pragma: no cover
                    logger.exception("Errore esecuzione tool %s", tool_call.name)
                    result = json.dumps({"error": str(exc)})
                current_messages.append(
                    ChatMessage(
                        role="tool",
                        content=result,
                        tool_call_id=tool_call.id,
                    )
                )

        return output.content, current_messages

    @abstractmethod
    async def _complete(
        self, messages: list[ChatMessage], system_prompt: str, tools: list[Tool]
    ) -> AssistantOutput:
        raise NotImplementedError

    async def close(self) -> None:
        """Rilascia risorse eventualmente allocate."""
        pass


class AnthropicLLMClient(LLMClient):
    """Client per le API Messages di Anthropic (Claude 3.5 Sonnet)."""

    API_URL = "https://api.anthropic.com/v1/messages"

    def __init__(
        self, settings: Settings, http_client: httpx.AsyncClient | None = None
    ):
        super().__init__(max_tool_turns=settings.max_tool_turns)
        self.api_key = settings.anthropic_api_key
        self.model = settings.llm_model
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature
        self.http_client = http_client or httpx.AsyncClient(timeout=60.0)

    def _build_messages(self, messages: list[ChatMessage]) -> list[dict[str, Any]]:
        formatted: list[dict[str, Any]] = []
        for msg in messages:
            if msg.role == "tool":
                formatted.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": msg.tool_call_id,
                                "content": msg.content,
                            }
                        ],
                    }
                )
            elif msg.role == "assistant":
                if msg.tool_calls:
                    content: list[dict[str, Any]] = []
                    if msg.content:
                        content.append({"type": "text", "text": msg.content})
                    for tc in msg.tool_calls:
                        content.append(
                            {
                                "type": "tool_use",
                                "id": tc.id,
                                "name": tc.name,
                                "input": tc.arguments,
                            }
                        )
                    formatted.append({"role": "assistant", "content": content})
                else:
                    formatted.append({"role": "assistant", "content": msg.content})
            else:
                formatted.append({"role": "user", "content": msg.content})
        return formatted

    async def _complete(
        self, messages: list[ChatMessage], system_prompt: str, tools: list[Tool]
    ) -> AssistantOutput:
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY non configurata")

        body: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": system_prompt,
            "messages": self._build_messages(messages),
        }
        if tools:
            body["tools"] = [tool.to_anthropic() for tool in tools]

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        response = await self.http_client.post(self.API_URL, json=body, headers=headers)
        response.raise_for_status()
        data = response.json()

        content_text = ""
        tool_calls: list[ToolCall] = []
        for block in data.get("content", []):
            if block.get("type") == "text":
                content_text += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block["id"],
                        name=block["name"],
                        arguments=block.get("input", {}),
                    )
                )

        return AssistantOutput(content=content_text, tool_calls=tool_calls)

    async def close(self) -> None:
        await self.http_client.aclose()


class OpenAILLMClient(LLMClient):
    """Client per le API Chat Completions di OpenAI."""

    DEFAULT_API_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(
        self, settings: Settings, http_client: httpx.AsyncClient | None = None
    ):
        super().__init__(max_tool_turns=settings.max_tool_turns)
        self.api_key = settings.openai_api_key
        self.api_url = self._resolve_api_url(settings.llm_base_url)
        self.model = settings.llm_model
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature
        self.http_client = http_client or httpx.AsyncClient(timeout=60.0)

    @classmethod
    def _resolve_api_url(cls, base_url: str | None) -> str:
        if not base_url:
            return cls.DEFAULT_API_URL
        base = base_url.rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        return f"{base}/chat/completions"

    def _build_messages(
        self, messages: list[ChatMessage], system_prompt: str
    ) -> list[dict[str, Any]]:
        formatted: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            if msg.role == "tool":
                formatted.append(
                    {
                        "role": "tool",
                        "tool_call_id": msg.tool_call_id,
                        "content": msg.content,
                    }
                )
            elif msg.role == "assistant":
                if msg.tool_calls:
                    tool_calls = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments),
                            },
                        }
                        for tc in msg.tool_calls
                    ]
                    formatted.append(
                        {
                            "role": "assistant",
                            "content": msg.content or None,
                            "tool_calls": tool_calls,
                        }
                    )
                else:
                    formatted.append({"role": "assistant", "content": msg.content})
            else:
                formatted.append({"role": "user", "content": msg.content})
        return formatted

    async def _complete(
        self, messages: list[ChatMessage], system_prompt: str, tools: list[Tool]
    ) -> AssistantOutput:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY non configurata")

        body: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": self._build_messages(messages, system_prompt),
        }
        if tools:
            body["tools"] = [tool.to_openai() for tool in tools]
            body["tool_choice"] = "auto"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "content-type": "application/json",
        }

        response = await self.http_client.post(self.api_url, json=body, headers=headers)
        response.raise_for_status()
        data = response.json()

        message = data["choices"][0]["message"]
        content_text = message.get("content") or ""
        tool_calls: list[ToolCall] = []
        for tc in message.get("tool_calls", []):
            try:
                args = json.loads(tc["function"]["arguments"])
            except (json.JSONDecodeError, KeyError):
                args = {}
            tool_calls.append(
                ToolCall(
                    id=tc["id"],
                    name=tc["function"]["name"],
                    arguments=args,
                )
            )

        return AssistantOutput(content=content_text, tool_calls=tool_calls)

    async def close(self) -> None:
        await self.http_client.aclose()


class MockLLMClient(LLMClient):
    """Client fittizio per test senza API key."""

    def __init__(self, max_tool_turns: int = 5):
        super().__init__(max_tool_turns=max_tool_turns)

    async def _complete(
        self, messages: list[ChatMessage], system_prompt: str, tools: list[Tool]
    ) -> AssistantOutput:
        # Se l'ultimo messaggio è un tool result, restituiamo un report fittizio
        if messages and messages[-1].role == "tool":
            try:
                data = json.loads(messages[-1].content)
            except json.JSONDecodeError:
                data = {}
            return AssistantOutput(
                content=(
                    "Ho analizzato i dati della simulazione. "
                    f"Rischio stock-out: {data.get('stockout_risk_percent', 'N/A')}%. "
                    f"Rischio spreco/scadenza: {data.get('waste_risk_percent', 'N/A')}%. "
                    "Raccomandazione: valutare un aggiustamento del piano di produzione in base ai rischi evidenziati."
                )
            )

        # Cerca l'ultimo messaggio utente
        user_message = ""
        for msg in reversed(messages):
            if msg.role == "user":
                user_message = msg.content
                break

        scenario_keywords = [
            "cosa succede",
            "simulazione",
            "scenario",
            "aumenta",
            "diminuisce",
            "ordine",
            "ordini",
            "produce",
            "produzione",
        ]
        if any(kw in user_message.lower() for kw in scenario_keywords):
            args = _extract_scenario_args(user_message)
            return AssistantOutput(
                content="",
                tool_calls=[
                    ToolCall(
                        id="mock_tool_call_1",
                        name="simulate_scenario",
                        arguments=args,
                    )
                ],
            )

        return AssistantOutput(
            content="Ciao, sono il tuo consulente di produzione alimentare. Come posso aiutarti?"
        )


def _extract_scenario_args(user_message: str) -> dict[str, Any]:
    """Estrae argomenti di scenario in modo euristico per il mock."""
    args: dict[str, Any] = {
        "cliente": "Carrefour",
        "categoria_prodotto": "pinse",
        "variazione_ordine_percentuale": 20.0,
        "orizzonte_giorni": 7,
    }

    cliente_match = re.search(r"(?:per|cliente|da)\s+([A-Z][a-zA-Z]+)", user_message)
    if cliente_match:
        args["cliente"] = cliente_match.group(1)

    lower = user_message.lower()
    if "fritt" in lower:
        args["categoria_prodotto"] = "fritti"
    elif "4" in lower or "quarta" in lower or "gamma" in lower:
        args["categoria_prodotto"] = "quarta_gamma"
    elif "pinse" in lower:
        args["categoria_prodotto"] = "pinse"

    var_match = re.search(r"([+-]?\d+(?:\.\d+)?)\s*%", user_message)
    if var_match:
        args["variazione_ordine_percentuale"] = float(var_match.group(1))

    if "diminuisce" in lower or "diminuzione" in lower or "riduce" in lower:
        args["variazione_ordine_percentuale"] = -abs(
            args["variazione_ordine_percentuale"]
        )

    return args


def get_llm_client(
    settings: Settings, http_client: httpx.AsyncClient | None = None
) -> LLMClient:
    provider = settings.llm_provider.lower()
    if provider == "anthropic":
        return AnthropicLLMClient(settings, http_client)
    if provider in ("openai", "windsurf"):
        # "windsurf" usa il client OpenAI-compatibile puntato su llm_base_url
        # (gateway Windsurf/SWE che espone /v1/chat/completions).
        return OpenAILLMClient(settings, http_client)
    if provider == "mock":
        return MockLLMClient(max_tool_turns=settings.max_tool_turns)
    raise ValueError(f"LLM provider non supportato: {settings.llm_provider}")
