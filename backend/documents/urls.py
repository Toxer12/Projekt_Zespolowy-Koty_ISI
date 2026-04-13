from django.urls import path
from documents.views import (
    DocumentUploadView,
    ProjectDocumentListView,
    DocumentDetailView,
)

urlpatterns = [
    path('',          DocumentUploadView.as_view(),        name='document-upload'),
    path('list/',     ProjectDocumentListView.as_view(),    name='document-list'),
    path('<uuid:pk>/', DocumentDetailView.as_view(),        name='document-detail'),
]