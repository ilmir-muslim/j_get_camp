from datetime import timedelta
from django.db import models
from employees.models import Employee
from schedule.models import Schedule

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('food', 'Питание'),
        ('materials', 'Материалы'),
        ('transport', 'Транспорт'),
        ('rent', 'Аренда'),
        ('other', 'Прочее'),
    ]

    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='expenses')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    comment = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.get_category_display()} — {self.amount} руб."


class Salary(models.Model):
    """
    Зарплата сотрудника за смену с учётом типа выплаты.
    """

    PAYMENT_TYPE_CHOICES = [
        ("fixed", "Фиксированная ставка"),
        ("percent", "Процент от оплаты"),
        ("combined", "Фикс + процент"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="salaries",
        verbose_name="Сотрудник",
    )
    schedule = models.ForeignKey(
        Schedule, on_delete=models.CASCADE, verbose_name="Смена"
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        default="fixed",
        verbose_name="Тип выплаты",
    )
    # остальные поля без изменений
    daily_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Ставка за день",
        editable=False, 
    )
    percent_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, verbose_name="Процент от оплаты"
    )
    total_payment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Итоговая сумма выплаты",
    )
    is_paid = models.BooleanField(default=False, verbose_name="Выплачено")


    def calculate_days_worked(self):
        """
        Расчёт количества отработанных дней на основе посещаемости.
        """
        from employees.models import EmployeeAttendance

        # Получаем все даты смены
        dates = [
            self.schedule.start_date + timedelta(days=i)
            for i in range((self.schedule.end_date - self.schedule.start_date).days + 1)
        ]

        # Считаем количество дней с отметкой "присутствовал"
        return EmployeeAttendance.objects.filter(
            employee=self.employee, date__in=dates, present=True
        ).count()

    def calculate_total_payment(self):
        """
        Расчёт итоговой суммы выплаты в зависимости от типа выплаты.
        """
        days_worked = self.calculate_days_worked()

        if self.payment_type == "fixed":
            self.total_payment = days_worked * self.daily_rate
        elif self.payment_type == "percent":
            self.total_payment = (
                self.percent_rate
            )  # Подразумевается ручной ввод суммы с учётом процента
        elif self.payment_type == "combined":
            self.total_payment = (days_worked * self.daily_rate) + self.percent_rate
        return self.total_payment

    def save(self, *args, **kwargs):
        if not self.daily_rate or self.daily_rate == 0:
            self.daily_rate = self.employee.rate_per_day
        super().save(*args, **kwargs)

    @property
    def days_worked(self):
        """
        Свойство для получения количества отработанных дней.
        """
        return self.calculate_days_worked()

    class Meta:
        verbose_name = "Зарплата сотрудника"
        verbose_name_plural = "Зарплаты сотрудников"

    def __str__(self):
        return f"{self.employee.full_name} — {self.total_payment} руб."