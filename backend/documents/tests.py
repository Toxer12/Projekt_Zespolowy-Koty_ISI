import io
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from projects.models import Project, ProjectMember
from documents.models import Document, Chunk

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(email, password='Pass1234x', username=None, is_active=True):
    username = username or email.split('@')[0]
    user = User.objects.create_user(email=email, password=password, username=username)
    user.is_active = is_active
    user.save()
    return user


def auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.cookies['access_token'] = str(refresh.access_token)
    return client


def make_project(owner, name='Doc Project', visibility='private'):
    return Project.objects.create(owner=owner, name=name, visibility=visibility)


def add_member(project, user, role):
    return ProjectMember.objects.create(
        project=project, user=user, role=role,
        added_by=project.owner,
    )


def make_document(project, uploader, name='test.txt', status='ready'):
    return Document.objects.create(
        project=project,
        uploaded_by=uploader,
        original_name=name,
        file_type='txt',
        file_size=100,
        status=status,
    )


def fake_txt_file(name='sample.txt', content=b'Hello world'):
    f = io.BytesIO(content)
    f.name = name
    f.size = len(content)
    return f


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class DocumentModelTests(TestCase):

    def setUp(self):
        self.owner = make_user('docown@docs.com')
        self.project = make_project(self.owner)

    def test_document_str(self):
        doc = make_document(self.project, self.owner)
        self.assertIn('test.txt', str(doc))

    def test_document_default_status_is_pending(self):
        doc = Document.objects.create(
            project=self.project,
            uploaded_by=self.owner,
            original_name='a.txt',
            file_type='txt',
            file_size=10,
        )
        self.assertEqual(doc.status, Document.Status.PENDING)

    def test_document_default_embedding_status_is_none(self):
        doc = make_document(self.project, self.owner)
        self.assertEqual(doc.embedding_status, Document.EmbeddingStatus.NONE)

    def test_chunk_str(self):
        doc = make_document(self.project, self.owner)
        chunk = Chunk.objects.create(
            document=doc, index=0, text='hello', char_count=5, chunk_type='sentence',
        )
        self.assertIn('0', str(chunk))

    def test_document_uuid_primary_key(self):
        doc = make_document(self.project, self.owner)
        import uuid
        self.assertIsInstance(doc.pk, uuid.UUID)


# ---------------------------------------------------------------------------
# DocumentUploadView  POST /api/documents/
# ---------------------------------------------------------------------------

class DocumentUploadViewTests(TestCase):

    def setUp(self):
        self.owner = make_user('upown@docs.com')
        self.project = make_project(self.owner)
        self.url = '/api/documents/'

    @patch('documents.views.process_document')
    def test_owner_can_upload_txt(self, mock_task):
        mock_task.delay = MagicMock()
        c = auth_client(self.owner)
        f = fake_txt_file('note.txt')
        resp = c.post(
            self.url,
            {'file': f, 'project_id': self.project.pk},
            format='multipart',
        )
        self.assertEqual(resp.status_code, 202)
        mock_task.delay.assert_called_once()

    @patch('documents.views.process_document')
    def test_editor_can_upload(self, mock_task):
        mock_task.delay = MagicMock()
        editor = make_user('editor@docs.com')
        add_member(self.project, editor, 'editor')
        c = auth_client(editor)
        f = fake_txt_file('note2.txt')
        resp = c.post(
            self.url,
            {'file': f, 'project_id': self.project.pk},
            format='multipart',
        )
        self.assertEqual(resp.status_code, 202)

    @patch('documents.views.process_document')
    def test_viewer_cannot_upload(self, mock_task):
        mock_task.delay = MagicMock()
        viewer = make_user('viewer@docs.com')
        add_member(self.project, viewer, 'viewer')
        c = auth_client(viewer)
        f = fake_txt_file('note3.txt')
        resp = c.post(
            self.url,
            {'file': f, 'project_id': self.project.pk},
            format='multipart',
        )
        self.assertEqual(resp.status_code, 403)

    @patch('documents.views.process_document')
    def test_stranger_cannot_upload_to_private_project(self, mock_task):
        mock_task.delay = MagicMock()
        stranger = make_user('str@docs.com')
        c = auth_client(stranger)
        f = fake_txt_file('note4.txt')
        resp = c.post(
            self.url,
            {'file': f, 'project_id': self.project.pk},
            format='multipart',
        )
        self.assertEqual(resp.status_code, 403)

    def test_upload_invalid_extension_returns_400(self):
        c = auth_client(self.owner)
        f = fake_txt_file('malware.exe', b'bad content')
        resp = c.post(
            self.url,
            {'file': f, 'project_id': self.project.pk},
            format='multipart',
        )
        self.assertEqual(resp.status_code, 400)

    @patch('documents.views.process_document')
    def test_upload_oversized_file_returns_400(self, mock_task):
        mock_task.delay = MagicMock()
        c = auth_client(self.owner)
        # Simulate file larger than 10 MB
        big_content = b'x' * (10 * 1024 * 1024 + 1)
        f = fake_txt_file('big.txt', big_content)
        resp = c.post(
            self.url,
            {'file': f, 'project_id': self.project.pk},
            format='multipart',
        )
        self.assertEqual(resp.status_code, 400)

    def test_upload_without_project_id_returns_400(self):
        c = auth_client(self.owner)
        f = fake_txt_file('note5.txt')
        resp = c.post(self.url, {'file': f}, format='multipart')
        self.assertEqual(resp.status_code, 400)

    def test_unauthenticated_cannot_upload(self):
        c = APIClient()
        f = fake_txt_file('note6.txt')
        resp = c.post(
            self.url,
            {'file': f, 'project_id': self.project.pk},
            format='multipart',
        )
        self.assertEqual(resp.status_code, 401)

    def test_upload_nonexistent_project_returns_404(self):
        c = auth_client(self.owner)
        f = fake_txt_file('note7.txt')
        resp = c.post(self.url, {'file': f, 'project_id': 99999}, format='multipart')
        self.assertEqual(resp.status_code, 404)


