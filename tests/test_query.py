"""
Tests for the query pipeline.

Tests cover: per-document answer generation, theme identification,
and the full process_query orchestration — all with mocked services.
"""
import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# get_all_documents
# ---------------------------------------------------------------------------

def test_get_all_documents_returns_unique_filenames(mock_clients):
    from app.services.query import get_all_documents

    point_a = MagicMock()
    point_a.payload = {"filename": "paper1.pdf"}
    point_b = MagicMock()
    point_b.payload = {"filename": "paper2.pdf"}
    point_c = MagicMock()
    point_c.payload = {"filename": "paper1.pdf"}  # duplicate

    mock_clients["qdrant"].scroll.return_value = ([point_a, point_b, point_c], None)

    docs = get_all_documents()

    assert set(docs) == {"paper1.pdf", "paper2.pdf"}
    assert len(docs) == 2


def test_get_all_documents_empty_collection(mock_clients):
    from app.services.query import get_all_documents

    mock_clients["qdrant"].scroll.return_value = ([], None)

    docs = get_all_documents()
    assert docs == []


# ---------------------------------------------------------------------------
# answer_per_document
# ---------------------------------------------------------------------------

def test_answer_per_document_no_chunks(mock_clients):
    from app.services.query import answer_per_document

    result = answer_per_document("What is RAG?", chunks=[], filename="paper.pdf")

    assert result["filename"] == "paper.pdf"
    assert result["answer"] == "No relevant content found"
    assert result["citation"] == "N/A"
    # LLM should not be called when there are no chunks
    mock_clients["groq"].chat.completions.create.assert_not_called()


def test_answer_per_document_parses_llm_response(mock_clients):
    from app.services.query import answer_per_document

    mock_response = MagicMock()
    mock_response.choices[0].message.content = (
        "ANSWER: RAG combines retrieval and generation.\nCITATION: Page 3"
    )
    mock_clients["groq"].chat.completions.create.return_value = mock_response

    chunks = [{"text": "RAG stands for Retrieval Augmented Generation.", "page": 3, "chunk_index": 0}]
    result = answer_per_document("What is RAG?", chunks, "paper.pdf")

    assert result["answer"] == "RAG combines retrieval and generation."
    assert result["citation"] == "Page 3"
    assert result["filename"] == "paper.pdf"


# ---------------------------------------------------------------------------
# identify_themes
# ---------------------------------------------------------------------------

def test_identify_themes_skips_empty_answers(mock_clients):
    from app.services.query import identify_themes

    doc_answers = [
        {"filename": "a.pdf", "answer": "No relevant content found", "citation": "N/A"},
        {"filename": "b.pdf", "answer": "No relevant content found", "citation": "N/A"},
    ]

    result = identify_themes("What is RAG?", doc_answers)

    assert "No common themes" in result
    mock_clients["groq"].chat.completions.create.assert_not_called()


def test_identify_themes_calls_llm_with_relevant_answers(mock_clients):
    from app.services.query import identify_themes

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "THEME 1 - Retrieval:\nBoth papers discuss retrieval.\nSupporting documents: a.pdf, b.pdf"
    mock_clients["groq"].chat.completions.create.return_value = mock_response

    doc_answers = [
        {"filename": "a.pdf", "answer": "RAG uses dense retrieval.", "citation": "Page 2"},
        {"filename": "b.pdf", "answer": "FAISS enables fast retrieval.", "citation": "Page 5"},
    ]

    result = identify_themes("What is retrieval?", doc_answers)

    assert "THEME 1" in result
    mock_clients["groq"].chat.completions.create.assert_called_once()


# ---------------------------------------------------------------------------
# process_query — full pipeline
# ---------------------------------------------------------------------------

def test_process_query_no_documents(mock_clients):
    from app.services.query import process_query

    mock_clients["qdrant"].scroll.return_value = ([], None)

    result = process_query("What is RAG?")

    assert "error" in result
    assert "No documents" in result["error"]


def test_process_query_returns_full_structure(mock_clients):
    from app.services.query import process_query

    # Mock documents in Qdrant
    point = MagicMock()
    point.payload = {"filename": "paper.pdf"}
    mock_clients["qdrant"].scroll.return_value = ([point], None)

    # Mock query embedding
    fake_vector = [0.1] * 3072
    mock_embed = MagicMock()
    mock_embed.embeddings[0].values = fake_vector
    mock_clients["gemini"].models.embed_content.return_value = mock_embed

    # Mock vector search results
    mock_hit = MagicMock()
    mock_hit.payload = {"text": "RAG combines retrieval with generation.", "page": 1, "chunk_index": 0}
    mock_hit.score = 0.95
    mock_clients["qdrant"].query_points.return_value.points = [mock_hit]

    # Mock LLM responses
    answer_response = MagicMock()
    answer_response.choices[0].message.content = "ANSWER: RAG is effective.\nCITATION: Page 1"

    theme_response = MagicMock()
    theme_response.choices[0].message.content = "THEME 1 - RAG:\nCore theme.\nSupporting documents: paper.pdf"

    mock_clients["groq"].chat.completions.create.side_effect = [answer_response, theme_response]

    result = process_query("What is RAG?")

    assert result["query"] == "What is RAG?"
    assert len(result["doc_answers"]) == 1
    assert result["doc_answers"][0]["filename"] == "paper.pdf"
    assert "themes" in result


# ---------------------------------------------------------------------------
# Pydantic schema validation
# ---------------------------------------------------------------------------

def test_query_request_rejects_empty_string():
    from app.models.schemas import QueryRequest
    import pydantic

    with pytest.raises(pydantic.ValidationError):
        QueryRequest(query="   ")


def test_query_request_strips_whitespace():
    from app.models.schemas import QueryRequest

    req = QueryRequest(query="  what is RAG?  ")
    assert req.query == "what is RAG?"
