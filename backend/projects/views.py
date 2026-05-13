from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404

from users.auth import CookieJWTAuthentication
from projects.models import Project, Tag, ProjectMember, ProjectInvite, ProjectFavorite, ROLE_RANK
from projects.serializers import (
    ProjectSerializer, TagSerializer,
    ProjectMemberSerializer, ProjectInviteSerializer,
)

User = get_user_model()


def get_project_role(project, user):
    """Returns 'owner', 'admin', 'editor', 'viewer', or None."""
    if project.owner == user:
        return 'owner'
    try:
        return project.members.get(user=user).role
    except ProjectMember.DoesNotExist:
        return None


class PublicProjectPagination(PageNumberPagination):
    page_size             = 9
    page_size_query_param = 'page_size'
    max_page_size         = 50


# ── Projects ──────────────────────────────────────────────────────────────

class ProjectListCreateView(generics.ListCreateAPIView):
    serializer_class       = ProjectSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]
    filter_backends        = [filters.SearchFilter, filters.OrderingFilter]
    search_fields          = ['name', 'tags__name']
    ordering_fields        = ['created_at', 'name']

    def get_queryset(self):
        qs = Project.objects.filter(owner=self.request.user).prefetch_related('tags', 'members', 'favorited_by')
        visibility = self.request.query_params.get('visibility')
        if visibility in ('public', 'private'):
            qs = qs.filter(visibility=visibility)
        tag = self.request.query_params.get('tag')
        if tag:
            qs = qs.filter(tags__name=tag.strip().lower())
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class       = ProjectSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(
            Q(owner=user) | Q(members__user=user) | Q(visibility='public')
        ).prefetch_related('tags', 'members', 'favorited_by').distinct()

    def get_object(self):
        obj  = super().get_object()
        role = get_project_role(obj, self.request.user)

        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            if obj.owner != self.request.user:
                raise PermissionDenied("Tylko właściciel może edytować lub usuwać projekt.")

        if self.request.method == 'GET':
            if role is None and obj.visibility != 'public':
                raise PermissionDenied()

        return obj


class MemberProjectListView(generics.ListAPIView):
    serializer_class       = ProjectSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(
            members__user=self.request.user
        ).prefetch_related('tags', 'members', 'favorited_by').select_related('owner')


class PublicProjectListView(generics.ListAPIView):
    serializer_class       = ProjectSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]
    pagination_class       = PublicProjectPagination
    filter_backends        = [filters.OrderingFilter]
    ordering_fields        = ['created_at', 'name']

    def get_queryset(self):
        return Project.objects.filter(
            visibility='public'
        ).prefetch_related('tags', 'members', 'favorited_by').select_related('owner')


class FavoriteListView(generics.ListAPIView):
    """All projects favorited by the current user."""
    serializer_class       = ProjectSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(
            favorited_by__user=self.request.user
        ).prefetch_related('tags', 'members', 'favorited_by').select_related('owner')


class FavoriteToggleView(APIView):
    """POST to toggle favorite on a project. Returns { is_favorited: bool }."""
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def post(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        role    = get_project_role(project, request.user)

        # Allow any member or any user for public projects
        if role is None and project.visibility != 'public':
            raise PermissionDenied()

        favorite, created = ProjectFavorite.objects.get_or_create(
            user=request.user, project=project,
        )
        if not created:
            favorite.delete()
            return Response({'is_favorited': False})
        return Response({'is_favorited': True})


class TagListView(generics.ListAPIView):
    serializer_class       = TagSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]
    queryset               = Tag.objects.all().order_by('name')


# ── Members ───────────────────────────────────────────────────────────────

class ProjectMemberListView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        role    = get_project_role(project, request.user)
        if role is None and project.visibility != 'public':
            raise PermissionDenied()

        members = project.members.select_related('user', 'added_by').all()
        owner_entry = {
            'id':         None,
            'user_id':    project.owner.id,
            'user_name':  project.owner.name,
            'user_email': project.owner.email,
            'role':       'owner',
            'added_at':   None,
        }
        data = [owner_entry] + list(ProjectMemberSerializer(members, many=True).data)
        return Response(data)


