from django.urls import path
from projects.views import (
    ProjectListCreateView, ProjectDetailView,
    PublicProjectListView, MemberProjectListView, TagListView,
    ProjectMemberListView, ProjectInviteCreateView,
    ProjectMemberUpdateView, LeaveProjectView,
    InviteListView, InviteRespondView, InviteCancelView,
)

urlpatterns = [
    # Projects — specific paths must come before <int:pk>
    path('projects/',                                          ProjectListCreateView.as_view()),
    path('projects/public/',                                   PublicProjectListView.as_view()),
    path('projects/shared/',                                   MemberProjectListView.as_view()),
    path('projects/<int:pk>/',                                 ProjectDetailView.as_view()),

    # Members
    path('projects/<int:project_id>/members/',                 ProjectMemberListView.as_view()),
    path('projects/<int:project_id>/members/invite/',          ProjectInviteCreateView.as_view()),
    path('projects/<int:project_id>/members/<int:user_id>/',   ProjectMemberUpdateView.as_view()),
    path('projects/<int:project_id>/leave/',                   LeaveProjectView.as_view()),

    # Invites
    path('invites/',                                           InviteListView.as_view()),
    path('invites/<int:pk>/respond/',                          InviteRespondView.as_view()),
    path('invites/<int:pk>/cancel/',                           InviteCancelView.as_view()),

    # Tags
    path('tags/',                                              TagListView.as_view()),
]