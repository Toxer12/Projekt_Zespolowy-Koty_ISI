from rest_framework import serializers
from documents.models import Document

ALLOWED_EXTENSIONS = {'pdf', 'txt'}
ALLOWED_CONTENT_TYPES = {
    'application/pdf',
    'text/plain',
    # Niektóre przeglądarki wysyłają TXT jako octet-stream
    'application/octet-stream',
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Używany przy POST — przyjmuje plik i project."""
    file       = serializers.FileField()
    project_id = serializers.IntegerField(write_only=True)

    class Meta:
        model  = Document
        fields = ('file', 'project_id')

    def validate_file(self, file):
        # Walidacja rozszerzenia (7.3)
        ext = file.name.rsplit('.', 1)[-1].lower() if '.' in file.name else ''
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Dozwolone formaty: PDF i TXT. Przesłano: .{ext or 'brak rozszerzenia'}"
            )

        # Walidacja rozmiaru (7.3)
        if file.size > MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"Plik jest za duży ({file.size // (1024*1024)} MB). Limit: 10 MB."
            )

        return file

    def create(self, validated_data):
        file       = validated_data['file']
        project_id = validated_data['project_id']
        ext        = file.name.rsplit('.', 1)[-1].lower()

        doc = Document(
            project_id    = project_id,
            uploaded_by   = self.context['request'].user,
            file          = file,
            original_name = file.name,
            file_type     = ext,
            file_size     = file.size,
            status        = Document.Status.PENDING,
        )
        doc.save()
        return doc


class DocumentSerializer(serializers.ModelSerializer):
    """Używany przy GET — pełny widok dokumentu."""
    file_url = serializers.SerializerMethodField()

    class Meta:
        model  = Document
        fields = (
            'id', 'original_name', 'file_type', 'file_size',
            'status', 'error_message', 'file_url',
            'uploaded_at', 'processed_at',
        )

    def get_file_url(self, obj):
        if obj.status != Document.Status.READY:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.file.url) if request else obj.file.url