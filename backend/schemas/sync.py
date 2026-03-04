from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SyncOperation(BaseModel):
    id: str
    operation: str  # create | update | delete
    resource_type: str
    resource_id: UUID | None = None
    payload: dict
    client_timestamp: datetime


class SyncResult(BaseModel):
    id: str
    status: str  # ok | conflict | error
    detail: str | None = None
    data: dict | None = None
    server_version: dict | None = None
