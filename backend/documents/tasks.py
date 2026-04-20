from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024
PDF_MAGIC     = b'%PDF'


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    import io
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        return '\n'.join(
            page.extract_text() or '' for page in reader.pages
        ).strip()
    except Exception as e:
        raise ValueError(f"Nie udało się odczytać tekstu z PDF: {e}")


def _validate_pdf(file_bytes: bytes) -> str | None:
    if not file_bytes.startswith(PDF_MAGIC):
        return "Plik nie jest prawidłowym dokumentem PDF (brak sygnatury %PDF)."
    return None


def _validate_txt(file_bytes: bytes) -> str | None:
    try:
        file_bytes.decode('utf-8')
    except UnicodeDecodeError:
        return "Plik TXT zawiera znaki spoza UTF-8."
    return None


# ── Task 1: Walidacja pliku ────────────────────────────────────────────────
@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def process_document(self, document_id: str):
    from documents.models import Document

    try:
        doc = Document.objects.get(pk=document_id)
    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
        return

    doc.status = Document.Status.PROCESSING
    doc.save(update_fields=['status'])

    try:
        doc.file.open('rb')
        file_bytes = doc.file.read()
        doc.file.close()

        if len(file_bytes) > MAX_FILE_SIZE:
            raise ValueError("Plik przekracza limit 10 MB.")

        if doc.file_type == Document.FileType.PDF:
            error = _validate_pdf(file_bytes)
        elif doc.file_type == Document.FileType.TXT:
            error = _validate_txt(file_bytes)
        else:
            error = f"Nieobsługiwany typ pliku: {doc.file_type}"

        if error:
            doc.status        = Document.Status.ERROR
            doc.error_message = error
        else:
            doc.status        = Document.Status.READY
            doc.error_message = ''

        doc.processed_at = timezone.now()
        doc.save(update_fields=['status', 'error_message', 'processed_at'])

        if doc.status == Document.Status.READY:
            chunk_and_embed_document.delay(document_id)

    except Exception as exc:
        logger.exception(f"Error processing document {document_id}: {exc}")
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            doc.status        = Document.Status.ERROR
            doc.error_message = "Wewnętrzny błąd przetwarzania."
            doc.processed_at  = timezone.now()
            doc.save(update_fields=['status', 'error_message', 'processed_at'])


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def chunk_and_embed_document(self, document_id: str):
    from documents.models import Document, Chunk
    from documents.chunker import chunk_text
    from documents.embeddings import embed_texts, store_chunks_in_chroma

    try:
        doc = Document.objects.get(pk=document_id)
    except Document.DoesNotExist:
        return

    doc.embedding_status = Document.EmbeddingStatus.CHUNKING
    doc.save(update_fields=['embedding_status'])

    try:
        doc.file.open('rb')
        file_bytes = doc.file.read()
        doc.file.close()

        if doc.file_type == 'pdf':
            text = _extract_text_from_pdf(file_bytes)
        else:
            text = file_bytes.decode('utf-8')

        if not text.strip():
            doc.embedding_status = Document.EmbeddingStatus.ERROR
            doc.embedding_error  = "Dokument nie zawiera tekstu do przetworzenia."
            doc.save(update_fields=['embedding_status', 'embedding_error'])
            return

        doc.chunks.all().delete()

        method = doc.chunk_type or 'sentence'
        raw_chunks = chunk_text(text, method=method)

        chunk_objs = Chunk.objects.bulk_create([
            Chunk(
                document   = doc,
                index      = c.index,
                text       = c.text,
                char_count = c.char_count,
                chunk_type = c.chunk_type,
            )
            for c in raw_chunks
        ])

        doc.embedding_status = Document.EmbeddingStatus.EMBEDDING
        doc.save(update_fields=['embedding_status'])

        texts      = [c.text for c in chunk_objs]
        embeddings = embed_texts(texts)

        metadatas = [
            {
                'document_id': str(doc.pk),
                'project_id':  str(doc.project_id),
                'chunk_index': c.index,
                'chunk_type':  c.chunk_type,
                'file_name':   doc.original_name,
            }
            for c in chunk_objs
        ]

        store_chunks_in_chroma(
            document_id = str(doc.pk),
            chunk_ids   = [str(c.pk) for c in chunk_objs],
            texts       = texts,
            embeddings  = embeddings,
            metadatas   = metadatas,
        )

        doc.embedding_status = Document.EmbeddingStatus.DONE
        doc.embedding_error  = ''
        doc.embedded_at      = timezone.now()
        doc.save(update_fields=['embedding_status', 'embedding_error', 'embedded_at'])

        logger.info(f"Dokument {document_id} — {len(chunk_objs)} chunków, embeddingi gotowe.")

    except Exception as exc:
        logger.exception(f"Błąd chunk/embed dla {document_id}: {exc}")
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            doc.embedding_status = Document.EmbeddingStatus.ERROR
            doc.embedding_error  = f"Błąd generowania embeddingów: {str(exc)}"
            doc.save(update_fields=['embedding_status', 'embedding_error'])