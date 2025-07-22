from django.db import models
from branches.models import Branch


COLOR_CHOICES = [
    ("#ff6b6b", "Красный"),
    ("#51cf66", "Зеленый"),
    ("#339af0", "Синий"),
    ("#ffd43b", "Желтый"),
    ("#cc5de8", "Фиолетовый"),
    ("#ff922b", "Оранжевый"),
    ("#20c997", "Бирюзовый"),
]


class Schedule(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название смены")
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="schedule", verbose_name="Филиал"
    )
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания")
    theme = models.CharField(max_length=255, verbose_name="Тематика смены")

    color = models.CharField(
        max_length=7,
        choices=COLOR_CHOICES,
        default="#cce6ff",
        verbose_name="Цвет маркировки",
    )

    def __str__(self):
        return f"{self.name} ({self.start_date} — {self.end_date})"

    class Meta:
        verbose_name = "Смена"
        verbose_name_plural = "Смены"
