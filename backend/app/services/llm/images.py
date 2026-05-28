import base64
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from openai import AsyncOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger
from app.services.llm.base import build_httpx_client

log = get_logger(__name__)

ImageSize = Literal["1024x1024", "1024x1536", "1536x1024", "auto"]
ImageQuality = Literal["low", "medium", "high", "auto"]


@dataclass
class GeneratedImage:
    """Raw image bytes + metadata."""

    data: bytes  # decoded PNG/JPEG
    model: str
    size: str
    quality: str
    revised_prompt: str | None = None


class ImageClient:
    """gpt-image-2 generator (and fallback to DALL-E if configured)."""

    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key, http_client=build_httpx_client())
        self._model = model

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate(
        self,
        prompt: str,
        size: ImageSize = "1024x1024",
        quality: ImageQuality = "high",
        n: int = 1,
    ) -> list[GeneratedImage]:
        log.info("image.generate.start", model=self._model, size=size, quality=quality)
        resp = await self._client.images.generate(
            model=self._model,
            prompt=prompt,
            size=size,
            quality=quality,
            n=n,
        )
        out: list[GeneratedImage] = []
        for item in resp.data:
            if item.b64_json:
                out.append(
                    GeneratedImage(
                        data=base64.b64decode(item.b64_json),
                        model=self._model,
                        size=size,
                        quality=quality,
                        revised_prompt=getattr(item, "revised_prompt", None),
                    )
                )
        log.info("image.generate.done", model=self._model, count=len(out))
        return out


@lru_cache(maxsize=1)
def get_image_client() -> ImageClient:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return ImageClient(
        api_key=settings.openai_api_key,
        model=settings.openai_model_image,
    )
