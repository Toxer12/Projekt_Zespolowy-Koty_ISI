from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from projects.models import Project, Tag

User = get_user_model()

PROJECT_LIST_URL = '/api/projects/'
PROJECT_PUBLIC_URL = '/api/projects/public/'
TAG_LIST_URL = '/api/projects/tags/'


def make_client():
    """APIClient z wyłączonym CSRF."""
    return APIClient(enforce_csrf_checks=False)


def create_active_user(email='owner@example.com', password='Pass1234', name='owneruser'):
    user = User.objects.create_user(name=name, email=email, password=password)
    user.is_active = True
    user.save()
    return user


def auth_client(user):
    """Zwraca APIClient z JWT access_token w ciasteczku."""
    client = make_client()
    refresh = RefreshToken.for_user(user)
    client.cookies['access_token'] = str(refresh.access_token)
    return client


def project_detail_url(pk):
    return f'/api/projects/{pk}/'


# ─────────────────────────────────────────────────────────────────────────────
# [5.1] Tworzenie projektu
# ─────────────────────────────────────────────────────────────────────────────
class ProjectCreateTests(APITestCase):
    """[5.1] Tworzenie projektu."""

    def setUp(self):
        self.user = create_active_user()
        self.client = auth_client(self.user)

    def test_create_project_returns_201(self):
        """Tworzenie projektu z poprawnymi danymi zwraca 201."""
        payload = {'name': 'Nowy projekt', 'visibility': 'private'}
        response = self.client.post(PROJECT_LIST_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_project_saves_to_database(self):
        """Nowo utworzony projekt istnieje w bazie danych."""
        payload = {'name': 'Projekt DB', 'visibility': 'private'}
        self.client.post(PROJECT_LIST_URL, payload, format='json')
        self.assertTrue(Project.objects.filter(name='Projekt DB').exists())

    def test_create_project_assigns_owner(self):
        """Tworzony projekt ma jako właściciela zalogowanego użytkownika."""
        payload = {'name': 'Projekt Ownera', 'visibility': 'private'}
        response = self.client.post(PROJECT_LIST_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project = Project.objects.get(name='Projekt Ownera')
        self.assertEqual(project.owner, self.user)

    def test_create_project_with_tags(self):
        """Tworzenie projektu z tagami zapisuje tagi."""
        payload = {'name': 'Projekt z tagami', 'visibility': 'private', 'tags': ['python', 'django']}
        response = self.client.post(PROJECT_LIST_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project = Project.objects.get(name='Projekt z tagami')
        tag_names = list(project.tags.values_list('name', flat=True))
        self.assertIn('python', tag_names)
        self.assertIn('django', tag_names)

    def test_create_project_default_visibility_is_private(self):
        """Domyślna widoczność projektu to 'private'."""
        payload = {'name': 'Projekt domyslny'}
        response = self.client.post(PROJECT_LIST_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project = Project.objects.get(name='Projekt domyslny')
        self.assertEqual(project.visibility, 'private')

    def test_create_project_without_name_returns_400(self):
        """Tworzenie projektu bez nazwy zwraca 400."""
        payload = {'visibility': 'private'}
        response = self.client.post(PROJECT_LIST_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_project_unauthenticated_returns_401_or_403(self):
        """Tworzenie projektu bez logowania zwraca 401 lub 403."""
        anon = make_client()
        response = anon.post(PROJECT_LIST_URL, {'name': 'Hack'}, format='json')
        self.assertIn(response.status_code, [401, 403])


# ─────────────────────────────────────────────────────────────────────────────
# [5.2] Edycja projektu
# ─────────────────────────────────────────────────────────────────────────────
class ProjectUpdateTests(APITestCase):
    """[5.2] Edycja projektu."""

    def setUp(self):
        self.user = create_active_user()
        self.client = auth_client(self.user)
        self.project = Project.objects.create(name='Stary projekt', owner=self.user, visibility='private')

    def test_patch_project_name_returns_200(self):
        """PATCH projektu ze zmianą nazwy zwraca 200."""
        url = project_detail_url(self.project.pk)
        response = self.client.patch(url, {'name': 'Nowa nazwa'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_project_name_updates_database(self):
        """Po edycji nowa nazwa jest zapisana w bazie."""
        url = project_detail_url(self.project.pk)
        self.client.patch(url, {'name': 'Zaktualizowana nazwa'}, format='json')
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Zaktualizowana nazwa')

    def test_patch_project_visibility(self):
        """Zmiana widoczności projektu zostaje zapisana."""
        url = project_detail_url(self.project.pk)
        self.client.patch(url, {'visibility': 'public'}, format='json')
        self.project.refresh_from_db()
        self.assertEqual(self.project.visibility, 'public')

    def test_patch_project_tags_updates_tags(self):
        """Edycja tagów projektu aktualizuje powiązane tagi."""
        url = project_detail_url(self.project.pk)
        self.client.patch(url, {'tags': ['flask', 'api']}, format='json')
        tag_names = list(self.project.tags.values_list('name', flat=True))
        self.assertIn('flask', tag_names)
        self.assertIn('api', tag_names)

    def test_patch_other_users_project_returns_404(self):
        """Edycja cudzego projektu zwraca 404 (queryset filtruje po właścicielu)."""
        other = create_active_user(email='other@example.com', name='otheruser2')
        other_project = Project.objects.create(name='Cudzy projekt', owner=other, visibility='private')
        url = project_detail_url(other_project.pk)
        response = self.client.patch(url, {'name': 'Zmiana'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_project_unauthenticated_returns_401_or_403(self):
        """Edycja projektu bez logowania zwraca 401 lub 403."""
        anon = make_client()
        url = project_detail_url(self.project.pk)
        response = anon.patch(url, {'name': 'Hack'}, format='json')
        self.assertIn(response.status_code, [401, 403])


# ─────────────────────────────────────────────────────────────────────────────
# [5.3] Usuwanie projektu
# ─────────────────────────────────────────────────────────────────────────────
class ProjectDeleteTests(APITestCase):
    """[5.3] Usuwanie projektu."""

    def setUp(self):
        self.user = create_active_user()
        self.client = auth_client(self.user)
        self.project = Project.objects.create(name='Projekt do usunięcia', owner=self.user)

    def test_delete_project_returns_204(self):
        """DELETE projektu zwraca 204."""
        url = project_detail_url(self.project.pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_project_removes_from_database(self):
        """Po usunięciu projekt nie istnieje w bazie."""
        pk = self.project.pk
        url = project_detail_url(pk)
        self.client.delete(url)
        self.assertFalse(Project.objects.filter(pk=pk).exists())

    def test_delete_other_users_project_returns_404(self):
        """Usunięcie cudzego projektu zwraca 404."""
        other = create_active_user(email='other2@example.com', name='otheruser3')
        other_project = Project.objects.create(name='Cudzy projekt2', owner=other)
        url = project_detail_url(other_project.pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_project_unauthenticated_returns_401_or_403(self):
        """Usunięcie projektu bez logowania zwraca 401 lub 403."""
        anon = make_client()
        url = project_detail_url(self.project.pk)
        response = anon.delete(url)
        self.assertIn(response.status_code, [401, 403])


# ─────────────────────────────────────────────────────────────────────────────
# [5.4] Lista projektów użytkownika
# ─────────────────────────────────────────────────────────────────────────────
class ProjectListTests(APITestCase):
    """[5.4] Lista projektów użytkownika."""

    def setUp(self):
        self.user = create_active_user()
        self.client = auth_client(self.user)
        self.other = create_active_user(email='other3@example.com', name='otheruser4')
        # Projekty własne
        self.p1 = Project.objects.create(name='Mój projekt 1', owner=self.user, visibility='private')
        self.p2 = Project.objects.create(name='Mój projekt 2', owner=self.user, visibility='public')
        # Cudzy projekt
        Project.objects.create(name='Cudzy projekt', owner=self.other, visibility='private')

    def test_list_returns_200(self):
        """GET /api/projects/ zwraca 200."""
        response = self.client.get(PROJECT_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_returns_only_own_projects(self):
        """Lista zwraca tylko projekty zalogowanego użytkownika."""
        response = self.client.get(PROJECT_LIST_URL)
        names = [p['name'] for p in response.data]
        self.assertIn('Mój projekt 1', names)
        self.assertIn('Mój projekt 2', names)
        self.assertNotIn('Cudzy projekt', names)

    def test_list_count_matches_own_projects(self):
        """Liczba zwróconych projektów odpowiada liczbie projektów użytkownika."""
        response = self.client.get(PROJECT_LIST_URL)
        self.assertEqual(len(response.data), 2)

    def test_list_unauthenticated_returns_401_or_403(self):
        """Lista projektów bez logowania zwraca 401 lub 403."""
        anon = make_client()
        response = anon.get(PROJECT_LIST_URL)
        self.assertIn(response.status_code, [401, 403])

    def test_list_filter_by_visibility_private(self):
        """Filtrowanie po visibility=private zwraca tylko prywatne projekty."""
        response = self.client.get(PROJECT_LIST_URL + '?visibility=private')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for p in response.data:
            self.assertEqual(p['visibility'], 'private')

    def test_list_filter_by_visibility_public(self):
        """Filtrowanie po visibility=public zwraca tylko publiczne projekty."""
        response = self.client.get(PROJECT_LIST_URL + '?visibility=public')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for p in response.data:
            self.assertEqual(p['visibility'], 'public')


# ─────────────────────────────────────────────────────────────────────────────
# [5.5] Wyszukiwanie projektów (ILIKE / search)
# ─────────────────────────────────────────────────────────────────────────────
class ProjectSearchTests(APITestCase):
    """[5.5] Wyszukiwanie projektów (search po nazwie i tagach)."""

    def setUp(self):
        self.user = create_active_user()
        self.client = auth_client(self.user)
        tag_py = Tag.objects.create(name='python')
        self.p_py = Project.objects.create(name='Python app', owner=self.user, visibility='private')
        self.p_py.tags.add(tag_py)
        self.p_other = Project.objects.create(name='Java app', owner=self.user, visibility='private')

    def test_search_by_name_returns_matching_project(self):
        """Wyszukiwanie po nazwie zwraca pasujące projekty."""
        response = self.client.get(PROJECT_LIST_URL + '?search=Python')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [p['name'] for p in response.data]
        self.assertIn('Python app', names)

    def test_search_by_name_excludes_non_matching(self):
        """Wyszukiwanie po nazwie nie zwraca niepasujących projektów."""
        response = self.client.get(PROJECT_LIST_URL + '?search=Python')
        names = [p['name'] for p in response.data]
        self.assertNotIn('Java app', names)

    def test_search_by_tag_returns_matching_project(self):
        """Wyszukiwanie po nazwie tagu zwraca projekty z tym tagiem."""
        response = self.client.get(PROJECT_LIST_URL + '?search=python')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [p['name'] for p in response.data]
        self.assertIn('Python app', names)

    def test_search_case_insensitive(self):
        """Wyszukiwanie jest case-insensitive."""
        response = self.client.get(PROJECT_LIST_URL + '?search=python')
        names = [p['name'] for p in response.data]
        self.assertIn('Python app', names)

    def test_filter_by_tag_query_param(self):
        """Filtrowanie przez ?tag= zwraca projekty z podanym tagiem."""
        response = self.client.get(PROJECT_LIST_URL + '?tag=python')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [p['name'] for p in response.data]
        self.assertIn('Python app', names)
        self.assertNotIn('Java app', names)


# ─────────────────────────────────────────────────────────────────────────────
# [6.1] CRUD tagów
# ─────────────────────────────────────────────────────────────────────────────
class TagCRUDTests(APITestCase):
    """[6.1] CRUD tagów – tworzenie i odczyt."""

    def setUp(self):
        self.user = create_active_user()
        self.client = auth_client(self.user)

    def test_tag_created_via_project_creation(self):
        """Tag jest tworzony automatycznie przy tworzeniu projektu z tagiem."""
        payload = {'name': 'Projekt z nowym tagiem', 'tags': ['newtag']}
        self.client.post(PROJECT_LIST_URL, payload, format='json')
        self.assertTrue(Tag.objects.filter(name='newtag').exists())

    def test_tag_list_returns_200(self):
        """GET /api/projects/tags/ zwraca 200."""
        response = self.client.get(TAG_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_tag_list_is_accessible_without_auth(self):
        """Lista tagów jest dostępna bez uwierzytelnienia."""
        anon = make_client()
        response = anon.get(TAG_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_tag_list_contains_existing_tags(self):
        """Lista tagów zwraca istniejące tagi."""
        Tag.objects.create(name='listtag')
        response = self.client.get(TAG_LIST_URL)
        names = [t['name'] for t in response.data]
        self.assertIn('listtag', names)

    def test_tag_name_is_unique(self):
        """Tagi mają unikalną nazwę (get_or_create nie tworzy duplikatów)."""
        payload1 = {'name': 'Projekt A', 'tags': ['unique_tag']}
        payload2 = {'name': 'Projekt B', 'tags': ['unique_tag']}
        self.client.post(PROJECT_LIST_URL, payload1, format='json')
        self.client.post(PROJECT_LIST_URL, payload2, format='json')
        count = Tag.objects.filter(name='unique_tag').count()
        self.assertEqual(count, 1)

    def test_tag_name_is_normalized_to_lowercase(self):
        """Nazwa tagu jest normalizowana do małych liter."""
        payload = {'name': 'Projekt uppercase tag', 'tags': ['DJANGO']}
        self.client.post(PROJECT_LIST_URL, payload, format='json')
        self.assertTrue(Tag.objects.filter(name='django').exists())


# ─────────────────────────────────────────────────────────────────────────────
# [6.2] Przypisywanie tagów do projektów
# ─────────────────────────────────────────────────────────────────────────────
class TagAssignmentTests(APITestCase):
    """[6.2] Przypisywanie tagów do projektów."""

    def setUp(self):
        self.user = create_active_user()
        self.client = auth_client(self.user)
        self.project = Project.objects.create(name='Projekt tagowania', owner=self.user)

    def test_assign_tags_on_create(self):
        """Tagi przypisane przy tworzeniu są widoczne w odpowiedzi."""
        payload = {'name': 'Nowy z tagami', 'tags': ['react', 'node']}
        response = self.client.post(PROJECT_LIST_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('react', response.data.get('tags', []))
        self.assertIn('node', response.data.get('tags', []))

    def test_assign_tags_on_patch(self):
        """Tagi przypisane przez PATCH są widoczne w odpowiedzi."""
        url = project_detail_url(self.project.pk)
        response = self.client.patch(url, {'tags': ['vue', 'ts']}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('vue', response.data.get('tags', []))
        self.assertIn('ts', response.data.get('tags', []))

    def test_patch_tags_replaces_existing_tags(self):
        """PATCH tagów zastępuje istniejące tagi nowymi."""
        tag_old = Tag.objects.create(name='old')
        self.project.tags.add(tag_old)
        url = project_detail_url(self.project.pk)
        self.client.patch(url, {'tags': ['new']}, format='json')
        tag_names = list(self.project.tags.values_list('name', flat=True))
        self.assertIn('new', tag_names)
        self.assertNotIn('old', tag_names)

    def test_tags_returned_in_project_detail(self):
        """Tagi projektu są zwracane przy GET na szczegóły projektu."""
        tag = Tag.objects.create(name='detail_tag')
        self.project.tags.add(tag)
        url = project_detail_url(self.project.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detail_tag', response.data.get('tags', []))

    def test_empty_tags_list_clears_tags(self):
        """PATCH z pustą listą tagów usuwa wszystkie tagi projektu."""
        tag = Tag.objects.create(name='to_remove')
        self.project.tags.add(tag)
        url = project_detail_url(self.project.pk)
        self.client.patch(url, {'tags': []}, format='json')
        self.assertEqual(self.project.tags.count(), 0)


# ─────────────────────────────────────────────────────────────────────────────
# [6.3] Filtrowanie projektów po tagach
# ─────────────────────────────────────────────────────────────────────────────
class TagFilterTests(APITestCase):
    """[6.3] Filtrowanie projektów po tagach."""

    def setUp(self):
        self.user = create_active_user()
        self.client = auth_client(self.user)
        tag_py = Tag.objects.create(name='python')
        tag_js = Tag.objects.create(name='javascript')
        self.p_py = Project.objects.create(name='Python projekt', owner=self.user)
        self.p_py.tags.add(tag_py)
        self.p_js = Project.objects.create(name='JS projekt', owner=self.user)
        self.p_js.tags.add(tag_js)
        self.p_none = Project.objects.create(name='Bez tagów', owner=self.user)

    def test_filter_by_tag_returns_correct_project(self):
        """?tag=python zwraca projekty z tagiem 'python'."""
        response = self.client.get(PROJECT_LIST_URL + '?tag=python')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [p['name'] for p in response.data]
        self.assertIn('Python projekt', names)

    def test_filter_by_tag_excludes_other_projects(self):
        """?tag=python nie zwraca projektów bez tego tagu."""
        response = self.client.get(PROJECT_LIST_URL + '?tag=python')
        names = [p['name'] for p in response.data]
        self.assertNotIn('JS projekt', names)
        self.assertNotIn('Bez tagów', names)

    def test_filter_by_nonexistent_tag_returns_empty(self):
        """?tag=nieistniejący zwraca pustą listę."""
        response = self.client.get(PROJECT_LIST_URL + '?tag=nieistniejacy')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_public_projects_filterable_by_tag(self):
        """Publiczna lista projektów (/public/) obsługuje filtrowanie przez ?search=tag."""
        tag = Tag.objects.create(name='publictag')
        pub_project = Project.objects.create(name='Publiczny z tagiem', owner=self.user, visibility='public')
        pub_project.tags.add(tag)
        anon = make_client()
        response = anon.get(PROJECT_PUBLIC_URL + '?search=publictag')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [p['name'] for p in response.data]
        self.assertIn('Publiczny z tagiem', names)


# ─────────────────────────────────────────────────────────────────────────────
# Publiczne projekty (dodatkowe)
# ─────────────────────────────────────────────────────────────────────────────
class PublicProjectListTests(APITestCase):
    """Publiczna lista projektów – dostępna bez uwierzytelnienia."""

    def setUp(self):
        self.user = create_active_user()
        self.pub = Project.objects.create(name='Publiczny', owner=self.user, visibility='public')
        self.priv = Project.objects.create(name='Prywatny', owner=self.user, visibility='private')

    def test_public_list_returns_200_without_auth(self):
        """GET /api/projects/public/ zwraca 200 bez logowania."""
        anon = make_client()
        response = anon.get(PROJECT_PUBLIC_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_public_list_contains_only_public_projects(self):
        """Publiczna lista zawiera tylko projekty publiczne."""
        anon = make_client()
        response = anon.get(PROJECT_PUBLIC_URL)
        names = [p['name'] for p in response.data]
        self.assertIn('Publiczny', names)
        self.assertNotIn('Prywatny', names)
