import uuid
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.core.cache import cache

from users.auth import CookieJWTAuthentication
from projects.models import Project, ProjectMember
from documents.models import Document, Chunk
from documents.serializers import DocumentUploadSerializer, DocumentSerializer, ChunkSerializer
from documents.tasks import process_document, run_semantic_search_task
from documents.tasks import reembed_chunk_task

def _get_project_role(project, user):
    """Returns 'owner', 'admin', 'editor', 'viewer', or None."""
    if project.owner == user:
        return 'owner'
    try:
        return project.members.get(user=user).role
    except ProjectMember.DoesNotExist:
        return None


class DocumentUploadView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        project_id = serializer.validated_data['project_id']
        project    = get_object_or_404(Project, pk=project_id)

        role = _get_project_role(project, request.user)
        if role not in ('owner', 'admin', 'editor'):
            raise PermissionDenied("Nie masz uprawnień do dodawania dokumentów.")

        doc = serializer.save()
        process_document.delay(str(doc.pk))

        return Response(
            DocumentSerializer(doc, context={'request': request}).data,
            status=status.HTTP_202_ACCEPTED,
        )


class ProjectDocumentListView(generics.ListAPIView):
    serializer_class       = DocumentSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get_queryset(self):
        project_id = self.request.query_params.get('project_id')
        if not project_id:
            return Document.objects.none()
        project = get_object_or_404(Project, pk=project_id)
        role = _get_project_role(project, self.request.user)
        if role is None and project.visibility != 'public':
            raise PermissionDenied("Nie masz dostępu do tego projektu.")
        return Document.objects.filter(project=project).prefetch_related('chunks')


class DocumentDetailView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def _get_doc_and_role(self, request, pk):
        doc  = get_object_or_404(Document, pk=pk)
        role = _get_project_role(doc.project, request.user)
        return doc, role

    def get(self, request, pk):
        doc, role = self._get_doc_and_role(request, pk)
        if role is None and doc.project.visibility != 'public':
            raise PermissionDenied("Nie masz dostępu do tego dokumentu.")
        return Response(DocumentSerializer(doc, context={'request': request}).data)

    def delete(self, request, pk):
        doc, role = self._get_doc_and_role(request, pk)
        if role not in ('owner', 'admin', 'editor'):
            raise PermissionDenied("Nie masz uprawnień do usuwania dokumentów.")
        try:
            from documents.embeddings import get_chroma_client, get_or_create_collection
            client     = get_chroma_client()
            collection = get_or_create_collection(client)
            existing   = collection.get(where={"document_id": str(doc.pk)})
            if existing['ids']:
                collection.delete(ids=existing['ids'])
        except Exception:
            pass
        doc.file.delete(save=False)
        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentChunkListView(generics.ListAPIView):
    serializer_class       = ChunkSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get_queryset(self):
        doc  = get_object_or_404(Document, pk=self.kwargs['pk'])
        role = _get_project_role(doc.project, self.request.user)
        if role is None and doc.project.visibility != 'public':
            raise PermissionDenied("Nie masz dostępu do tego dokumentu.")
        return doc.chunks.all()


class ChunkUpdateView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def delete(self, request, pk):
        chunk = get_object_or_404(Chunk, pk=pk)
        role = _get_project_role(chunk.document.project, request.user)

        if role not in ('owner', 'admin', 'editor'):
            raise PermissionDenied("Nie masz uprawnień do usuwania chunków.")

        try:
            from documents.embeddings import get_chroma_client, get_or_create_collection
            client = get_chroma_client()
            collection = get_or_create_collection(client)
            collection.delete(ids=[str(chunk.pk)])
        except Exception:
            pass

        chunk.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, pk):
        chunk = get_object_or_404(Chunk, pk=pk)
        role  = _get_project_role(chunk.document.project, request.user)

        if role not in ('owner', 'admin', 'editor'):
            raise PermissionDenied("Nie masz uprawnień do edycji chunków.")

        new_text = request.data.get('text', '').strip()
        if not new_text:
            return Response({'error': 'Tekst nie może być pusty.'}, status=400)

        chunk.text       = new_text
        chunk.char_count = len(new_text)
        chunk.save(update_fields=['text', 'char_count'])

        try:
            reembed_chunk_task.delay(str(chunk.pk))
        except Exception:
            pass

        return Response(ChunkSerializer(chunk).data)


# ── Zmienione Wyszukiwanie Semantyczne (Wydzielone do Celery) ─────────────────
class SemanticSearchView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        query = request.data.get('query', '').strip()
        scope = request.data.get('scope', 'mine')
        n_results = min(int(request.data.get('n_results', 8)), 20)

        if not query:
            return Response({'error': 'Pole query jest wymagane.'}, status=400)
        if scope not in ['mine', 'public']:
            return Response({'error': 'Nieprawidłowy scope.'}, status=400)

        # Generowanie losowego identyfikatora zadania
        task_id = str(uuid.uuid4())
        
        # Ustawienie stanu początkowego w pamięci podręcznej Redis
        cache.set(f"search_res_{task_id}", {"status": "PENDING"}, timeout=300)

        # Natychmiastowe przekazanie wykonania do puli procesów Celery
        run_semantic_search_task.delay(task_id, request.user.id, query, scope, n_results)

        # Zwrócenie tokenu śledzącego do aplikacji klienckiej (Frontend React)
        return Response({'task_id': task_id, 'status': 'PENDING'}, status=status.HTTP_202_ACCEPTED)


# ── Nowy Endpoint do Sprawdzania Stanu Przetwarzania Wyszukiwania ─────────────
class SemanticSearchStatusView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        task_data = cache.get(f"search_res_{task_id}")
        
        if not task_data:
            return Response({'status': 'NOT_FOUND', 'error': 'Zadanie wygasło lub nie istnieje.'}, status=status.HTTP_404_NOT_FOUND)
            
        if task_data.get("status") == "FAILURE":
            return Response(task_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response(task_data, status=status.HTTP_200_OK)