class ProjectInviteCreateView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def post(self, request, project_id):
        project    = get_object_or_404(Project, pk=project_id)
        actor_role = get_project_role(project, request.user)

        if actor_role not in ('owner', 'admin'):
            raise PermissionDenied("Tylko właściciel lub admin może zapraszać użytkowników.")

        username = request.data.get('username', '').strip()
        role     = request.data.get('role', '')

        if not username:
            return Response({'error': 'Podaj nazwę użytkownika.'}, status=400)

        valid_roles = ['editor', 'viewer'] if actor_role == 'admin' else ['admin', 'editor', 'viewer']
        if role not in valid_roles:
            return Response({'error': f"Nieprawidłowa rola. Dostępne: {', '.join(valid_roles)}."}, status=400)

        try:
            invitee = User.objects.get(name=username)
        except User.DoesNotExist:
            return Response({'error': 'Użytkownik nie istnieje.'}, status=404)

        if invitee == request.user:
            return Response({'error': 'Nie możesz zaprosić siebie.'}, status=400)

        if get_project_role(project, invitee) is not None:
            return Response({'error': 'Użytkownik jest już członkiem projektu.'}, status=400)

        if ProjectInvite.objects.filter(project=project, invitee=invitee, status='pending').exists():
            return Response({'error': 'Użytkownik ma już oczekujące zaproszenie do tego projektu.'}, status=400)

        invite = ProjectInvite.objects.create(
            project=project, invited_by=request.user, invitee=invitee, role=role,
        )
        return Response(ProjectInviteSerializer(invite).data, status=201)


class ProjectMemberUpdateView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def _get_and_check(self, request, project_id, user_id):
        project    = get_object_or_404(Project, pk=project_id)
        actor_role = get_project_role(project, request.user)
        member     = get_object_or_404(ProjectMember, project=project, user_id=user_id)

        if ROLE_RANK.get(actor_role, -1) <= ROLE_RANK.get(member.role, -1):
            raise PermissionDenied("Nie możesz zarządzać użytkownikami o tej samej lub wyższej roli.")

        return project, member, actor_role

    def patch(self, request, project_id, user_id):
        project, member, actor_role = self._get_and_check(request, project_id, user_id)
        new_role = request.data.get('role', '')

        if new_role not in ('admin', 'editor', 'viewer'):
            return Response({'error': 'Nieprawidłowa rola.'}, status=400)

        if ROLE_RANK.get(new_role, -1) >= ROLE_RANK.get(actor_role, -1):
            return Response({'error': 'Nie możesz nadać roli wyższej lub równej swojej.'}, status=400)

        member.role = new_role
        member.save()
        return Response(ProjectMemberSerializer(member).data)

    def delete(self, request, project_id, user_id):
        _, member, _ = self._get_and_check(request, project_id, user_id)
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LeaveProjectView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def post(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        if project.owner == request.user:
            return Response({'error': 'Właściciel nie może opuścić projektu.'}, status=400)
        member = get_object_or_404(ProjectMember, project=project, user=request.user)
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Invites ───────────────────────────────────────────────────────────────

class InviteListView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        sent = ProjectInvite.objects.filter(
            invited_by=request.user
        ).select_related('project', 'invitee').order_by('-created_at')

        received = ProjectInvite.objects.filter(
            invitee=request.user
        ).select_related('project', 'invited_by').order_by('-created_at')

        return Response({
            'sent':     ProjectInviteSerializer(sent,     many=True).data,
            'received': ProjectInviteSerializer(received, many=True).data,
        })


class InviteRespondView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def post(self, request, pk):
        invite = get_object_or_404(ProjectInvite, pk=pk, invitee=request.user)

        if invite.status != 'pending':
            return Response({'error': 'To zaproszenie nie jest już aktywne.'}, status=400)

        action = request.data.get('action')
        if action not in ('accept', 'decline'):
            return Response({'error': 'Nieprawidłowa akcja. Użyj accept lub decline.'}, status=400)

        invite.responded_at = timezone.now()

        if action == 'accept':
            invite.status = 'accepted'
            invite.save()
            ProjectMember.objects.get_or_create(
                project  = invite.project,
                user     = invite.invitee,
                defaults = {'role': invite.role, 'added_by': invite.invited_by},
            )
        else:
            invite.status = 'declined'
            invite.save()

        return Response(ProjectInviteSerializer(invite).data)


class InviteCancelView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def post(self, request, pk):
        invite     = get_object_or_404(ProjectInvite, pk=pk)
        project    = invite.project
        actor_role = get_project_role(project, request.user)
        is_sender  = invite.invited_by == request.user
        has_rank   = ROLE_RANK.get(actor_role, -1) > ROLE_RANK.get(invite.role, -1)

        if not is_sender and not has_rank:
            raise PermissionDenied("Nie możesz anulować tego zaproszenia.")

        if invite.status != 'pending':
            return Response({'error': 'To zaproszenie nie jest już aktywne.'}, status=400)

        invite.status = 'cancelled'
        invite.save()
        return Response(ProjectInviteSerializer(invite).data)