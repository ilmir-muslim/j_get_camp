from django.db import models
from branches.models import Branch
from schedule.models import Schedule


class Employee(models.Model):
    POSITION_CHOICES = [
        ("teacher", "Преподаватель"),
        ("admin", "Администратор"),
        ("camp_head", "Начальник лагеря"),
        ("lab_head", "Начальник лаборатории"),
    ]

    full_name = models.CharField(max_length=255, verbose_name="ФИО")
    position = models.CharField(
        max_length=50, choices=POSITION_CHOICES, verbose_name="Должность"
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Филиал"
    )
    schedule = models.ForeignKey(
        Schedule, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Смена"
    )
    rate_per_day = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Ставка за день"
    )

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"

    def __str__(self):
        return self.full_name


class EmployeeAttendance(models.Model):
    """
    Учёт посещений сотрудников по датам с возможностью указать комментарий.
    """

    employee = models.ForeignKey(
        "Employee",
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name="Сотрудник",
    )
    date = models.DateField(verbose_name="Дата посещения")
    comment = models.CharField(max_length=255, blank=True, verbose_name="Комментарий")

    class Meta:
        verbose_name = "Посещение сотрудника"
        verbose_name_plural = "Посещения сотрудников"

    def __str__(self):
        return f"{self.employee.full_name} — {self.date}"
