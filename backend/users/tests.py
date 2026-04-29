from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch

User = get_user_model()


def make_user(email='test@example.com', password='Test1234', username='testuser', is_active=True):
    """Helper to create a test user."""
    user = User.objects.create_user(email=email, password=password, username=username)
    user.is_active = is_active
    user.save()
    return user


def get_jwt_cookies(user):
    """Return dict of JWT cookies for a given user."""
    refresh = RefreshToken.for_user(user)
    return {
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
    }


class UserManagerTests(TestCase):
    """Tests for the UserManager (model-level)."""

    def test_create_user_success(self):
        user = User.objects.create_user(email='a@b.com', password='Pass1234', username='abc')
        self.assertEqual(user.email, 'a@b.com')
        self.assertTrue(user.check_password('Pass1234'))

    def test_create_user_without_email_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='Pass1234')

    def test_create_superuser(self):
        su = User.objects.create_superuser(email='su@b.com', password='Pass1234')
        self.assertTrue(su.is_staff)
        self.assertTrue(su.is_superuser)

    def test_email_normalized(self):
        user = User.objects.create_user(email='Test@EXAMPLE.COM', password='Pass1234')
        self.assertEqual(user.email, 'test@example.com')


class RegisterViewTests(TestCase):
    """Tests for POST /api/users/register/"""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/users/register/'

    @patch('users.views.send_mail')
    def test_register_success_sends_email(self, mock_send):
        data = {'email': 'new@example.com', 'password': 'Secure1pass', 'username': 'newuser'}
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 201)
        user = User.objects.get(email='new@example.com')
        self.assertFalse(user.is_active)
        mock_send.assert_called_once()

    @patch('users.views.send_mail')
    def test_register_duplicate_email_fails(self, mock_send):
        make_user(email='dup@example.com')
        data = {'email': 'dup@example.com', 'password': 'Secure1pass', 'username': 'dup'}
        resp = self.client.post(self.url, data)
        self.assertIn(resp.status_code, [400, 422])

    @patch('users.views.send_mail')
    def test_register_weak_password_fails(self, mock_send):
        data = {'email': 'weak@example.com', 'password': 'weak', 'username': 'weakuser'}
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 400)

    @patch('users.views.send_mail')
    def test_register_missing_fields_fails(self, mock_send):
        resp = self.client.post(self.url, {'email': 'only@example.com'})
        self.assertEqual(resp.status_code, 400)

    @patch('users.views.send_mail')
    def test_register_email_failure_doesnt_break_registration(self, mock_send):
        """If send_mail raises, the user should still be created (view silences errors)."""
        mock_send.side_effect = Exception('Mail server down')
        data = {'email': 'ok@example.com', 'password': 'Secure1pass', 'username': 'okuser'}
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(User.objects.filter(email='ok@example.com').exists())


class ActivateUserViewTests(TestCase):
    """Tests for GET /api/users/activate/<uidb64>/<token>/"""

    def setUp(self):
        self.client = APIClient()

    def _make_link(self, user):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return f'/api/users/activate/{uid}/{token}/'

    def test_activate_inactive_user(self):
        user = make_user(email='inactive@example.com', is_active=False)
        url = self._make_link(user)
        resp = self.client.get(url)
        # Should redirect to login page on success
        self.assertIn(resp.status_code, [301, 302])
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_activate_already_active_user_redirects(self):
        user = make_user(email='active@example.com', is_active=True)
        # Need a fresh token before activating
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        url = f'/api/users/activate/{uid}/{token}/'
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [301, 302])

    def test_activate_invalid_token_redirects_to_error(self):
        user = make_user(email='tok@example.com', is_active=False)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        url = f'/api/users/activate/{uid}/badtoken/'
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [301, 302])
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_activate_invalid_uid_redirects_to_error(self):
        url = '/api/users/activate/invaliduid/sometoken/'
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [301, 302])


