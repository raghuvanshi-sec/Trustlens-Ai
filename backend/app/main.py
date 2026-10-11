from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.investigation import router as investigation_router

app = FastAPI(
    title="TrustLens AI",
    description="AI-powered investigation engine for suspicious job offers",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:4173", "http://127.0.0.1:4173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "TrustLens AI"}


app.include_router(investigation_router, prefix="/api")
