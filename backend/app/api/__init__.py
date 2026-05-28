from fastapi import APIRouter

from app.api.routes import agents, auth, billing, chat, communities, health

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(communities.router)
api_router.include_router(agents.router)
api_router.include_router(chat.router)
api_router.include_router(billing.router)

# Health endpoint outside /api prefix (used by Docker/k8s probes)
health_router = APIRouter()
health_router.include_router(health.router)
