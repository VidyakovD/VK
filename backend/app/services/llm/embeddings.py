from functools import lru_cache

from openai import AsyncOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger
from app.services.llm.base import build_httpx_client

log = get_logger(__name__)


class EmbeddingsClient:
    """OpenAI embeddings (text-embedding-3-small by default)."""

    # text-embedding-3-small dimensions
    DIMENSIONS_BY_MODEL = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
    }

    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key, http_client=build_httpx_client())
        self._model = model

    @property
    def dimensions(self) -> int:
        return self.DIMENSIONS_BY_MODEL.get(self._model, 1536)

    @property
    def model(self) -> str:
        return self._model

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        log.info("embeddings.start", model=self._model, count=len(texts))
        resp = await self._client.embeddings.create(model=self._model, input=texts)
        log.info("embeddings.done", model=self._model, tokens=resp.usage.total_tokens)
        return [item.embedding for item in resp.data]

    async def embed_one(self, text: str) -> list[float]:
        result = await self.embed([text])
        return result[0]


@lru_cache(maxsize=1)
def get_embeddings_client() -> EmbeddingsClient:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return EmbeddingsClient(
        api_key=settings.openai_api_key,
        model=settings.openai_model_embedding,
    )
