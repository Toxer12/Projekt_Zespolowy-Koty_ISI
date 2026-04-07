from rest_framework import generics, filters, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from users.auth import CookieJWTAuthentication
from projects.models import Project, Tag
from projects.serializers import ProjectSerializer, TagSerializer


class ProjectListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/projects/          – lista projektów zalogowanego usera
    POST /api/projects/          – utwórz nowy projekt
    """
    serializer_class       = ProjectSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]
    filter_backends        = [filters.SearchFilter, filters.OrderingFilter]
    search_fields          = ['name', 'tags__name']
    ordering_fields        = ['created_at', 'name']

    def get_queryset(self):
        qs = Project.objects.filter(owner=self.request.user).prefetch_related('tags')

        # ?visibility=public / private
        visibility = self.request.query_params.get('visibility')
        if visibility in ('public', 'private'):
            qs = qs.filter(visibility=visibility)

        # ?tag=python
        tag = self.request.query_params.get('tag')
        if tag:
            qs = qs.filter(tags__name=tag.strip().lower())

        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/projects/<id>/   – szczegóły projektu
    PATCH  /api/projects/<id>/   – edytuj projekt
    DELETE /api/projects/<id>/   – usuń projekt
    """
    serializer_class       = ProjectSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user).prefetch_related('tags')

    def get_object(self):
        obj = super().get_object()
        if obj.owner != self.request.user:
            raise PermissionDenied("Nie masz dostępu do tego projektu.")
        return obj


class PublicProjectListView(generics.ListAPIView):
    """
    GET /api/projects/public/    – publiczne projekty wszystkich userów (bez auth)
    """
    serializer_class   = ProjectSerializer
    permission_classes = [AllowAny]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['name', 'tags__name']
    ordering_fields    = ['created_at', 'name']

    def get_queryset(self):
        return Project.objects.filter(
            visibility='public'
        ).prefetch_related('tags').select_related('owner')


class TagListView(generics.ListAPIView):
    """
    GET /api/projects/tags/      –  tagi (do autocomplete w formularwszystkiezu)
    """
    serializer_class   = TagSerializer
    permission_classes = [AllowAny]
    queryset           = Tag.objects.all().order_by('name')