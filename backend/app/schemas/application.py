from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


ApplicationStatus = Literal[
    "saved",
    "applied",
    "interviewing",
    "offer",
    "rejected",
    "withdrawn",
]


class ApplicationCreateRequest(BaseModel):
    job_id: UUID
    status: ApplicationStatus = "saved"
    notes: str | None = Field(default=None, max_length=5000)


class ApplicationUpdateRequest(BaseModel):
    status: ApplicationStatus | None = None
    notes: str | None = Field(default=None, max_length=5000)


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    job_title: str
    company: str
    status: ApplicationStatus
    notes: str | None
    applied_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ApplicationListResponse(BaseModel):
    items: list[ApplicationResponse]
    total: int
    page: int
    limit: int
