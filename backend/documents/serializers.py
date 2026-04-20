from rest_framework import serializers
from documents.models import Document, Chunk

ALLOWED_EXTENSIONS  = {'pdf', 'txt'}
MAX_FILE_SIZE       = 10 * 1024 * 1024


class ChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Chunk
        fields = ('id', 'index', 'text', 'char_count', 'chunk_type', 'created_at')


class DocumentUploadSerializer(serializers.ModelSerializer):
    file       = serializers.FileField()
    project_id = serializers.IntegerField(write_only=True)
    chunk_type = serializers.ChoiceField(
        choices=['fixed', 'sentence'],
        default='sentence',
        required=False,
    )

    class Meta:
        model  = Document
        fields = ('file', 'project_id', 'chunk_type')

    def validate_file(self, file):
        ext = file.name.rsplit('.', 1)[-1].lower() if '.' in file.name else ''
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Dozwolone formaty: PDF i TXT. Przesłano: .{ext or 'brak rozszerzenia'}"
            )
        if file.size > MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"Plik jest za duży ({file.size // (1024*1024)} MB). Limit: 10 MB."
            )
        return file

    def create(self, validated_data):
        file       = validated_data['file']
        project_id = validated_data['project_id']
        chunk_type = validated_data.get('chunk_type', 'sentence')
        ext        = file.name.rsplit('.', 1)[-1].lower()

        doc = Document(
            project_id    = project_id,
            uploaded_by   = self.context['request'].user,
            file          = file,
            original_name = file.name,
            file_type     = ext,
            file_size     = file.size,
            status        = Document.Status.PENDING,
            chunk_type    = chunk_type,
        )
        doc.save()
        return doc


class DocumentSerializer(serializers.ModelSerializer):
    file_url       = serializers.SerializerMethodField()
    chunk_count    = serializers.SerializerMethodField()

    class Meta:
        model  = Document
        fields = (
            'id', 'original_name', 'file_type', 'file_size',
            'status', 'error_message', 'file_url',
            'embedding_status', 'embedding_error', 'chunk_type',
            'chunk_count', 'uploaded_at', 'processed_at', 'embedded_at',
        )

    def get_file_url(self, obj):
        if obj.status != Document.Status.READY:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.file.url) if request else obj.file.url

    def get_chunk_count(self, obj):
        return obj.chunks.count()