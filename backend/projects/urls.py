from django.urls import path
from projects.views import (
    ProjectListCreateView,
    ProjectDetailView,
    PublicProjectListView,
    TagListView,
)

urlpatterns = [
    path('',        ProjectListCreateView.as_view(), name='project-list-create'),
    path('<int:pk>/', ProjectDetailView.as_view(),   name='project-detail'),
    path('public/', PublicProjectListView.as_view(), name='project-public'),
    path('tags/',   TagListView.as_view(),           name='tag-list'),
]