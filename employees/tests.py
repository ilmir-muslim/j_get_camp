from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from employees.models import Employee, EmployeeAttendance
from branches.models import Branch
from schedule.models import Schedule


class EmployeeApiTests(TestCase):
    """
    Набор тестов для проверки API сотрудников.
    """

    def setUp(self):
        """
        Создание пользователя, филиала, смены и сотрудника для тестов.
        """
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="manager", password="password", role="manager"
        )
        self.client.force_login(self.user)

        self.branch = Branch.objects.create(name="Тестовый филиал")
        self.schedule = Schedule.objects.create(
            name="Тестовая смена",
            branch=self.branch,
            start_date="2025-07-01",
            end_date="2025-07-15",
            theme="Робототехника"
        )

        self.employee = Employee.objects.create(
            full_name="Тестовый Сотрудник",
            position="teacher",
            branch=self.branch,
            schedule=self.schedule,
            rate_per_day=3000
        )

    def test_employee_list(self):
        """
        Проверка получения списка сотрудников.
        """
        response = self.client.get("/api/employees/")
        self.assertEqual(response.status_code, 200)

        import json
        data = json.loads(response.content)
        self.assertTrue(any(item["full_name"] == "Тестовый Сотрудник" for item in data))


    def test_employee_detail(self):
        """
        Проверка получения информации о конкретном сотруднике.
        """
        response = self.client.get(f"/api/employees/{self.employee.pk}/")
        self.assertEqual(response.status_code, 200)

        import json
        data = json.loads(response.content)
        self.assertEqual(data["full_name"], "Тестовый Сотрудник")


class EmployeeAttendanceApiTests(TestCase):
    """
    Набор тестов для проверки API посещаемости сотрудников.
    """

    def setUp(self):
        """
        Создание пользователя, филиала, смены, сотрудника и посещения для тестов.
        """
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="manager", password="password", role="manager"
        )
        self.client.force_login(self.user)

        self.branch = Branch.objects.create(name="Тестовый филиал")
        self.schedule = Schedule.objects.create(
            name="Тестовая смена",
            branch=self.branch,
            start_date="2025-07-01",
            end_date="2025-07-15",
            theme="Робототехника"
        )

        self.employee = Employee.objects.create(
            full_name="Тестовый Сотрудник",
            position="teacher",
            branch=self.branch,
            schedule=self.schedule,
            rate_per_day=3000
        )

        self.attendance = EmployeeAttendance.objects.create(
            employee=self.employee,
            date="2025-07-10",
            comment="Тестовый комментарий"
        )

    def test_attendance_update(self):
        """
        Тестирование обновления посещения сотрудника.
        """
        update_data = {
            "employee_id": self.employee.id,
            "date": "2025-07-15",
            "comment": "Обновленный комментарий"
        }

        response = self.client.put(
            f"/api/employees/attendances/{self.attendance.pk}/",
            data=update_data,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        updated_attendance = EmployeeAttendance.objects.get(id=self.attendance.id)
        self.assertEqual(str(updated_attendance.date), "2025-07-15")
        self.assertEqual(updated_attendance.comment, "Обновленный комментарий")
