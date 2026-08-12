import logging
from datetime import datetime, timedelta
from arq.connections import RedisSettings
from app.config import settings
from sqlmodel import Session
from app.database import engine
from app.models.notification import Notification, NotificationStatus

logger = logging.getLogger(__name__)
MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 10


async def process_notification(ctx, notification_id: int):
    with Session(engine) as session:
        notification = session.get(Notification, notification_id)
        if not notification:
            logger.error(f"Notification {notification_id} not found")
            return

        notification.status = NotificationStatus.processing
        notification.attempts += 1
        notification.updated_at = datetime.utcnow()
        session.add(notification)
        session.commit()

        try:
            logger.info(f"Processing notification {notification_id} for {notification.recipient}")
            notification.status = NotificationStatus.delivered
            notification.updated_at = datetime.utcnow()
            session.add(notification)
            session.commit()
            logger.info(f"Notification {notification_id} delivered successfully")

        except Exception as e:
            notification.last_error = str(e)
            notification.updated_at = datetime.utcnow()

            if notification.attempts >= MAX_ATTEMPTS:
                notification.status = NotificationStatus.failed
                logger.error(f"Notification {notification_id} failed permanently after {MAX_ATTEMPTS} attempts")
                session.add(notification)
                session.commit()
            else:
                notification.status = NotificationStatus.pending
                logger.warning(f"Notification {notification_id} failed, attempt {notification.attempts}/{MAX_ATTEMPTS}, retrying in {RETRY_DELAY_SECONDS}s")
                session.add(notification)
                session.commit()
                await ctx['redis'].enqueue_job(
                    'process_notification',
                    notification_id,
                    _defer_by=timedelta(seconds=RETRY_DELAY_SECONDS)
                )


class WorkerSettings:
    functions = [process_notification]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)