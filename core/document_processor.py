from pathlib import Path
from typing import Any

import pymupdf


class DocumentProcessingError(Exception):
    """Raised when a PDF cannot be processed."""


def process_pdf(file_path: str | Path) -> dict[str, Any]:
    """
    Extract page-aware text and metadata from a PDF.

    OCR is not performed. Pages without extractable text
    are identified for future OCR processing.
    """

    path = Path(file_path)

    if not path.exists():
        raise DocumentProcessingError(
            f"File does not exist: {path}"
        )

    if not path.is_file():
        raise DocumentProcessingError(
            f"Path is not a file: {path}"
        )

    if path.suffix.lower() != ".pdf":
        raise DocumentProcessingError(
            "Only PDF files are supported."
        )

    try:
        document = pymupdf.open(path)
    except Exception as exc:
        raise DocumentProcessingError(
            "Unable to open PDF. The file may be invalid or corrupted."
        ) from exc

    try:
        if not document.is_pdf:
            raise DocumentProcessingError(
                "The uploaded file is not a valid PDF."
            )

        pages = []
        empty_pages = []

        for page_index, page in enumerate(document):
            text = page.get_text("text").strip()

            page_data = {
                "page_number": page_index + 1,
                "text": text,
                "character_count": len(text),
                "has_text": bool(text),
            }

            pages.append(page_data)

            if not text:
                empty_pages.append(page_index + 1)

        metadata = document.metadata or {}

        extracted_text = "\n\n".join(
            page["text"]
            for page in pages
            if page["text"]
        )

        return {
            "document_id": path.stem,
            "file_name": path.name,
            "file_path": str(path.resolve()),
            "page_count": len(document),
            "metadata": metadata,
            "pages": pages,
            "extracted_text": extracted_text,
            "empty_pages": empty_pages,
            "requires_ocr": len(empty_pages) > 0,
            "processing_status": (
                "SUCCESS" if extracted_text else "NO_EXTRACTABLE_TEXT"
            ),
        }

    finally:
        document.close()