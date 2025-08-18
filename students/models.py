from django.utils import timezone
from django.db import models
from schedule.models import Schedule


class Student(models.Model):
    ATTENDANCE_TYPE_CHOICES = [
        ("camp", "Лагерь"),
        ("lab", "Лаборатория"),
        ("full_day", "Полный день"),
    ]

    full_name = models.CharField(max_length=255, verbose_name="ФИО")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    parent_name = models.CharField(
        max_length=255, blank=True, verbose_name="Имя родителя"
    )
    schedule = models.ForeignKey(
        Schedule, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Смена"
    )
    attendance_type = models.CharField(
        max_length=20, choices=ATTENDANCE_TYPE_CHOICES, verbose_name="Тип посещения"
    )
    attendance_dates = models.JSONField(
        default=list, blank=True, verbose_name="Даты посещений"
    )
    default_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=11400, verbose_name="Базовая цена"
    )
    individual_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Индивидуальная цена",
    )
    price_comment = models.CharField(
        max_length=255, blank=True, default="", verbose_name="Комментарий к цене"
    )

    def save(self, *args, **kwargs):
        if not self.default_price:
            if self.attendance_type in ["camp", "lab"]:
                self.default_price = 7000
            elif self.attendance_type == "full_day":
                self.default_price = 11400
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Ученик"
        verbose_name_plural = "Ученики"

    def __str__(self):
        return self.full_name


class Payment(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="payments"
    )
    schedule = models.ForeignKey(
        Schedule, on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    date = models.DateField(default=timezone.now, verbose_name="Дата оплаты")
    comment = models.CharField(max_length=255, blank=True, null=True, verbose_name="Комментарий")

    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"

    def __str__(self):
        return f"{self.student} - {self.amount} руб."


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    present = models.BooleanField(default=False, verbose_name="Присутствовал")
    excused = models.BooleanField(default=False, verbose_name="По уважительной причине")

    class Meta:
        unique_together = ("student", "date")
        verbose_name = "Посещение"
        verbose_name_plural = "Посещения"

    def __str__(self):
        if self.present:    
            status = "Присутствовал"
        elif self.excused:
            status = "По уважительной причине"
        else:
            status = "Отсутствовал"
        return f"{self.student} - {self.date} - {status}"