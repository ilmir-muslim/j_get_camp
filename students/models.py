from django.utils import timezone
from django.db.models import Sum
from django.db import models
from jget_crm import settings
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

    @property
    def current_balance(self):
        deposits = (
            self.balance_operations.filter(operation_type="deposit").aggregate(
                Sum("amount")
            )["amount__sum"]
            or 0
        )
        payments = (
            self.balance_operations.filter(operation_type="payment").aggregate(
                Sum("amount")
            )["amount__sum"]
            or 0
        )
        corrections = (
            self.balance_operations.filter(operation_type="correction").aggregate(
                Sum("amount")
            )["amount__sum"]
            or 0
        )
        return deposits - payments + corrections

    class Meta:
        verbose_name = "Ученик"
        verbose_name_plural = "Ученики"

    def __str__(self):
        return self.full_name


    def get_total_paid_for_schedule(self, schedule):
        total = self.payments.filter(schedule=schedule).aggregate(Sum("amount"))[
            "amount__sum"
        ]
        return total or 0

    def can_make_payment(self, amount):
        return self.current_balance >= amount


class Payment(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="payments"
    )
    schedule = models.ForeignKey(
        Schedule, on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    date = models.DateField(default=timezone.now, verbose_name="Дата оплаты")
    comment = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Комментарий"
    )

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


class Balance(models.Model):
    OPERATION_TYPES = [
        ("deposit", "Пополнение"),
        ("payment", "Списание"),
        ("refund", "Возврат"),
    ]

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="balance_operations"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    operation_type = models.CharField(
        max_length=20, choices=OPERATION_TYPES, verbose_name="Тип операции"
    )
    date = models.DateTimeField(default=timezone.now, verbose_name="Дата операции")
    comment = models.CharField(max_length=255, blank=True, verbose_name="Комментарий")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Кем создано",
    )

    class Meta:
        verbose_name = "Операция по балансу"
        verbose_name_plural = "Операции по балансу"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.student} - {self.amount} ({self.get_operation_type_display()})"
