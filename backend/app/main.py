from fastapi import FastAPI
from app.api.routes.investigation import router as investigation_router

app = FastAPI(
    title="TrustLens AI",
    description="AI-powered investigation engine for suspicious job offers",
    version="0.1.0"
)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "TrustLens AI"
    }


app.include_router(
    investigation_router,
    prefix="/api"
)