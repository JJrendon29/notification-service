from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.notification import NotificationStatus
from pydantic import BaseModel, EmailStr


class NotificationCreate(BaseModel):
    recipient: EmailStr
    message: str


class NotificationResponse(BaseModel):
    id: int
    recipient: EmailStr
    message: str
    status: NotificationStatus
    attempts: int
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
