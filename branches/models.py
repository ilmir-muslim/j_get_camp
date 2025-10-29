from django.db import models


class City(models.Model):
    name = models.CharField(max_length=255, verbose_name="Город")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"


class Branch(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    address = models.TextField(blank=True, verbose_name="Адрес")
    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        verbose_name="Город",
        related_name="branches",
        null=True,
        blank=True,
    )

    def __str__(self):
        if self.city:
            return f"{self.name} ({self.city.name})"
        return self.name

    def get_statistics(self):
        """Получить статистику по филиалу"""
        from schedule.models import Schedule
        from employees.models import Employee
        from students.models import Student
        from payroll.models import Expense, Salary
        from django.db.models import Q, Sum

        return {
            "schedule_count": Schedule.objects.filter(branch=self).count(),
            "employee_count": Employee.objects.filter(branch=self).count(),
            "student_count": Student.objects.filter(branch=self).count(),
            "total_expenses": Expense.objects.filter(
                Q(schedule__branch=self) | Q(employee__branch=self)
            ).aggregate(Sum("amount"))["amount__sum"]
            or 0,
            "total_salaries": Salary.objects.filter(employee__branch=self).aggregate(
                Sum("total_payment")
            )["total_payment__sum"]
            or 0,
        }

    class Meta:
        verbose_name = "Филиал"
        verbose_name_plural = "Филиалы"
