from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.job_discovery import (
    JobDiscoveryRequest,
    JobDiscoveryResponse,
)
from app.services.job_discovery.service import JobDiscoveryService
from app.services.job_ingestion.registry import (
    create_default_registry,
)


router = APIRouter(
    prefix="/api/v1/jobs",
    tags=["Job Discovery"],
)


def get_discovery_service() -> JobDiscoveryService:
    return JobDiscoveryService(
        registry=create_default_registry(),
    )


@router.post(
    "/discover",
    response_model=JobDiscoveryResponse,
)
async def discover_jobs(
    payload: JobDiscoveryRequest,
    session: AsyncSession = Depends(get_db),
    service: JobDiscoveryService = Depends(
        get_discovery_service,
    ),
):
    try:
        result = await service.discover(
            session,
            source=payload.source,
            query=payload.query,
            location=payload.location,
            page=payload.page,
            limit=payload.limit,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return JobDiscoveryResponse(
        source=payload.source,
        query=payload.query,
        location=payload.location,
        fetched=result["fetched"],
        created=result["created"],
        updated=result["updated"],
    )
