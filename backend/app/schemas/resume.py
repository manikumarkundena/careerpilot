from uuid import UUID

from pydantic import BaseModel


class ResumeGenerateRequest(BaseModel):
    job_id: UUID
