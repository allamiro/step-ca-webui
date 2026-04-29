from datetime import datetime

from pydantic import BaseModel


class JobOut(BaseModel):
    id: int
    task_name: str
    status: str
    requested_by: str
    created_at: datetime
    updated_at: datetime
    error: str | None = None

    class Config:
        from_attributes = True
