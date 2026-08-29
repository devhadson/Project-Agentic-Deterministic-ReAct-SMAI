from fastapi import APIRouter
from app.api.v1.endpoints import health, agent, auth, clinical, rag, audio, notifications

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(agent.router, prefix="/agent", tags=["Agent Tools API"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(clinical.router, prefix="/clinical", tags=["Clinical"])
api_router.include_router(rag.router, prefix="/rag", tags=["RAG"])
api_router.include_router(audio.router, prefix="/audio", tags=["Audio"])
api_router.include_router(notifications.router, prefix="/twilio", tags=["Notifications / Twilio"])