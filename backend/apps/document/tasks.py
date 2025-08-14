from __future__ import annotations
import logging
from celery import shared_task
from django.db import transaction
from apps.document.models import Document, SmartChunk, ChunkingStatus
from apps.document.utils.chunker import chunk_text_and_embed
from apps.document.utils.parser import parse_file

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_document_chunks(self, doc_id: int) -> str:
    try:
        doc = Document.objects.get(pk=doc_id)

        # Skip if already processed
        if doc.chunking_done or doc.chunking_status == ChunkingStatus.DONE:
            logger.info("Document %s already processed; skipping.", doc_id)
            return "already_done"

        # Mark as processing
        doc.chunking_status = ChunkingStatus.PROCESSING
        doc.save(update_fields=["chunking_status"])

        file_path = doc.file.path
        text = parse_file(file_path)

        chunks = chunk_text_and_embed(text, doc.id)
        if not chunks:
            logger.warning("No chunks produced for document %s.", doc_id)

        SmartChunk.objects.bulk_create(chunks, ignore_conflicts=True, batch_size=1000)

        doc.extracted_text = text
        doc.chunking_done = True
        doc.chunking_status = ChunkingStatus.DONE
        doc.last_error = ""
        doc.save(update_fields=["extracted_text", "chunking_done", "chunking_status", "last_error"])

        logger.info("Chunking completed for document %s (%d chunks).", doc_id, len(chunks))
        return "ok"

    except Document.DoesNotExist:
        logger.error("Document %s not found for chunking.", doc_id)
        return "missing"

    except Exception as e:
        logger.exception("Failed to chunk document %s: %s", doc_id, e)
        try:
            Document.objects.filter(pk=doc_id).update(
                last_error=str(e),
                chunking_status=ChunkingStatus.ERROR
            )
        except Exception:
            pass
        return "error"
