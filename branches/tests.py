from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from branches.models import Branch
import json

class BranchApiTests(TestCase):
    """
    Набор тестов для проверки API филиалов.
    """

    def setUp(self):
        """
        Подготовка данных перед каждым тестом.
        """
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="manager",
            password="password",
            role="manager"
        )
        self.client.force_login(self.user)
        self.branch = Branch.objects.create(
            name="Test Branch",
            address="Test Address"
        )

    def test_branch_list(self):
        """
        Проверка получения списка филиалов.
        """
        response = self.client.get("/api/branches/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Branch", response.content.decode("utf-8"))

    def test_branch_detail(self):
        """
        Проверка получения информации о конкретном филиале.
        """
        response = self.client.get(f"/api/branches/{self.branch.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Branch", response.content.decode("utf-8"))

    def test_create_branch(self):
        """
        Проверка создания нового филиала через API.
        """
        data = {"name": "New Branch", "address": "New Address"}
        response = self.client.post(
            "/api/branches/",
            data=json.dumps(data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Branch.objects.count(), 2)

    def test_delete_branch(self):
        """
        Проверка удаления филиала через API.
        """
        response = self.client.delete(f"/api/branches/{self.branch.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Branch.objects.count(), 0)
