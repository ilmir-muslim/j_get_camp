from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('manager', 'Менеджер'),
        ('admin', 'Администратор'),
        ('camp_head', 'Начальник лагеря'),
        ('lab_head', 'Начальник лаборатории'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="Роль")
    branch = models.ForeignKey('branches.Branch', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Филиал")

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


