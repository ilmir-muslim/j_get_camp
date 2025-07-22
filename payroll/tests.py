from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from payroll.models import Expense, Salary
from schedule.models import Schedule
from branches.models import Branch
from employees.models import Employee
import json
from datetime import date


class PayrollApiTests(TestCase):
    """
    Набор тестов для проверки API расходов и расчёта зарплаты.
    """

    def setUp(self):
        """
        Подготовка тестового пользователя, филиала, расписания, сотрудника и одного расхода для проверки.
        """
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="manager", password="password", role="manager"
        )
        self.client.force_login(self.user)

        self.branch = Branch.objects.create(name="Test Branch")

        self.schedule = Schedule.objects.create(
            name="Тестовая смена",
            branch=self.branch,
            start_date=date(2025, 7, 1),
            end_date=date(2025, 7, 15),
            theme="Робототехника",
        )

        self.employee = Employee.objects.create(
            full_name="Тестовый Сотрудник",
            position="teacher",
            branch=self.branch,
            schedule=self.schedule,
            rate_per_day=3000,
        )

        self.expense = Expense.objects.create(
            schedule=self.schedule, category="materials", amount=1000, comment=""
        )

    def test_expense_list(self):
        """
        Проверка получения списка расходов.
        """
        response = self.client.get("/api/payroll/expenses/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("materials", response.content.decode("utf-8"))

    def test_create_expense(self):
        """
        Проверка создания нового расхода.
        """
        data = {
            "schedule_id": self.schedule.id,
            "category": "materials",
            "amount": 5000,
            "comment": "",
        }
        response = self.client.post(
            "/api/payroll/expenses/",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Expense.objects.count(), 2)

    def test_salary_calculation(self):
        """
        Проверка расчета зарплаты.
        """
        data = {
            "schedule_id": self.schedule.id,
            "employee_id": self.employee.id,
            "payment_type": "fixed",
            "days_worked": 5,
            "daily_rate": 3000,
            "percent_rate": 0,
            "is_paid": False,
        }
        response = self.client.post(
            "/api/payroll/salaries/",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Salary.objects.count(), 1)
        salary = Salary.objects.first()
        self.assertEqual(salary.total_payment, 15000)
