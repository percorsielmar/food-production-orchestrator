from __future__ import annotations

from .llm.client import ChatMessage, LLMClient
from .llm.system_prompt import SYSTEM_PROMPT
from .llm.tools import TOOLS, ToolExecutor


class ChatService:
    """Orchestra la conversazione utente-LLM-Blocco1."""

    def __init__(
        self,
        llm_client: LLMClient,
        tool_executor: ToolExecutor,
        system_prompt: str = SYSTEM_PROMPT,
    ):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.system_prompt = system_prompt

    async def handle(
        self, user_message: str, history: list[ChatMessage]
    ) -> tuple[str, list[ChatMessage]]:
        """Processa un messaggio utente e restituisce la risposta e lo storico aggiornato."""
        messages = list(history)
        messages.append(ChatMessage(role="user", content=user_message))

        response, updated_messages = await self.llm_client.run_conversation(
            messages=messages,
            system_prompt=self.system_prompt,
            tools=TOOLS,
            executor=self.tool_executor,
        )

        return response, updated_messages
