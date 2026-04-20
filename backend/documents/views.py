from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from users.auth import CookieJWTAuthentication
from projects.models import Project
from documents.models import Document, Chunk
from documents.serializers import DocumentUploadSerializer, DocumentSerializer, ChunkSerializer
from documents.tasks import process_document


class DocumentUploadView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        project_id = serializer.validated_data['project_id']
        project    = get_object_or_404(Project, pk=project_id)
        if project.owner != request.user:
            raise PermissionDenied("Nie masz dostępu do tego projektu.")

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
        if project.owner != self.request.user:
            raise PermissionDenied("Nie masz dostępu do tego projektu.")
        return Document.objects.filter(project=project).prefetch_related('chunks')


class DocumentDetailView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def _get_doc(self, request, pk):
        doc = get_object_or_404(Document, pk=pk)
        if doc.project.owner != request.user:
            raise PermissionDenied("Nie masz dostępu do tego dokumentu.")
        return doc

    def get(self, request, pk):
        doc = self._get_doc(request, pk)
        return Response(DocumentSerializer(doc, context={'request': request}).data)

    def delete(self, request, pk):
        doc = self._get_doc(request, pk)
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
        doc = get_object_or_404(Document, pk=self.kwargs['pk'])
        if doc.project.owner != self.request.user:
            raise PermissionDenied("Nie masz dostępu do tego dokumentu.")
        return doc.chunks.all()