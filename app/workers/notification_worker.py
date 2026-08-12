import logging
from datetime import datetime
from arq import cron
from arq.connections import RedisSettings
from app.config import settings
from sqlmodel import Session, select
from app.database import engine
from app.models.notification import Notification, NotificationStatus

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3


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
            # Simulamos el procesamiento de la notificacion
            # En produccion real aqui iria: enviar email, push notification, webhook, etc.
            logger.info(f"Processing notification {notification_id} for {notification.recipient}")

            # Simulamos que la entrega fue exitosa
            notification.status = NotificationStatus.delivered
            notification.updated_at = datetime.utcnow()
            session.add(notification)
            session.commit()

            logger.info(f"Notification {notification_id} delivered successfully")
            raise Exception("Simulando fallo del servidor de notificaciones")

        except Exception as e:
            notification.last_error = str(e)
            notification.updated_at = datetime.utcnow()

            if notification.attempts >= MAX_ATTEMPTS:
                notification.status = NotificationStatus.failed
                logger.error(f"Notification {notification_id} moved to dead letter queue after {MAX_ATTEMPTS} attempts")
            else:
                notification.status = NotificationStatus.pending
                logger.warning(f"Notification {notification_id} failed, attempt {notification.attempts}/{MAX_ATTEMPTS}")

            session.add(notification)
            session.commit()
            raise


class WorkerSettings:
    functions = [process_notification]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)

    def __init__(self):
        from arq.connections import RedisSettings
        from app.config import settings
        self.redis_settings = RedisSettings.from_dsn(settings.redis_url)
