from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from users.auth import CookieJWTAuthentication
from projects.models import Project, ProjectMember
from documents.models import Document, Chunk
from documents.serializers import DocumentUploadSerializer, DocumentSerializer, ChunkSerializer
from documents.tasks import process_document


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
        # All roles (including viewer) can list documents
        # Public project visitors can also list documents
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
            from documents.embeddings import (
                get_chroma_client,
                get_or_create_collection,
            )

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

        # Re-embed this single chunk in Chroma inline
        try:
            from documents.embeddings import (
                embed_texts, get_chroma_client, get_or_create_collection,
            )
            doc        = chunk.document
            embeddings = embed_texts([new_text])
            client     = get_chroma_client()
            collection = get_or_create_collection(client)
            collection.upsert(
                ids        = [str(chunk.pk)],
                documents  = [new_text],
                embeddings = embeddings,
                metadatas  = [{
                    'document_id': str(doc.pk),
                    'project_id':  str(doc.project_id),
                    'chunk_index': chunk.index,
                    'chunk_type':  chunk.chunk_type,
                    'file_name':   doc.original_name,
                }],
            )
        except Exception:
            pass  # text is saved — embedding failure is non-fatal

        return Response(ChunkSerializer(chunk).data)


class SemanticSearchView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        query = request.data.get('query', '').strip()
        scope = request.data.get('scope', 'mine')
        n_results = min(int(request.data.get('n_results', 8)), 20)

        if not query:
            return Response({'error': 'Pole query jest wymagane.'}, status=400)

        try:
            if scope == 'mine':
                results = self._search_my_projects(request.user, query, n_results)
            elif scope == 'public':
                results = self._search_public(query, n_results)
            else:
                return Response({'error': 'Nieprawidłowy scope.'}, status=400)
        except Exception as e:
            return Response({'error': f'Błąd wyszukiwania: {str(e)}'}, status=500)

        return Response({'results': results, 'query': query, 'total': len(results)})

    def _get_project_ids(self, queryset):
        return [str(pk) for pk in queryset.values_list('pk', flat=True)]

    def _search_my_projects(self, user, query, n_results):
        """9.1 — szuka we wszystkich projektach zalogowanego użytkownika."""
        project_ids = self._get_project_ids(Project.objects.filter(owner=user))
        if not project_ids:
            return []
        return self._run_search(query, project_ids, n_results)

    def _search_public(self, query, n_results):
        """9.2 — szuka w dokumentach wszystkich publicznych projektów."""
        project_ids = self._get_project_ids(Project.objects.filter(visibility='public'))
        if not project_ids:
            return []
        return self._run_search(query, project_ids, n_results)

    def _run_search(self, query, project_ids, n_results):
        from documents.embeddings import embed_texts, get_chroma_client, get_or_create_collection

        query_embedding = embed_texts([query])[0]
        client = get_chroma_client()
        collection = get_or_create_collection(client)

        count = collection.count()
        if count == 0:
            return []

        where = {"project_id": {"$in": project_ids}}
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, count),
                where=where,
                include=['documents', 'metadatas', 'distances'],
            )
        except Exception:
            return []

        return self._format_results(results)

    def _format_results(self, raw):
        """9.3 — ranking po score podobieństwa."""
        items = []
        for text, meta, dist in zip(
                raw['documents'][0],
                raw['metadatas'][0],
                raw['distances'][0],
        ):
            score = round((2 - dist) / 2, 4)
            items.append({
                'text': text,
                'score': score,
                'file_name': meta.get('file_name', ''),
                'document_id': meta.get('document_id', ''),
                'chunk_index': meta.get('chunk_index', 0),
                'project_id': meta.get('project_id', ''),
            })

        items.sort(key=lambda x: x['score'], reverse=True)
        return items