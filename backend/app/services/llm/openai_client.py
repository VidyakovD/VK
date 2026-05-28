from functools import lru_cache

from openai import AsyncOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger
from app.services.llm.base import LLMMessage, LLMResponse, build_httpx_client

log = get_logger(__name__)


class OpenAIClient:
    """Async OpenAI chat completions wrapper with proxy + retries."""

    def __init__(self, api_key: str, default_model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key, http_client=build_httpx_client())
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
        max_tokens: int | None = 1024,
    ) -> LLMResponse:
        mdl = model or self._default_model
        log.info("openai.chat.start", model=mdl, msg_count=len(messages))
        resp = await self._client.chat.completions.create(
            model=mdl,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        usage = resp.usage
        choice = resp.choices[0]
        log.info(
            "openai.chat.done",
            model=mdl,
            tokens_in=usage.prompt_tokens if usage else 0,
            tokens_out=usage.completion_tokens if usage else 0,
        )
        return LLMResponse(
            text=choice.message.content or "",
            tokens_in=usage.prompt_tokens if usage else 0,
            tokens_out=usage.completion_tokens if usage else 0,
            model=mdl,
            provider="openai",
            finish_reason=choice.finish_reason,
            raw=resp.model_dump(),
        )


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAIClient:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAIClient(
        api_key=settings.openai_api_key,
        default_model=settings.openai_model_dialog,
    )
