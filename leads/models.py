from django.db import models
from django.utils import timezone

class Lead(models.Model):
    STATUS_CHOICES = [
        ('approved', 'Одобрен'),
        ('rejected', 'Отклонён'),
        ('no_answer', 'Не взял трубку'),
        ('not_set', 'Не задан'),
    ]

    SOURCE_CHOICES = [
        ('instagram', 'Instagram'),
        ('telegram', 'Telegram'),
        ('vk', 'ВКонтакте'),
        ('website', 'Форма на сайте'),
        ('schedule', 'Смена'),
        ('camp', 'Лагерь'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_set', verbose_name="Статус")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, verbose_name="Источник")
    added_date = models.DateField(auto_now_add=True, verbose_name="Дата добавления")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    parent_name = models.CharField(max_length=255, blank=True, verbose_name="Имя родителя")
    interest = models.CharField(max_length=255, blank=True, verbose_name="Интерес")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    callback_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата и время перезвона")


    class Meta:
        verbose_name = "Лид"
        verbose_name_plural = "Лиды"

    def __str__(self):
        return f"{self.phone} ({self.get_status_display()})"

    @property
    def is_callback_overdue(self):
        if self.callback_date:
            return self.callback_date < timezone.now()
        return False

    @property
    def is_callback_today(self):
        if self.callback_date:
            return self.callback_date.date() == timezone.now().date()
        return False
