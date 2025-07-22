from django.test import TestCase, Client
from education.models import Regulation
from django.contrib.auth import get_user_model

class EducationApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="manager",
            password="password",
            role="manager"
        )
        self.client.force_login(self.user)
        self.regulation = Regulation.objects.create(
            title="Test Regulation",
            file="regulations/test.pdf"
        )

    def test_regulation_list(self):
        response = self.client.get("/api/education/regulations/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Regulation", str(response.content))

    def test_regulation_detail(self):
        response = self.client.get(f"/api/education/regulations/{self.regulation.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Regulation")

    def test_delete_regulation(self):
        response = self.client.delete(f"/api/education/regulations/{self.regulation.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Regulation.objects.count(), 0)