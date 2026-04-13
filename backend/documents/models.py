import uuid
from django.db import models
from django.conf import settings


def document_upload_path(instance, filename):
    """Pliki lądują w media/documents/<project_uuid_or_id>/<doc_uuid>/<filename>"""
    return f"documents/{instance.project_id}/{instance.pk}/{filename}"


class Document(models.Model):
    class Status(models.TextChoices):
        PENDING    = 'pending',    'Oczekuje'
        PROCESSING = 'processing', 'Przetwarzanie'
        READY      = 'ready',      'Gotowy'
        ERROR      = 'error',      'Błąd'

    class FileType(models.TextChoices):
        PDF = 'pdf', 'PDF'
        TXT = 'txt', 'TXT'

    # Nietrywialny identyfikator (7.7)
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    project      = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='documents',
    )
    uploaded_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents',
    )

    file          = models.FileField(upload_to=document_upload_path)
    original_name = models.CharField(max_length=255)
    file_type     = models.CharField(max_length=10, choices=FileType.choices)
    file_size     = models.PositiveIntegerField(help_text='Rozmiar w bajtach')

    status        = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    error_message = models.TextField(blank=True, default='')

    uploaded_at   = models.DateTimeField(auto_now_add=True)
    processed_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.original_name} [{self.status}]"