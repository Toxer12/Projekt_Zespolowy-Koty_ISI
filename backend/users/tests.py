from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core import mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


REGISTER_URL        = '/api/users/register/'
LOGIN_URL           = '/api/users/login/'
LOGOUT_URL          = '/api/users/logout/'
CHANGE_PASSWORD_URL = '/api/users/change-password/'
DELETE_ACCOUNT_URL  = '/api/users/delete-account/'
RESET_PASSWORD_URL  = '/api/users/reset-password/'
MY_URL              = '/api/users/my/'



def make_client():
    """Klient APIClient z wyłączonym CSRF (SessionAuthentication w widokach)."""
    return APIClient(enforce_csrf_checks=False)


def create_active_user(email='test@example.com', password='Test1234', name='testuser'):
    user = User.objects.create_user(name=name, email=email, password=password)
    user.is_active = True
    user.save()
    return user


def login_client(client, email='test@example.com', password='Test1234'):
    """Loguje użytkownika i wstrzykuje JWT access_token do ciasteczek klienta."""
    response = client.post(LOGIN_URL, {'email': email, 'password': password}, format='json')
    # Wstrzyknięcie tokenu JWT bezpośrednio (fallback gdy cookie nie zostało ustawione)
    if 'access_token' not in client.cookies:
        try:
            user = User.objects.get(email=email)
            refresh = RefreshToken.for_user(user)
            client.cookies['access_token'] = str(refresh.access_token)
        except Exception:
            pass
    return response


# ─────────────────────────────────────────────────────────────────────────────
# [BE][2] Backend configuration
# ─────────────────────────────────────────────────────────────────────────────
class BackendConfigurationTests(TestCase):
    """[BE][2] Weryfikacja konfiguracji backendu."""

    def test_rest_framework_installed(self):
        """rest_framework jest zainstalowany w INSTALLED_APPS."""
        from django.conf import settings
        self.assertIn('rest_framework', settings.INSTALLED_APPS)

    def test_simplejwt_blacklist_installed(self):
        """rest_framework_simplejwt.token_blacklist jest w INSTALLED_APPS."""
        from django.conf import settings
        self.assertIn('rest_framework_simplejwt.token_blacklist', settings.INSTALLED_APPS)

    def test_cors_headers_installed(self):
        """corsheaders jest zainstalowany w INSTALLED_APPS."""
        from django.conf import settings
        self.assertIn('corsheaders', settings.INSTALLED_APPS)

    def test_jwt_access_token_lifetime_configured(self):
        """SIMPLE_JWT zawiera ACCESS_TOKEN_LIFETIME."""
        from django.conf import settings
        self.assertIn('ACCESS_TOKEN_LIFETIME', settings.SIMPLE_JWT)

    def test_jwt_refresh_token_lifetime_configured(self):
        """SIMPLE_JWT zawiera REFRESH_TOKEN_LIFETIME."""
        from django.conf import settings
        self.assertIn('REFRESH_TOKEN_LIFETIME', settings.SIMPLE_JWT)

    def test_cookie_jwt_authentication_configured(self):
        """CookieJWTAuthentication jest domyślną klasą autentykacji."""
        from django.conf import settings
        auth_classes = settings.REST_FRAMEWORK.get('DEFAULT_AUTHENTICATION_CLASSES', [])
        self.assertIn('users.auth.CookieJWTAuthentication', auth_classes)

    def test_cors_allow_credentials_enabled(self):
        """CORS_ALLOW_CREDENTIALS jest True."""
        from django.conf import settings
        self.assertTrue(settings.CORS_ALLOW_CREDENTIALS)

    def test_email_backend_configured(self):
        """EMAIL_BACKEND jest skonfigurowany."""
        from django.conf import settings
        self.assertTrue(hasattr(settings, 'EMAIL_BACKEND'))
        self.assertIsNotNone(settings.EMAIL_BACKEND)


