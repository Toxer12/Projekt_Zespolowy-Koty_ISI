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
            collection.update(
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