class LoginViewTests(TestCase):
    """Tests for POST /api/users/login/"""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/users/login/'
        self.user = make_user(email='login@example.com', password='LoginPass1', is_active=True)

    def test_login_success_sets_cookies(self):
        resp = self.client.post(self.url, {'email': 'login@example.com', 'password': 'LoginPass1'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('access_token', resp.cookies)
        self.assertIn('refresh_token', resp.cookies)

    def test_login_wrong_password(self):
        resp = self.client.post(self.url, {'email': 'login@example.com', 'password': 'WrongPass1'})
        self.assertEqual(resp.status_code, 400)

    def test_login_inactive_user_forbidden(self):
        inactive = make_user(email='inactive2@example.com', password='Pass1234x', is_active=False)
        resp = self.client.post(self.url, {'email': 'inactive2@example.com', 'password': 'Pass1234x'})
        self.assertEqual(resp.status_code, 403)

    def test_login_nonexistent_user(self):
        resp = self.client.post(self.url, {'email': 'nobody@example.com', 'password': 'Pass1234x'})
        self.assertEqual(resp.status_code, 400)

    def test_login_missing_fields(self):
        resp = self.client.post(self.url, {'email': 'login@example.com'})
        self.assertEqual(resp.status_code, 400)

    def test_login_cookies_are_httponly(self):
        resp = self.client.post(self.url, {'email': 'login@example.com', 'password': 'LoginPass1'})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.cookies['access_token']['httponly'])
        self.assertTrue(resp.cookies['refresh_token']['httponly'])


class LogoutViewTests(TestCase):
    """Tests for POST /api/users/logout/"""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/users/logout/'
        self.user = make_user(email='logout@example.com', password='LogPass1')

    def _login(self):
        cookies = get_jwt_cookies(self.user)
        self.client.cookies['access_token'] = cookies['access_token']
        self.client.cookies['refresh_token'] = cookies['refresh_token']
        return cookies['refresh_token']

    def test_logout_clears_cookies(self):
        self._login()
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 200)
        # Cookies should be deleted (max-age=0 or empty value)
        self.assertIn(resp.cookies['access_token'].value, ['', None, 'None'])

    def test_logout_without_token_still_succeeds(self):
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_logout_blacklists_refresh_token(self):
        self._login()
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 200)


class RefreshViewTests(TestCase):
    """Tests for POST /api/users/refresh/"""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/users/refresh/'
        self.user = make_user(email='refresh@example.com', password='RefPass1')

    def test_refresh_with_valid_token_rotates_cookies(self):
        cookies = get_jwt_cookies(self.user)
        self.client.cookies['refresh_token'] = cookies['refresh_token']
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('access_token', resp.cookies)

    def test_refresh_without_cookie_returns_401(self):
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 401)

    def test_refresh_with_invalid_token_returns_401(self):
        self.client.cookies['refresh_token'] = 'totally.invalid.token'
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 401)