# ---------------------------------------------------------------------------
# ProjectDocumentListView  GET /api/documents/list/?project_id=<pk>
# ---------------------------------------------------------------------------

class ProjectDocumentListViewTests(TestCase):

    def setUp(self):
        self.owner = make_user('listdown@docs.com')
        self.project = make_project(self.owner)
        make_document(self.project, self.owner, 'doc1.txt')
        make_document(self.project, self.owner, 'doc2.txt')
        self.url = f'/api/documents/list/?project_id={self.project.pk}'

    def test_owner_can_list_documents(self):
        c = auth_client(self.owner)
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 2)

    def test_member_can_list_documents(self):
        member = make_user('listmem@docs.com')
        add_member(self.project, member, 'viewer')
        c = auth_client(member)
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_stranger_cannot_list_documents(self):
        stranger = make_user('liststr@docs.com')
        c = auth_client(stranger)
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_missing_project_id_returns_empty(self):
        c = auth_client(self.owner)
        resp = c.get('/api/documents/list/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 0)

    def test_unauthenticated_cannot_list(self):
        c = APIClient()
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 401)


# ---------------------------------------------------------------------------
# DocumentDetailView  GET/DELETE /api/documents/<uuid>/
# ---------------------------------------------------------------------------

class DocumentDetailViewTests(TestCase):

    def setUp(self):
        self.owner = make_user('detdown@docs.com')
        self.project = make_project(self.owner)
        self.doc = make_document(self.project, self.owner, 'detail.txt')
        self.url = f'/api/documents/{self.doc.pk}/'

    def test_owner_can_get_document(self):
        c = auth_client(self.owner)
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['original_name'], 'detail.txt')

    def test_member_can_get_document(self):
        member = make_user('detmem@docs.com')
        add_member(self.project, member, 'viewer')
        c = auth_client(member)
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_stranger_cannot_get_document(self):
        stranger = make_user('detstr@docs.com')
        c = auth_client(stranger)
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 403)

    @patch('documents.views.get_chroma_client')
    @patch('documents.views.get_or_create_collection')
    def test_owner_can_delete_document(self, mock_col, mock_client):
        mock_collection = MagicMock()
        mock_collection.get.return_value = {'ids': []}
        mock_col.return_value = mock_collection
        c = auth_client(self.owner)
        # Patch file.delete to avoid filesystem errors
        with patch.object(self.doc.file, 'delete', return_value=None):
            resp = c.delete(self.url)
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(Document.objects.filter(pk=self.doc.pk).exists())

    def test_viewer_cannot_delete_document(self):
        viewer = make_user('detvie@docs.com')
        add_member(self.project, viewer, 'viewer')
        c = auth_client(viewer)
        resp = c.delete(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_stranger_cannot_delete_document(self):
        stranger = make_user('detstr2@docs.com')
        c = auth_client(stranger)
        resp = c.delete(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_nonexistent_document_returns_404(self):
        import uuid
        c = auth_client(self.owner)
        resp = c.get(f'/api/documents/{uuid.uuid4()}/')
        self.assertEqual(resp.status_code, 404)


# ---------------------------------------------------------------------------
# DocumentChunkListView  GET /api/documents/<uuid>/chunks/
# ---------------------------------------------------------------------------

class DocumentChunkListViewTests(TestCase):

    def setUp(self):
        self.owner = make_user('cown@docs.com')
        self.project = make_project(self.owner)
        self.doc = make_document(self.project, self.owner)
        Chunk.objects.create(document=self.doc, index=0, text='chunk A', char_count=7, chunk_type='sentence')
        Chunk.objects.create(document=self.doc, index=1, text='chunk B', char_count=7, chunk_type='sentence')
        self.url = f'/api/documents/{self.doc.pk}/chunks/'

    def test_owner_can_list_chunks(self):
        c = auth_client(self.owner)
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 2)

    def test_chunks_are_ordered_by_index(self):
        c = auth_client(self.owner)
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 200)
        indexes = [ch['index'] for ch in resp.data]
        self.assertEqual(indexes, sorted(indexes))

    def test_member_can_list_chunks(self):
        member = make_user('cmem@docs.com')
        add_member(self.project, member, 'viewer')
        c = auth_client(member)
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_stranger_cannot_list_chunks(self):
        stranger = make_user('cstr@docs.com')
        c = auth_client(stranger)
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_unauthenticated_cannot_list_chunks(self):
        c = APIClient()
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 401)


# ---------------------------------------------------------------------------
# DocumentUploadSerializer validation
# ---------------------------------------------------------------------------

class DocumentUploadSerializerTests(TestCase):

    def test_allowed_extensions(self):
        from documents.serializers import ALLOWED_EXTENSIONS
        self.assertIn('pdf', ALLOWED_EXTENSIONS)
        self.assertIn('txt', ALLOWED_EXTENSIONS)

    def test_max_file_size_is_10mb(self):
        from documents.serializers import MAX_FILE_SIZE
        self.assertEqual(MAX_FILE_SIZE, 10 * 1024 * 1024)
