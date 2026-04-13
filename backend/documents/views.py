from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, NotFound
from django.shortcuts import get_object_or_404

from users.auth import CookieJWTAuthentication
from projects.models import Project
from documents.models import Document
from documents.serializers import DocumentUploadSerializer, DocumentSerializer
from documents.tasks import process_document


class DocumentUploadView(APIView):
    """
    POST /api/documents/
    Przyjmuje multipart/form-data: { file, project_id }
    Zwraca 202 Accepted i odpala Celery task (7.4).
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def post(self, request):
        serializer = DocumentUploadSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        # Sprawdź czy projekt należy do usera
        project_id = serializer.validated_data['project_id']
        project = get_object_or_404(Project, pk=project_id)
        if project.owner != request.user:
            raise PermissionDenied("Nie masz dostępu do tego projektu.")

        doc = serializer.save()

        # Odpal asynchroniczne przetwarzanie (7.4)
        process_document.delay(str(doc.pk))

        return Response(
            DocumentSerializer(doc, context={'request': request}).data,
            status=status.HTTP_202_ACCEPTED,
        )


class ProjectDocumentListView(generics.ListAPIView):
    """
    GET /api/documents/?project_id=<id>
    Lista dokumentów projektu należącego do zalogowanego usera.
    """
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

        return Document.objects.filter(project=project)


class DocumentDetailView(APIView):
    """
    GET    /api/documents/<uuid>/  — status dokumentu (polling)
    DELETE /api/documents/<uuid>/  — usuń dokument (7.5 CRUD)
    """
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
        # Usuń plik z dysku
        doc.file.delete(save=False)
        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)