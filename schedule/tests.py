from django.test import TestCase, Client
from schedule.models import Schedule
from branches.models import Branch
from django.contrib.auth import get_user_model
import json


class ScheduleApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="manager", password="password", role="manager"
        )
        self.client.force_login(self.user)

        self.branch = Branch.objects.create(name="Test Branch")
        self.schedule = Schedule.objects.create(
            name="Test Schedule",
            branch=self.branch,
            start_date="2025-07-01",
            end_date="2025-07-15",
            theme="Robotics",
        )

    def test_schedule_list(self):
        response = self.client.get("/api/schedules/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Schedule", str(response.content))

    def test_schedule_detail(self):
        response = self.client.get(f"/api/schedules/{self.schedule.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Robotics")

    def test_create_schedule(self):
        data = {
            "name": "New Schedule",
            "branch_id": self.branch.id,
            "start_date": "2025-08-01",
            "end_date": "2025-08-15",
            "theme": "Programming",
        }

        response = self.client.post(
            "/api/schedules/", data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Schedule.objects.count(), 2)

    def test_delete_schedule(self):
        response = self.client.delete(f"/api/schedules/{self.schedule.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Schedule.objects.count(), 0)