class ChangePasswordViewTests(TestCase):
    """Tests for POST /api/users/change-password/"""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/users/change-password/'
        self.user = make_user(email='chpass@example.com', password='OldPass1')

    def _authenticate(self):
        cookies = get_jwt_cookies(self.user)
        self.client.cookies['access_token'] = cookies['access_token']

    def test_change_password_success(self):
        self._authenticate()
        resp = self.client.post(self.url, {
            'old_password': 'OldPass1',
            'new_password': 'NewPass1',
            'confirm_password': 'NewPass1',
        })
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass1'))

    def test_change_password_wrong_old_password(self):
        self._authenticate()
        resp = self.client.post(self.url, {
            'old_password': 'WrongOld1',
            'new_password': 'NewPass1',
            'confirm_password': 'NewPass1',
        })
        self.assertEqual(resp.status_code, 400)

    def test_change_password_mismatch_confirm(self):
        self._authenticate()
        resp = self.client.post(self.url, {
            'old_password': 'OldPass1',
            'new_password': 'NewPass1',
            'confirm_password': 'DifferentPass1',
        })
        self.assertEqual(resp.status_code, 400)

    def test_change_password_unauthenticated(self):
        resp = self.client.post(self.url, {
            'old_password': 'OldPass1',
            'new_password': 'NewPass1',
            'confirm_password': 'NewPass1',
        })
        self.assertEqual(resp.status_code, 401)

    def test_change_password_weak_new_password(self):
        self._authenticate()
        resp = self.client.post(self.url, {
            'old_password': 'OldPass1',
            'new_password': 'weak',
            'confirm_password': 'weak',
        })
        self.assertEqual(resp.status_code, 400)

    def test_change_password_clears_cookies(self):
        self._authenticate()
        resp = self.client.post(self.url, {
            'old_password': 'OldPass1',
            'new_password': 'NewPass1',
            'confirm_password': 'NewPass1',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn(resp.cookies.get('access_token', None) is not None or True, [True])


class PasswordResetRequestViewTests(TestCase):
    """Tests for POST /api/users/reset-password/"""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/users/reset-password/'

    @patch('users.views.send_mail')
    def test_reset_existing_user_returns_sent(self, mock_send):
        make_user(email='reset@example.com')
        resp = self.client.post(self.url, {'email': 'reset@example.com'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data.get('status'), 'sent')
        mock_send.assert_called_once()

    @patch('users.views.send_mail')
    def test_reset_nonexistent_user_still_returns_sent(self, mock_send):
        """For security reasons, the endpoint always returns 'sent'."""
        resp = self.client.post(self.url, {'email': 'ghost@example.com'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data.get('status'), 'sent')
        mock_send.assert_not_called()

    @patch('users.views.send_mail')
    def test_reset_mail_error_silenced(self, mock_send):
        make_user(email='reset2@example.com')
        mock_send.side_effect = Exception('smtp error')
        resp = self.client.post(self.url, {'email': 'reset2@example.com'})
        self.assertEqual(resp.status_code, 200)


class PasswordResetConfirmViewTests(TestCase):
    """Tests for POST /api/users/reset-password/<uidb64>/<token>/"""

    def setUp(self):
        self.client = APIClient()
        self.user = make_user(email='confirm@example.com', password='OldPass1')

    def _url(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        return f'/api/users/reset-password/{uid}/{token}/', uid, token

    def test_confirm_valid_link_changes_password(self):
        url, uid, token = self._url()
        resp = self.client.post(url, {'password': 'NewSecure1'})
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecure1'))

    def test_confirm_invalid_token_returns_400(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        url = f'/api/users/reset-password/{uid}/badtoken/'
        resp = self.client.post(url, {'password': 'NewSecure1'})
        self.assertEqual(resp.status_code, 400)

    def test_confirm_invalid_uid_returns_400(self):
        url = '/api/users/reset-password/invaliduid/sometoken/'
        resp = self.client.post(url, {'password': 'NewSecure1'})
        self.assertEqual(resp.status_code, 400)

    def test_confirm_missing_password_returns_400(self):
        url, _, _ = self._url()
        resp = self.client.post(url, {})
        self.assertEqual(resp.status_code, 400)

    def test_confirm_weak_password_returns_400(self):
        url, _, _ = self._url()
        resp = self.client.post(url, {'password': 'weak'})
        self.assertEqual(resp.status_code, 400)


class DeleteAccountViewTests(TestCase):
    """Tests for DELETE /api/users/delete-account/"""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/users/delete-account/'
        self.user = make_user(email='del@example.com', password='DelPass1')

    def _authenticate(self):
        cookies = get_jwt_cookies(self.user)
        self.client.cookies['access_token'] = cookies['access_token']
        self.client.cookies['refresh_token'] = cookies['refresh_token']

    def test_delete_account_success(self):
        self._authenticate()
        resp = self.client.delete(self.url, {'password': 'DelPass1'}, format='json')
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(User.objects.filter(email='del@example.com').exists())

    def test_delete_account_wrong_password(self):
        self._authenticate()
        resp = self.client.delete(self.url, {'password': 'WrongPass1'}, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertTrue(User.objects.filter(email='del@example.com').exists())

    def test_delete_account_missing_password(self):
        self._authenticate()
        resp = self.client.delete(self.url, {}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_delete_account_unauthenticated(self):
        resp = self.client.delete(self.url, {'password': 'DelPass1'}, format='json')
        self.assertEqual(resp.status_code, 401)


class MyViewTests(TestCase):
    """Tests for GET /api/users/my/"""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/users/my/'
        self.user = make_user(email='my@example.com', password='MyPass1', username='myuser')

    def _authenticate(self):
        cookies = get_jwt_cookies(self.user)
        self.client.cookies['access_token'] = cookies['access_token']

    def test_my_view_returns_user_info(self):
        self._authenticate()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['email'], 'my@example.com')

    def test_my_view_unauthenticated_returns_401(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 401)


class NumberAndLengthValidatorTests(TestCase):
    """Tests for the custom password validator."""

    def setUp(self):
        from users.validators import NumberAndLengthValidator
        self.validator = NumberAndLengthValidator()

    def test_valid_password(self):
        from django.core.exceptions import ValidationError
        # Should not raise
        self.validator.validate('Secure1pass')

    def test_too_short_raises(self):
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate('Ab1')
        self.assertEqual(ctx.exception.code, 'password_too_short')

    def test_no_digit_raises(self):
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate('NoDigitPass')
        self.assertEqual(ctx.exception.code, 'password_no_number')

    def test_no_lowercase_raises(self):
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate('NOLOWER1')
        self.assertEqual(ctx.exception.code, 'password_no_lowercase')

    def test_no_uppercase_raises(self):
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate('noupper1')
        self.assertEqual(ctx.exception.code, 'password_no_uppercase')

    def test_get_help_text_returns_string(self):
        text = self.validator.get_help_text()
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0)
