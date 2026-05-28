from contextlib import asynccontextmanager
from typing import AsyncIterator

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router, health_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

configure_logging()
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    log.info("startup", env=settings.env, debug=settings.debug)
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.env,
            traces_sample_rate=0.1 if settings.is_production else 1.0,
        )
        log.info("sentry.enabled")
    yield
    log.info("shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="VK SaaS for Entrepreneurs",
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # CORS — на проде ограничить доменами VK Mini App + наш фронт.
    allowed_origins = [
        settings.frontend_url,
        "https://vk.com",
        "https://m.vk.com",
        "https://prod-app*.pages.vk-apps.com",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if settings.prometheus_enabled:
        from prometheus_fastapi_instrumentator import Instrumentator

        Instrumentator().instrument(app).expose(app, include_in_schema=False)

    app.include_router(health_router)
    app.include_router(api_router)

    return app


app = create_app()
