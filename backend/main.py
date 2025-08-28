from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app_core.config import settings
from api.v1.api import api_router

app = FastAPI(
    title="Solution Agent API",
    description="Multi-agent solution writing system API",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")