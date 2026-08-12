from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.notification import NotificationStatus


class NotificationCreate(BaseModel):
    recipient: str
    message: str


class NotificationResponse(BaseModel):
    id: int
    recipient: str
    message: str
    status: NotificationStatus
    attempts: int
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
