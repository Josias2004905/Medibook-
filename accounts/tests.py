from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegistrationTest(TestCase):
    def test_register_page_status(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)

    def test_user_registration_creates_patient_profile(self):
        data = {
            "username": "testpatient",
            "first_name": "Test",
            "last_name": "Patient",
            "email": "test@example.com",
            "phone": "123456789",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="testpatient")
        self.assertEqual(user.role, "patient")
        self.assertTrue(hasattr(user, "patient_profile"))

    def test_registration_with_mismatched_passwords(self):
        data = {
            "username": "badpass",
            "first_name": "Bad",
            "last_name": "Pass",
            "email": "bad@example.com",
            "password1": "StrongPass123!",
            "password2": "DifferentPass123!",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="badpass").exists())


class LoginLogoutTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="TestPass123!",
            role="patient",
            first_name="Test",
            last_name="User",
        )

    def test_login_page_status(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

    def test_login_with_valid_credentials(self):
        response = self.client.post(
            reverse("login"), {"username": "testuser", "password": "TestPass123!"}
        )
        self.assertEqual(response.status_code, 302)

    def test_login_with_invalid_credentials(self):
        response = self.client.post(
            reverse("login"), {"username": "testuser", "password": "wrongpass"}
        )
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)


class RoleAssignmentTest(TestCase):
    def test_patient_role_on_registration(self):
        User.objects.create_user(
            username="rolepatient",
            password="TestPass123!",
            role="patient",
        )
        user = User.objects.get(username="rolepatient")
        self.assertEqual(user.role, "patient")
        self.assertTrue(user.is_patient)
        self.assertFalse(user.is_doctor)

    def test_doctor_role(self):
        User.objects.create_user(
            username="roledoctor",
            password="TestPass123!",
            role="doctor",
        )
        user = User.objects.get(username="roledoctor")
        self.assertEqual(user.role, "doctor")
        self.assertTrue(user.is_doctor)
        self.assertFalse(user.is_patient)

    def test_admin_role(self):
        User.objects.create_superuser(
            username="roleadmin",
            email="admin@test.com",
            password="TestPass123!",
        )
        user = User.objects.get(username="roleadmin")
        self.assertTrue(user.is_admin_user)
