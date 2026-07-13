from __future__ import annotations

import pytest

from orchestratore_llm.config import Settings
from orchestratore_llm.llm.client import (
    OpenAILLMClient,
    get_llm_client,
)


def test_windsurf_provider_uses_openai_compatible_client():
    settings = Settings(
        llm_provider="windsurf",
        openai_api_key="test-key",
        llm_base_url="http://localhost:3003/v1",
        llm_model="cognition-swe-1.5",
    )
    client = get_llm_client(settings)
    assert isinstance(client, OpenAILLMClient)
    assert client.api_url == "http://localhost:3003/v1/chat/completions"
    assert client.model == "cognition-swe-1.5"


def test_openai_client_defaults_without_base_url():
    settings = Settings(llm_provider="openai", openai_api_key="test-key")
    client = get_llm_client(settings)
    assert isinstance(client, OpenAILLMClient)
    assert client.api_url == OpenAILLMClient.DEFAULT_API_URL


@pytest.mark.parametrize(
    "base_url,expected",
    [
        ("http://gw/v1", "http://gw/v1/chat/completions"),
        ("http://gw/v1/", "http://gw/v1/chat/completions"),
        ("http://gw/v1/chat/completions", "http://gw/v1/chat/completions"),
        (None, OpenAILLMClient.DEFAULT_API_URL),
    ],
)
def test_resolve_api_url(base_url, expected):
    assert OpenAILLMClient._resolve_api_url(base_url) == expected
