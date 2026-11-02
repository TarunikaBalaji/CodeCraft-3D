import pymupdf
import pytest

from core.document_processor import (
    DocumentProcessingError,
    process_pdf,
)


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a temporary two-page PDF for testing."""

    pdf_path = tmp_path / "sample_regulation.pdf"

    document = pymupdf.open()

    page1 = document.new_page()
    page1.insert_text(
        (72, 72),
        "Tamil Nadu Building Regulations"
    )

    page2 = document.new_page()
    page2.insert_text(
        (72, 72),
        "Maximum building height is subject to applicable rules."
    )

    document.save(pdf_path)
    document.close()

    return pdf_path


def test_extracts_text_from_multiple_pages(sample_pdf):
    result = process_pdf(sample_pdf)

    assert result["processing_status"] == "SUCCESS"
    assert result["page_count"] == 2

    assert "Tamil Nadu Building Regulations" in (
        result["pages"][0]["text"]
    )

    assert "Maximum building height" in (
        result["pages"][1]["text"]
    )


def test_preserves_page_numbers(sample_pdf):
    result = process_pdf(sample_pdf)

    assert result["pages"][0]["page_number"] == 1
    assert result["pages"][1]["page_number"] == 2


def test_returns_document_metadata(sample_pdf):
    result = process_pdf(sample_pdf)

    assert result["document_id"] == "sample_regulation"
    assert result["file_name"] == "sample_regulation.pdf"
    assert isinstance(result["metadata"], dict)


def test_detects_empty_pages(tmp_path):
    pdf_path = tmp_path / "empty_pages.pdf"

    document = pymupdf.open()
    document.new_page()
    document.new_page()
    document.save(pdf_path)
    document.close()

    result = process_pdf(pdf_path)

    assert result["page_count"] == 2
    assert result["empty_pages"] == [1, 2]
    assert result["requires_ocr"] is True
    assert result["processing_status"] == "NO_EXTRACTABLE_TEXT"


def test_invalid_pdf_is_rejected(tmp_path):
    invalid_path = tmp_path / "invalid.pdf"
    invalid_path.write_bytes(b"This is not a PDF")

    with pytest.raises(DocumentProcessingError):
        process_pdf(invalid_path)


def test_non_pdf_file_is_rejected(tmp_path):
    text_path = tmp_path / "document.txt"
    text_path.write_text("This is a text file.")

    with pytest.raises(DocumentProcessingError):
        process_pdf(text_path)


def test_missing_file_is_rejected(tmp_path):
    missing_path = tmp_path / "missing.pdf"

    with pytest.raises(DocumentProcessingError):
        process_pdf(missing_path)