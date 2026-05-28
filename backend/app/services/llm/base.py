from dataclasses import dataclass, field
from typing import Literal

import httpx

from app.core.config import settings


Role = Literal["system", "user", "assistant"]


@dataclass
class LLMMessage:
    role: Role
    content: str


@dataclass
class LLMResponse:
    """Unified response shape across providers."""

    text: str
    tokens_in: int
    tokens_out: int
    model: str
    provider: Literal["openai", "anthropic"]
    finish_reason: str | None = None
    raw: dict = field(default_factory=dict)


def build_httpx_client(timeout: float = 60.0) -> httpx.AsyncClient:
    """
    httpx client configured with outbound proxy if set in env.
    All LLM SDKs accept httpx.AsyncClient for transport injection.
    """
    proxy = settings.https_proxy or settings.http_proxy
    transport_kwargs: dict = {"timeout": timeout}
    if proxy:
        transport_kwargs["proxy"] = proxy
    return httpx.AsyncClient(**transport_kwargs)
