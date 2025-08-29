from fastapi import APIRouter
from .endpoints import proposals, files, sessions, chat, pipeline

api_router = APIRouter()
api_router.include_router(proposals.router, prefix="/proposals", tags=["proposals"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(pipeline.router, prefix="/pipeline", tags=["pipeline"])