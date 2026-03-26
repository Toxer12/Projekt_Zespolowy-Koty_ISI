from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from django.core import mail
from rest_framework.test import APIClient
from web_app.views import reset_tokens


# [BE][6] User login 
class UserLoginTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="loginuser",
            email="login@test.com",
            password="MyPass123",
            is_active=True,
        )

    def test_login_valid_credentials(self):
        resp = self.client.post(
            "/api/token/", {"username": "loginuser", "password": "MyPass123"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_login_wrong_password(self):
        resp = self.client.post(
            "/api/token/", {"username": "loginuser", "password": "WrongPass"}
        )
        self.assertEqual(resp.status_code, 401)

    def test_login_nonexistent_user(self):
        resp = self.client.post(
            "/api/token/", {"username": "ghost", "password": "MyPass123"}
        )
        self.assertEqual(resp.status_code, 401)

    def test_login_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        resp = self.client.post(
            "/api/token/", {"username": "loginuser", "password": "MyPass123"}
        )
        self.assertEqual(resp.status_code, 401)


# [BE][7] Password hashing
class PasswordHashingTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.client.post(
            "/api/register/",
            {"username": "testuser", "email": "test@test.com", "password": "MyPass123"},
        )
        self.user = User.objects.get(username="testuser")

    def test_password_is_hashed(self):
        self.assertNotEqual(self.user.password, "MyPass123")

    def test_password_hash_is_valid(self):
        self.assertTrue(check_password("MyPass123", self.user.password))

    def test_password_not_in_response(self):
        resp = self.client.post(
            "/api/register/",
            {"username": "user2", "email": "u2@t.com", "password": "SecurePass123"},
        )
        self.assertNotIn("password", resp.data)


# [BE][8] Email activation
class EmailActivationTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.client.post(
            "/api/register/",
            {"username": "newuser", "email": "new@test.com", "password": "MyPass123"},
        )
        self.user = User.objects.get(username="newuser")
        body = mail.outbox[0].body
        self.activation_token = body.split("/api/activate/")[1].rstrip("/")

    def test_new_user_is_inactive(self):
        self.assertFalse(self.user.is_active)

    def test_activation_email_sent(self):
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("activate", mail.outbox[0].body)

    def test_activate_makes_user_active(self):
        self.client.get(f"/api/activate/{self.activation_token}/")
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_invalid_token_returns_400(self):
        resp = self.client.get("/api/activate/bad-token/")
        self.assertEqual(resp.status_code, 400)

    def test_active_user_can_login(self):
        self.client.get(f"/api/activate/{self.activation_token}/")
        resp = self.client.post(
            "/api/token/", {"username": "newuser", "password": "MyPass123"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.data)


# [BE][9] Password recovery
class PasswordRecoveryTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="recuser",
            email="rec@test.com",
            password="OldPassword",
            is_active=True,
        )
        reset_tokens.clear()

    def test_reset_sends_email(self):
        self.client.post("/api/reset/", {"email": "rec@test.com"})
        self.assertEqual(len(mail.outbox), 1)

    def test_reset_nonexistent_email_no_mail(self):
        self.client.post("/api/reset/", {"email": "none@test.com"})
        self.assertEqual(len(mail.outbox), 0)

    def test_reset_changes_password(self):
        self.client.post("/api/reset/", {"email": "rec@test.com"})
        token = mail.outbox[0].body.split("/reset-password-confirm/")[1].rstrip("/")

        self.client.post(f"/api/reset/{token}/", {"password": "NewPassword"})
        self.user.refresh_from_db()
        self.assertTrue(check_password("NewPassword", self.user.password))

    def test_invalid_reset_token(self):
        resp = self.client.post("/api/reset/bad-token/", {"password": "X"})
        self.assertEqual(resp.status_code, 400)


# [BE][10] Password change
class ChangePasswordTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="chpwuser",
            email="chpw@test.com",
            password="OldPass123",
            is_active=True,
        )
        resp = self.client.post(
            "/api/token/", {"username": "chpwuser", "password": "OldPass123"}
        )
        self.access_token = resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)

    def test_change_password_success(self):
        resp = self.client.post(
            "/api/change-password/",
            {"old_password": "OldPass123", "new_password": "NewSecure456"},
        )
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(check_password("NewSecure456", self.user.password))

    def test_change_password_wrong_old(self):
        resp = self.client.post(
            "/api/change-password/",
            {"old_password": "WrongOldPass", "new_password": "NewSecure456"},
        )
        self.assertEqual(resp.status_code, 400)

    def test_change_password_unauthenticated(self):
        self.client.credentials()  
        resp = self.client.post(
            "/api/change-password/",
            {"old_password": "OldPass123", "new_password": "NewSecure456"},
        )
        self.assertEqual(resp.status_code, 401)

    
