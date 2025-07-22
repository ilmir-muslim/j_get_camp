from django.test import TestCase, Client
from django.contrib.auth import get_user_model
import json


class AuthApiTests(TestCase):
    """
    Набор тестов для проверки авторизации через API.
    """

    def setUp(self):
        """
        Создание тестового пользователя.
        """
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="testpass",
            role="manager"
        )

    def test_login_success(self):
        """
        Проверка успешной авторизации с правильными данными.
        """
        data = {"username": "testuser", "password": "testpass"}
        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps(data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get("success"))

    def test_login_failure(self):
        """
        Проверка отклонения авторизации с неправильными данными.
        """
        data = {"username": "testuser", "password": "wrongpass"}
        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps(data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json().get("success"))

    def test_logout(self):
        """
        Проверка выхода из системы.
        """
        self.client.login(username="testuser", password="testpass")
        response = self.client.post("/api/auth/logout/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get("success"))
