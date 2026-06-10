from django.contrib import admin
from documents.models import Document, Chunk


class ChunkInline(admin.TabularInline):
    model           = Chunk
    extra           = 0
    fields          = ('index', 'chunk_type', 'char_count', 'text')
    readonly_fields = ('index', 'chunk_type', 'char_count', 'text')
    can_delete      = False
    max_num         = 0
    show_change_link = True


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display    = ('original_name', 'project', 'file_type', 'file_size_kb',
                       'status', 'embedding_status', 'uploaded_at')
    list_filter     = ('status', 'embedding_status', 'file_type', 'chunk_type')
    search_fields   = ('original_name', 'project__name', 'uploaded_by__email')
    readonly_fields = ('id', 'uploaded_at', 'processed_at', 'embedded_at')
    inlines         = [ChunkInline]

    def file_size_kb(self, obj):
        return f"{obj.file_size // 1024} KB" if obj.file_size >= 1024 else f"{obj.file_size} B"
    file_size_kb.short_description = 'Rozmiar'


@admin.register(Chunk)
class ChunkAdmin(admin.ModelAdmin):
    list_display    = ('document', 'index', 'chunk_type', 'char_count', 'created_at')
    list_filter     = ('chunk_type',)
    search_fields   = ('document__original_name', 'text')
    readonly_fields = ('id', 'created_at')