# core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Ticket
from core.telegram import send_telegram_message
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Ticket)
def send_telegram_notification(sender, instance, created, **kwargs):
    """
    Отправляет уведомление в Telegram при создании нового тикета
    """
    if created:
        message = (
            f"🚨 <b>Новый тикет #{instance.id}</b>\n"
            f"👤 <b>Пользователь:</b> {instance.user.username}\n"
            f"📝 <b>Тема:</b> {instance.subject}\n"
            f"📄 <b>Описание:</b>\n{instance.description[:500]}"
        )

        send_telegram_message(message)
