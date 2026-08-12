from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from arq.connections import ArqRedis, create_pool, RedisSettings
from app.database import get_session
from app.models.notification import Notification, NotificationStatus
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.config import settings

router = APIRouter(prefix="/notifications", tags=["notifications"])


async def get_redis() -> ArqRedis:
    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    return redis


@router.post("/", response_model=NotificationResponse, status_code=202)
async def create_notification(
    notification_data: NotificationCreate,
    session: Session = Depends(get_session)
):
    notification = Notification(
        recipient=notification_data.recipient,
        message=notification_data.message
    )
    session.add(notification)
    session.commit()
    session.refresh(notification)

    redis = await get_redis()
    await redis.enqueue_job("process_notification", notification.id)
    await redis.close()

    return notification


@router.get("/", response_model=List[NotificationResponse])
def get_notifications(
    status: NotificationStatus = None,
    session: Session = Depends(get_session)
):
    query = select(Notification)
    if status:
        query = query.where(Notification.status == status)
    return session.exec(query).all()


@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification(notification_id: int, session: Session = Depends(get_session)):
    notification = session.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notificacion no encontrada")
    return notification
