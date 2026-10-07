from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ResumeGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: UUID
