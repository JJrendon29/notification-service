from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel


class NotificationStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    delivered = "delivered"
    failed = "failed"


class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    recipient: str
    message: str
    status: NotificationStatus = Field(default=NotificationStatus.pending)
    attempts: int = Field(default=0)
    last_error: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
