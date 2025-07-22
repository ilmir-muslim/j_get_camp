from django.test import TestCase, Client
from leads.models import Lead
from django.contrib.auth import get_user_model
import json

class LeadApiTests(TestCase):
    """
    Набор тестов для проверки API лидов.
    """

    def setUp(self):
        """
        Подготовка тестовых данных и клиента.
        """
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="manager",
            password="password",
            role="manager"
        )
        self.client.force_login(self.user)
        self.lead = Lead.objects.create(
            status="approved",
            source="instagram",
            phone="79001112233",
            parent_name="Test Parent"
        )

    def test_lead_list(self):
        """
        Проверка получения списка лидов.
        """
        response = self.client.get("/api/leads/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Parent", response.content.decode("utf-8"))

    def test_lead_detail(self):
        """
        Проверка получения информации о конкретном лиде.
        """
        response = self.client.get(f"/api/leads/{self.lead.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Parent", response.content.decode("utf-8"))

    def test_create_lead(self):
        """
        Проверка создания нового лида через API.
        """
        data = {
            "status": "new",
            "source": "website",
            "phone": "79002223344",
            "parent_name": "New Parent"
        }
        response = self.client.post(
            "/api/leads/",
            data=json.dumps(data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lead.objects.count(), 2)

    def test_delete_lead(self):
        """
        Проверка удаления лида через API.
        """
        response = self.client.delete(f"/api/leads/{self.lead.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lead.objects.count(), 0)
