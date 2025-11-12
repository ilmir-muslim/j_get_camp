# employees/models.py
from django.db import models
from branches.models import Branch, City
from schedule.models import Schedule


class Position(models.Model):
    """Модель для хранения должностей сотрудников"""

    name = models.CharField(max_length=100, verbose_name="Название должности")
    responsibilities = models.TextField(
        verbose_name="Должностные обязанности",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Должность"
        verbose_name_plural = "Должности"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Employee(models.Model):
    full_name = models.CharField(max_length=255, verbose_name="ФИО")

    position = models.ForeignKey(
        Position,
        on_delete=models.PROTECT,
        verbose_name="Должность",
        related_name="employees",
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
    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        verbose_name="Город",
        related_name="employees",
        null=True,
        blank=True,
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
    present = models.BooleanField(default=True, verbose_name="Присутствовал")
    excused = models.BooleanField(default=False, verbose_name="По уважительной причине")

    class Meta:
        unique_together = ("employee", "date")
        verbose_name = "Посещение"
        verbose_name_plural = "Посещения"

    def __str__(self):
        if self.present:
            status = "Присутствовал"
        elif self.excused:
            status = "По уважительной причине"
        else:
            status = "Отсутствовал"
        return f"{self.employee} - {self.date} - {status}"
