from django.db import models
from schedule.models import Schedule

class Student(models.Model):
    ATTENDANCE_TYPE_CHOICES = [
        ('camp', 'Лагерь'),
        ('lab', 'Лаборатория'),
        ('full_day', 'Полный день'),
    ]

    full_name = models.CharField(max_length=255, verbose_name="ФИО")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    parent_name = models.CharField(max_length=255, blank=True, verbose_name="Имя родителя")
    schedule = models.ForeignKey(Schedule, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Смена")
    attendance_type = models.CharField(max_length=20, choices=ATTENDANCE_TYPE_CHOICES, verbose_name="Тип посещения")
    default_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Цена по умолчанию")
    individual_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Индивидуальная цена")
    price_comment = models.CharField(max_length=255, blank=True, verbose_name="Комментарий к цене")

    class Meta:
        verbose_name = "Ученик"
        verbose_name_plural = "Ученики"

    def __str__(self):
        return self.full_name


