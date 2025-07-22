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
        ('fixed', 'Фиксированная ставка'),
        ('percent', 'Процент от оплаты'),
        ('combined', 'Фикс + процент'),
    ]

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='salaries',
        verbose_name="Сотрудник"
    )
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, verbose_name="Смена")
    payment_type = models.CharField(
        max_length=20, choices=PAYMENT_TYPE_CHOICES, default='fixed', verbose_name="Тип выплаты"
    )
    days_worked = models.IntegerField(default=0, verbose_name="Количество отработанных дней")
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Ставка за день")
    percent_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Процент от оплаты")
    total_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Итоговая сумма выплаты")
    is_paid = models.BooleanField(default=False, verbose_name="Выплачено")

    class Meta:
        verbose_name = "Зарплата сотрудника"
        verbose_name_plural = "Зарплаты сотрудников"

    def __str__(self):
        return f"{self.employee.full_name} — {self.total_payment} руб."

    def calculate_total_payment(self):
        """
        Расчёт итоговой суммы выплаты в зависимости от типа выплаты.
        """
        if self.payment_type == 'fixed':
            self.total_payment = self.days_worked * self.daily_rate
        elif self.payment_type == 'percent':
            self.total_payment = self.percent_rate  # Подразумевается ручной ввод суммы с учётом процента
        elif self.payment_type == 'combined':
            self.total_payment = (self.days_worked * self.daily_rate) + self.percent_rate
        return self.total_payment

