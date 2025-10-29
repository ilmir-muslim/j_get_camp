# core/telegram.py
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_telegram_message(message: str, chat_ids=None):
    """
    Отправка сообщения в Telegram одному или нескольким пользователям
    """
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)

    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not configured")
        return False

    # Если chat_ids не указан, используем настройки из settings.py
    if chat_ids is None:
        chat_ids = getattr(settings, "TELEGRAM_CHAT_ID", None)

    if not chat_ids:
        logger.warning("TELEGRAM_CHAT_ID not configured")
        return False

    # Преобразуем в список, если передан одиночный chat_id
    if not isinstance(chat_ids, list):
        chat_ids = [chat_ids]

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    success_count = 0
    for chat_id in chat_ids:
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}

        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"Telegram message sent to chat {chat_id}")
                success_count += 1
            else:
                logger.error(
                    f"Telegram API error for chat {chat_id}: {response.json()}"
                )
        except Exception as e:
            logger.error(f"Error sending Telegram message to chat {chat_id}: {e}")

    return success_count > 0