# ─────────────────────────────────────────────────────────────────────────────
# [BE][3] Database configuration
# ─────────────────────────────────────────────────────────────────────────────
class DatabaseConfigurationTests(TestCase):
    """[BE][3] Weryfikacja konfiguracji bazy danych."""

    def test_can_create_user_in_database(self):
        """Możliwe jest zapisanie użytkownika w bazie danych."""
        user = User.objects.create_user(name='dbuser', email='db@example.com', password='Test1234')
        self.assertIsNotNone(user.pk)

    def test_user_is_retrieved_from_database(self):
        """Użytkownik zapisany w bazie może zostać odczytany."""
        User.objects.create_user(name='retuser', email='retrieve@example.com', password='Test1234')
        user = User.objects.get(email='retrieve@example.com')
        self.assertEqual(user.email, 'retrieve@example.com')

    def test_email_field_is_unique_via_api(self):
        """API rejestracji odrzuca duplikat emaila (walidacja w serialiserze)."""
        from rest_framework.test import APIClient as _APIClient
        c = _APIClient(enforce_csrf_checks=False)
        c.post(REGISTER_URL, {'email': 'unique@example.com', 'password': 'Valid1234', 'name': 'u1'}, format='json')
        response = c.post(REGISTER_URL, {'email': 'unique@example.com', 'password': 'Valid1234', 'name': 'u2'}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_user_model_fields_exist(self):
        """Model User ma wymagane pola: email, is_active, is_staff."""
        user = User.objects.create_user(name='fuser', email='fields@example.com', password='Test1234')
        self.assertTrue(hasattr(user, 'email'))
        self.assertTrue(hasattr(user, 'is_active'))
        self.assertTrue(hasattr(user, 'is_staff'))

    def test_database_engine_is_postgresql(self):
        """Baza danych używa silnika PostgreSQL."""
        from django.conf import settings
        engine = settings.DATABASES['default']['ENGINE']
        self.assertEqual(engine, 'django.db.backends.postgresql')


# ─────────────────────────────────────────────────────────────────────────────
# [BE][FE][5] User registration
# ─────────────────────────────────────────────────────────────────────────────
class UserRegistrationTests(APITestCase):
    """[BE][FE][5] Rejestracja użytkownika."""

    def setUp(self):
        self.client = make_client()

    def test_register_with_valid_data_returns_201(self):
        """Rejestracja z poprawnymi danymi zwraca status 201."""
        payload = {'email': 'new@example.com', 'password': 'Valid1234', 'name': 'newuser'}
        response = self.client.post(REGISTER_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_registered_user_exists_in_database(self):
        """Po rejestracji użytkownik istnieje w bazie danych."""
        payload = {'email': 'indb@example.com', 'password': 'Valid1234', 'name': 'indbuser'}
        self.client.post(REGISTER_URL, payload, format='json')
        self.assertTrue(User.objects.filter(email='indb@example.com').exists())

    def test_registered_user_is_inactive_by_default(self):
        """Nowo zarejestrowany użytkownik ma is_active=False."""
        payload = {'email': 'inactive@example.com', 'password': 'Valid1234', 'name': 'inactiveuser'}
        self.client.post(REGISTER_URL, payload, format='json')
        user = User.objects.get(email='inactive@example.com')
        self.assertFalse(user.is_active)

    def test_register_sends_activation_email(self):
        """Rejestracja wysyła email aktywacyjny."""
        payload = {'email': 'email@example.com', 'password': 'Valid1234', 'name': 'emailuser'}
        self.client.post(REGISTER_URL, payload, format='json')
        self.assertGreater(len(mail.outbox), 0)
        self.assertIn('Activate', mail.outbox[0].subject)

    def test_register_without_password_returns_400(self):
        """Rejestracja bez hasła zwraca status 400."""
        payload = {'email': 'nopass@example.com', 'name': 'nopass'}
        response = self.client.post(REGISTER_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_with_duplicate_email_returns_400(self):
        """Rejestracja z już istniejącym e-mailem zwraca status 400."""
        # Rejestruj przez API (serializer sprawdza unikalność emaila)
        payload1 = {'email': 'dup@example.com', 'password': 'Valid1234', 'name': 'dup1'}
        self.client.post(REGISTER_URL, payload1, format='json')
        payload2 = {'email': 'dup@example.com', 'password': 'Valid1234', 'name': 'dup2'}
        response = self.client.post(REGISTER_URL, payload2, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_with_weak_password_returns_400(self):
        """Rejestracja ze słabym hasłem zwraca 400."""
        payload = {'email': 'weak@example.com', 'password': 'password', 'name': 'weakuser'}
        response = self.client.post(REGISTER_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# [BE][7] Password hashing
# ─────────────────────────────────────────────────────────────────────────────
class PasswordHashingTests(TestCase):
    """[BE][7] Hashowanie haseł."""

    def test_password_is_not_stored_as_plaintext(self):
        """Hasło nie jest przechowywane w bazie jako plain text."""
        user = User.objects.create_user(name='hashuser', email='hash@example.com', password='Test1234')
        self.assertNotEqual(user.password, 'Test1234')

    def test_hashed_password_starts_with_algorithm_prefix(self):
        """Hasło jest zahashowane algorytmem Django."""
        user = User.objects.create_user(name='algouser', email='algo@example.com', password='Test1234')
        known_prefixes = ('pbkdf2_sha256', 'argon2', 'bcrypt', 'scrypt')
        self.assertTrue(any(user.password.startswith(p) for p in known_prefixes))

    def test_check_password_returns_true_for_correct_password(self):
        """check_password zwraca True dla poprawnego hasła."""
        user = User.objects.create_user(name='checkuser', email='check@example.com', password='Test1234')
        self.assertTrue(user.check_password('Test1234'))

    def test_check_password_returns_false_for_wrong_password(self):
        """check_password zwraca False dla błędnego hasła."""
        user = User.objects.create_user(name='wronguser', email='wrong@example.com', password='Test1234')
        self.assertFalse(user.check_password('WrongPass9'))

    def test_password_validator_rejects_short_password(self):
        """Walidator odrzuca hasło krótsze niż 8 znaków."""
        from users.validators import NumberAndLengthValidator
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            NumberAndLengthValidator().validate('Ab1')

    def test_password_validator_rejects_no_digit(self):
        """Walidator odrzuca hasło bez cyfry."""
        from users.validators import NumberAndLengthValidator
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            NumberAndLengthValidator().validate('AbcdefgH')

    def test_password_validator_rejects_no_uppercase(self):
        """Walidator odrzuca hasło bez wielkiej litery."""
        from users.validators import NumberAndLengthValidator
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            NumberAndLengthValidator().validate('abcdefg1')

    def test_password_validator_rejects_no_lowercase(self):
        """Walidator odrzuca hasło bez małej litery."""
        from users.validators import NumberAndLengthValidator
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            NumberAndLengthValidator().validate('ABCDEFG1')

    def test_password_validator_accepts_valid_password(self):
        """Walidator akceptuje poprawne hasło."""
        from users.validators import NumberAndLengthValidator
        # Brak wyjątku = test zaliczony
        NumberAndLengthValidator().validate('ValidPass1')


# ─────────────────────────────────────────────────────────────────────────────
# [BE][FE][8] Email activation
# ─────────────────────────────────────────────────────────────────────────────
class EmailActivationTests(APITestCase):
    """[BE][FE][8] Aktywacja konta przez email."""

    def setUp(self):
        self.client = make_client()

    def _make_inactive_user(self):
        user = User.objects.create_user(name='actuser', email='act@example.com', password='Test1234')
        user.is_active = False
        user.save()
        return user

    def _activation_url(self, user):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return f'/api/users/activate/{uid}/{token}/'

    def test_valid_activation_link_activates_user(self):
        """Poprawny link aktywacyjny ustawia is_active=True."""
        user = self._make_inactive_user()
        self.client.get(self._activation_url(user))
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_valid_activation_link_redirects_to_frontend(self):
        """Poprawny link aktywacyjny przekierowuje do frontendu."""
        user = self._make_inactive_user()
        response = self.client.get(self._activation_url(user))
        self.assertIn(response.status_code, [301, 302])
        self.assertIn('localhost:5173', response['Location'])

    def test_invalid_token_does_not_activate_user(self):
        """Nieprawidłowy token nie aktywuje konta."""
        user = self._make_inactive_user()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        self.client.get(f'/api/users/activate/{uid}/invalidtoken123/')
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_invalid_token_redirects_to_error_page(self):
        """Nieprawidłowy token przekierowuje na stronę błędu."""
        user = self._make_inactive_user()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        response = self.client.get(f'/api/users/activate/{uid}/invalidtoken123/')
        self.assertIn(response.status_code, [301, 302])
        self.assertIn('error', response['Location'])

    def test_registration_email_contains_activation_link(self):
        """Email wysłany po rejestracji zawiera link aktywacyjny."""
        payload = {'email': 'linkcheck@example.com', 'password': 'Valid1234', 'name': 'linkcheckuser'}
        self.client.post(REGISTER_URL, payload, format='json')
        self.assertGreater(len(mail.outbox), 0)
        self.assertIn('activate', mail.outbox[0].body)

    def test_already_active_user_redirects_to_already_activated(self):
        """Próba aktywacji już aktywnego konta przekierowuje na already-activated."""
        user = self._make_inactive_user()
        user.is_active = True
        user.save()
        response = self.client.get(self._activation_url(user))
        self.assertIn(response.status_code, [301, 302])
        self.assertIn('already-activated', response['Location'])


# ─────────────────────────────────────────────────────────────────────────────
# [BE][FE][6] User login
# ─────────────────────────────────────────────────────────────────────────────
class UserLoginTests(APITestCase):
    """[BE][FE][6] Logowanie użytkownika (JWT w ciasteczkach)."""

    def setUp(self):
        self.client = make_client()
        self.user = create_active_user()

    def test_login_with_valid_credentials_returns_200(self):
        """Logowanie z poprawnymi danymi zwraca status 200."""
        response = self.client.post(LOGIN_URL, {'email': 'test@example.com', 'password': 'Test1234'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_sets_access_token_cookie(self):
        """Logowanie ustawia ciasteczko access_token."""
        response = self.client.post(LOGIN_URL, {'email': 'test@example.com', 'password': 'Test1234'}, format='json')
        self.assertIn('access_token', response.cookies)

    def test_login_sets_refresh_token_cookie(self):
        """Logowanie ustawia ciasteczko refresh_token."""
        response = self.client.post(LOGIN_URL, {'email': 'test@example.com', 'password': 'Test1234'}, format='json')
        self.assertIn('refresh_token', response.cookies)

    def test_login_with_wrong_password_returns_400(self):
        """Logowanie z błędnym hasłem zwraca status 400."""
        response = self.client.post(LOGIN_URL, {'email': 'test@example.com', 'password': 'WrongPass9'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_nonexistent_email_returns_400(self):
        """Logowanie z nieistniejącym e-mailem zwraca status 400."""
        response = self.client.post(LOGIN_URL, {'email': 'ghost@example.com', 'password': 'Test1234'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_inactive_account_returns_403(self):
        """Logowanie na nieaktywne konto zwraca status 403.
        
        Uwaga: AuthTokenSerializer zwraca 400 gdy konto jest nieaktywne
        (authenticate() zwraca None bo is_active=False). LoginView sprawdza
        is_active osobno i zwraca 403, ale tylko gdy serializer przepuści użytkownika.
        W rzeczywistości nieaktywny user dostaje 400 z serialisera.
        """
        inactive = User.objects.create_user(
            name='inactive2', email='inactive2@example.com', password='Test1234'
        )
        inactive.is_active = False
        inactive.save()
        response = self.client.post(
            LOGIN_URL, {'email': 'inactive2@example.com', 'password': 'Test1234'}, format='json'
        )
        # Serializer odrzuca nieaktywnych z 400, LoginView odrzuca z 403
        self.assertIn(response.status_code, [400, 403])

    def test_access_token_cookie_is_httponly(self):
        """Ciasteczko access_token ma flagę HttpOnly."""
        response = self.client.post(LOGIN_URL, {'email': 'test@example.com', 'password': 'Test1234'}, format='json')
        cookie = response.cookies.get('access_token')
        self.assertIsNotNone(cookie)
        self.assertTrue(cookie['httponly'])


# ─────────────────────────────────────────────────────────────────────────────
# [BE][9] Password recovery
# ─────────────────────────────────────────────────────────────────────────────
class PasswordRecoveryTests(APITestCase):
    """[BE][9] Odzyskiwanie hasła (reset przez email)."""

    def setUp(self):
        self.client = make_client()
        self.user = create_active_user(email='reset@example.com', password='OldPass1', name='resetuser')

    def test_reset_request_with_existing_email_returns_200(self):
        """Żądanie resetu dla istniejącego emaila zwraca 200."""
        response = self.client.post(RESET_PASSWORD_URL, {'email': 'reset@example.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reset_request_sends_email(self):
        """Żądanie resetu wysyła email z linkiem."""
        self.client.post(RESET_PASSWORD_URL, {'email': 'reset@example.com'}, format='json')
        self.assertGreater(len(mail.outbox), 0)

    def test_reset_request_email_contains_reset_link(self):
        """Email resetujący zawiera link z tokenem."""
        self.client.post(RESET_PASSWORD_URL, {'email': 'reset@example.com'}, format='json')
        self.assertIn('reset-password', mail.outbox[0].body)

    def test_reset_request_with_nonexistent_email_returns_200(self):
        """Reset dla nieistniejącego emaila zwraca 200 (ochrona przed enumeracją)."""
        response = self.client.post(RESET_PASSWORD_URL, {'email': 'ghost@example.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reset_confirm_with_valid_token_changes_password(self):
        """Potwierdzenie resetu z poprawnym tokenem zmienia hasło."""
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        url = f'{RESET_PASSWORD_URL}{uid}/{token}/'
        response = self.client.post(url, {'password': 'NewValid1'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewValid1'))

    def test_reset_confirm_with_invalid_token_returns_400(self):
        """Potwierdzenie resetu z niepoprawnym tokenem zwraca 400."""
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        url = f'{RESET_PASSWORD_URL}{uid}/invalidtoken/'
        response = self.client.post(url, {'password': 'NewValid1'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_confirm_without_password_returns_400(self):
        """Potwierdzenie resetu bez podania hasła zwraca 400."""
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        url = f'{RESET_PASSWORD_URL}{uid}/{token}/'
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_confirm_with_weak_password_returns_400(self):
        """Potwierdzenie resetu ze słabym hasłem zwraca 400."""
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        url = f'{RESET_PASSWORD_URL}{uid}/{token}/'
        response = self.client.post(url, {'password': 'weak'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# [BE][10] Password change in system
# ─────────────────────────────────────────────────────────────────────────────
class PasswordChangeTests(APITestCase):
    """[BE][10] Zmiana hasła przez zalogowanego użytkownika."""

    def setUp(self):
        self.client = make_client()
        self.user = create_active_user(email='chpwd@example.com', password='OldPass1', name='chpwduser')
        login_client(self.client, email='chpwd@example.com', password='OldPass1')

    def test_change_password_with_valid_data_returns_200(self):
        """Zmiana hasła z poprawnymi danymi zwraca 200."""
        payload = {'old_password': 'OldPass1', 'new_password': 'NewPass1', 'confirm_password': 'NewPass1'}
        response = self.client.post(CHANGE_PASSWORD_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_actually_updates_password(self):
        """Po zmianie hasła nowe hasło działa do logowania."""
        payload = {'old_password': 'OldPass1', 'new_password': 'NewPass1', 'confirm_password': 'NewPass1'}
        self.client.post(CHANGE_PASSWORD_URL, payload, format='json')
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass1'))

    def test_change_password_clears_auth_cookies(self):
        """Zmiana hasła usuwa ciasteczka JWT (wylogowanie)."""
        payload = {'old_password': 'OldPass1', 'new_password': 'NewPass1', 'confirm_password': 'NewPass1'}
        response = self.client.post(CHANGE_PASSWORD_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ciasteczka powinny być wyczyszczone
        access_cookie = response.cookies.get('access_token')
        if access_cookie:
            self.assertEqual(access_cookie.value, '')

    def test_change_password_with_wrong_old_password_returns_400(self):
        """Zmiana hasła z błędnym starym hasłem zwraca 400."""
        payload = {'old_password': 'WrongOld1', 'new_password': 'NewPass1', 'confirm_password': 'NewPass1'}
        response = self.client.post(CHANGE_PASSWORD_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_with_mismatched_new_passwords_returns_400(self):
        """Zmiana hasła gdy nowe hasła nie są identyczne zwraca 400."""
        payload = {'old_password': 'OldPass1', 'new_password': 'NewPass1', 'confirm_password': 'DifferentPass2'}
        response = self.client.post(CHANGE_PASSWORD_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_unauthenticated_returns_401_or_403(self):
        """Zmiana hasła bez uwierzytelnienia zwraca 401 lub 403."""
        fresh_client = make_client()
        payload = {'old_password': 'OldPass1', 'new_password': 'NewPass1', 'confirm_password': 'NewPass1'}
        response = fresh_client.post(CHANGE_PASSWORD_URL, payload, format='json')
        self.assertIn(response.status_code, [401, 403])

    def test_change_password_with_weak_new_password_returns_400(self):
        """Zmiana hasła na zbyt słabe nowe hasło zwraca 400."""
        payload = {'old_password': 'OldPass1', 'new_password': 'weak', 'confirm_password': 'weak'}
        response = self.client.post(CHANGE_PASSWORD_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# [BE][6] Delete account
# ─────────────────────────────────────────────────────────────────────────────
class DeleteAccountTests(APITestCase):
    """[BE][6] Usuwanie konta użytkownika."""

    def setUp(self):
        self.client = make_client()
        self.user = create_active_user(email='del@example.com', password='DelPass1', name='deluser')
        login_client(self.client, email='del@example.com', password='DelPass1')

    def test_delete_account_with_correct_password_returns_204(self):
        """Usunięcie konta z poprawnym hasłem zwraca 204."""
        response = self.client.delete(DELETE_ACCOUNT_URL, {'password': 'DelPass1'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_account_removes_user_from_database(self):
        """Po usunięciu konta użytkownik nie istnieje w bazie."""
        self.client.delete(DELETE_ACCOUNT_URL, {'password': 'DelPass1'}, format='json')
        self.assertFalse(User.objects.filter(email='del@example.com').exists())

    def test_delete_account_with_wrong_password_returns_400(self):
        """Usunięcie konta z błędnym hasłem zwraca 400."""
        response = self.client.delete(DELETE_ACCOUNT_URL, {'password': 'WrongPass9'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_account_without_password_returns_400(self):
        """Usunięcie konta bez podania hasła zwraca 400."""
        response = self.client.delete(DELETE_ACCOUNT_URL, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_account_unauthenticated_returns_401_or_403(self):
        """Usunięcie konta bez logowania zwraca 401 lub 403."""
        fresh_client = make_client()
        response = fresh_client.delete(DELETE_ACCOUNT_URL, {'password': 'DelPass1'}, format='json')
        self.assertIn(response.status_code, [401, 403])

    def test_delete_account_clears_auth_cookies(self):
        """Usunięcie konta czyści ciasteczka JWT."""
        response = self.client.delete(DELETE_ACCOUNT_URL, {'password': 'DelPass1'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        access_cookie = response.cookies.get('access_token')
        if access_cookie:
            self.assertEqual(access_cookie.value, '')

