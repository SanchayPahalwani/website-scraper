import logging
from .base import NotificationStrategy

logger = logging.getLogger(__name__)

class ConsoleNotification(NotificationStrategy):
    async def notify(self, message:str):
        logger.info(message)
