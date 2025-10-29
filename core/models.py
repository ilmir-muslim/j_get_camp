from django.contrib.auth.models import AbstractUser
from django.db import models

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

    def __str__(self):
        return f"{self.subject} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Тикет"
        verbose_name_plural = "Тикеты"
        ordering = ["-created_at"]
