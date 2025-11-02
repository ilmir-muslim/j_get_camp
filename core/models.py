import os
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from branches.models import City

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('manager', 'Менеджер'),
        ('admin', 'Администратор'),
        ('camp_head', 'Начальник лагеря'),
        ('lab_head', 'Начальник лаборатории'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="Роль")
    branch = models.ForeignKey('branches.Branch', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Филиал")
    schedules = models.ManyToManyField('schedule.Schedule', blank=True, verbose_name="Закрепленные смены")
    city = models.ForeignKey(
        City, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Город"
    )
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


def get_screenshot_upload_path(instance, filename):
    # Получаем расширение файла
    ext = filename.split(".")[-1]
    # Генерируем уникальное имя файла с timestamp и uuid
    filename = f"{timezone.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex}.{ext}"
    return os.path.join("screenshots", filename)


class Ticket(models.Model):
    STATUS_CHOICES = [
        ("open", "Открыт"),
        ("in_progress", "В работе"),
        ("resolved", "Решен"),
        ("closed", "Закрыт"),
    ]

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    subject = models.CharField(max_length=200, verbose_name="Тема")
    description = models.TextField(verbose_name="Описание проблемы")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="open", verbose_name="Статус"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    admin_notes = models.TextField(blank=True, verbose_name="Заметки администратора")
    screenshot = models.ImageField(
        upload_to=get_screenshot_upload_path,
        blank=True,
        null=True,
        verbose_name="Скриншот",
    )
    has_unread_admin_response = models.BooleanField(
        default=False, verbose_name="Есть непросмотренный ответ администратора"
    )

    def __str__(self):
        return f"{self.subject} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Тикет"
        verbose_name_plural = "Тикеты"
        ordering = ["-created_at"]
