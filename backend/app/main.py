from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes.auth import router as auth_router
from app.api.routes.applications import router as applications_router
from app.api.routes.job import router as job_router
from app.api.routes.job_discovery import (
    router as job_discovery_router,
)
from app.api.routes.job_ingestion import (
    router as job_ingestion_router,
)
from app.api.routes.job_intelligence import (
    router as job_intelligence_router,
)
from app.api.routes.matching import router as matching_router
from app.api.routes.resume import router as resume_router
from app.db.database import AsyncSessionLocal


app = FastAPI(
    title="CareerPilot API",
    version="0.1.0",
)


app.include_router(auth_router)
app.include_router(applications_router)
app.include_router(job_intelligence_router)
app.include_router(job_router)
app.include_router(job_ingestion_router)
app.include_router(job_discovery_router)
app.include_router(matching_router)
app.include_router(resume_router)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "careerpilot-api",
    }


@app.get("/health/db")
async def database_health_check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected",
            "result": result.scalar(),
        }