from functools import lru_cache

from anthropic import AsyncAnthropic
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger
from app.services.llm.base import LLMMessage, LLMResponse, build_httpx_client

log = get_logger(__name__)


class AnthropicClient:
    """Async Anthropic Messages API wrapper with proxy + retries."""

    def __init__(self, api_key: str, default_model: str) -> None:
        self._client = AsyncAnthropic(api_key=api_key, http_client=build_httpx_client())
        self._default_model = default_model

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def chat(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        mdl = model or self._default_model
        # Anthropic separates system message from user/assistant turns.
        system_parts = [m.content for m in messages if m.role == "system"]
        turns = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role in ("user", "assistant")
        ]
        log.info("anthropic.chat.start", model=mdl, msg_count=len(turns))
        resp = await self._client.messages.create(
            model=mdl,
            system="\n\n".join(system_parts) if system_parts else None,
            messages=turns,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        text = "".join(block.text for block in resp.content if block.type == "text")
        log.info(
            "anthropic.chat.done",
            model=mdl,
            tokens_in=resp.usage.input_tokens,
            tokens_out=resp.usage.output_tokens,
        )
        return LLMResponse(
            text=text,
            tokens_in=resp.usage.input_tokens,
            tokens_out=resp.usage.output_tokens,
            model=mdl,
            provider="anthropic",
            finish_reason=resp.stop_reason,
            raw=resp.model_dump(),
        )


@lru_cache(maxsize=1)
def get_anthropic_client() -> AnthropicClient:
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    return AnthropicClient(
        api_key=settings.anthropic_api_key,
        default_model=settings.anthropic_model_dialog,
    )
