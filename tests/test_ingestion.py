"""
Tests for the ingestion pipeline.

chunk_text is a pure function — tested without mocks.
extract_text_from_pdf and ingest_document use mocked external services.
"""
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# chunk_text — pure function, no external dependencies
# ---------------------------------------------------------------------------

def test_chunk_text_single_chunk():
    from app.services.ingestion import chunk_text

    text = " ".join([f"word{i}" for i in range(100)])  # 100 words
    chunks = chunk_text(text, page=1, filename="test.pdf")

    assert len(chunks) == 1
    assert chunks[0]["page"] == 1
    assert chunks[0]["filename"] == "test.pdf"
    assert chunks[0]["chunk_index"] == 0


def test_chunk_text_multiple_chunks():
    from app.services.ingestion import chunk_text

    # 1000 words -> should produce multiple 500-word chunks with 50 overlap
    text = " ".join([f"word{i}" for i in range(1000)])
    chunks = chunk_text(text, page=2, filename="test.pdf")

    assert len(chunks) > 1
    # Each chunk should have at most 500 words
    for chunk in chunks:
        assert len(chunk["text"].split()) <= 500


def test_chunk_text_overlap():
    from app.services.ingestion import chunk_text

    text = " ".join([f"word{i}" for i in range(600)])
    chunks = chunk_text(text, page=1, filename="test.pdf")

    # Second chunk should start 450 words in (500 - 50 overlap)
    first_chunk_words = chunks[0]["text"].split()
    second_chunk_words = chunks[1]["text"].split()

    # The last 50 words of chunk 0 should appear at the start of chunk 1
    assert first_chunk_words[-50:] == second_chunk_words[:50]


def test_chunk_text_empty_string():
    from app.services.ingestion import chunk_text

    chunks = chunk_text("", page=1, filename="test.pdf")
    assert chunks == []


# ---------------------------------------------------------------------------
# embed_text — uses mocked Gemini client
# ---------------------------------------------------------------------------

def test_embed_text_returns_vector(mock_clients):
    from app.services.ingestion import embed_text

    fake_vector = [0.1] * 3072
    mock_embedding = MagicMock()
    mock_embedding.values = fake_vector
    mock_clients["gemini"].models.embed_content.return_value.embeddings = [mock_embedding]

    result = embed_text("test text")

    assert result == fake_vector
    mock_clients["gemini"].models.embed_content.assert_called_once()


def test_embed_text_retries_on_rate_limit(mock_clients):
    from app.services.ingestion import embed_text

    fake_vector = [0.0] * 3072
    mock_embedding = MagicMock()
    mock_embedding.values = fake_vector

    # Fail twice with 429, succeed on third attempt
    mock_clients["gemini"].models.embed_content.side_effect = [
        Exception("429 RESOURCE_EXHAUSTED"),
        Exception("429 RESOURCE_EXHAUSTED"),
        MagicMock(embeddings=[mock_embedding]),
    ]

    with patch("time.sleep"):  # skip actual waiting
        result = embed_text("test text")

    assert result == fake_vector
    assert mock_clients["gemini"].models.embed_content.call_count == 3


def test_embed_text_raises_on_non_rate_limit_error(mock_clients):
    from app.services.ingestion import embed_text

    mock_clients["gemini"].models.embed_content.side_effect = ValueError("Bad input")

    with pytest.raises(ValueError, match="Bad input"):
        embed_text("test text")


# ---------------------------------------------------------------------------
# ingest_document — integration test with all services mocked
# ---------------------------------------------------------------------------

def test_ingest_document_success(mock_clients):
    from app.services.ingestion import ingest_document

    # Mock Qdrant collection check
    mock_clients["qdrant"].get_collections.return_value.collections = []

    # Mock PDF text extraction
    fake_pdf_bytes = b"%PDF-fake"
    fake_vector = [0.1] * 3072
    mock_embedding = MagicMock()
    mock_embedding.values = fake_vector
    mock_clients["gemini"].models.embed_content.return_value.embeddings = [mock_embedding]

    with patch("app.services.ingestion.extract_text_from_pdf") as mock_extract:
        mock_extract.return_value = [
            {"page": 1, "text": "This is page one content with enough words " * 20, "filename": "test.pdf"}
        ]
        result = ingest_document(fake_pdf_bytes, "test.pdf")

    assert result["status"] == "success"
    assert result["filename"] == "test.pdf"
    assert result["pages"] == 1
    assert result["chunks"] >= 1


def test_ingest_document_empty_pdf(mock_clients):
    from app.services.ingestion import ingest_document

    mock_clients["qdrant"].get_collections.return_value.collections = []

    with patch("app.services.ingestion.extract_text_from_pdf") as mock_extract:
        mock_extract.return_value = []
        result = ingest_document(b"fake", "empty.pdf")

    assert result["status"] == "error"
    assert "No text" in result["message"]
