from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
PDF_MAGIC     = b'%PDF'


def _validate_pdf(file_bytes: bytes) -> str | None:
    """Zwraca komunikat błędu lub None jeśli OK."""
    if not file_bytes.startswith(PDF_MAGIC):
        return "Plik nie jest prawidłowym dokumentem PDF (brak sygnatury %PDF)."
    return None


def _validate_txt(file_bytes: bytes) -> str | None:
    try:
        file_bytes.decode('utf-8')
    except UnicodeDecodeError:
        return "Plik TXT zawiera znaki spoza UTF-8."
    return None


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def process_document(self, document_id: str):
    """
    Asynchroniczne przetwarzanie dokumentu (7.4):
    1. Pobierz dokument z bazy
    2. Ustaw status na PROCESSING
    3. Odczytaj bajty i zwaliduj zawartość (7.3)
    4. Zaktualizuj status na READY lub ERROR
    """
    from documents.models import Document  # import wewnątrz, żeby uniknąć circular

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

        # Walidacja rozmiaru (drugi raz po stronie serwera)
        if len(file_bytes) > MAX_FILE_SIZE:
            raise ValueError(f"Plik przekracza limit 10 MB.")

        # Walidacja zawartości
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

    except Exception as exc:
        logger.exception(f"Error processing document {document_id}: {exc}")
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            doc.status        = Document.Status.ERROR
            doc.error_message = "Wewnętrzny błąd przetwarzania. Spróbuj ponownie."
            doc.processed_at  = timezone.now()
            doc.save(update_fields=['status', 'error_message', 'processed_at'])