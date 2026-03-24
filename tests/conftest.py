"""
Shared fixtures for DocLens tests.
All external services (Qdrant, Gemini, Groq) are mocked so tests run
without API keys or a running Qdrant instance.
"""
import sys
import os
import pytest

# Make sure the backend package is importable from the tests directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# ---------------------------------------------------------------------------
# Patch external clients before any app module is imported
# ---------------------------------------------------------------------------

from unittest.mock import MagicMock, patch

@pytest.fixture(autouse=True)
def mock_clients(monkeypatch):
    """Replace all external API clients with mocks for every test."""
    mock_gemini = MagicMock()
    mock_groq = MagicMock()
    mock_qdrant = MagicMock()

    monkeypatch.setattr("app.core.clients.gemini_client", mock_gemini)
    monkeypatch.setattr("app.core.clients.groq_client", mock_groq)
    monkeypatch.setattr("app.core.clients.qdrant_client", mock_qdrant)

    # Also patch the names already imported into services
    monkeypatch.setattr("app.services.ingestion.gemini_client", mock_gemini)
    monkeypatch.setattr("app.services.ingestion.qdrant_client", mock_qdrant)
    monkeypatch.setattr("app.services.query.gemini_client", mock_gemini)
    monkeypatch.setattr("app.services.query.groq_client", mock_groq)
    monkeypatch.setattr("app.services.query.qdrant_client", mock_qdrant)

    return {
        "gemini": mock_gemini,
        "groq": mock_groq,
        "qdrant": mock_qdrant,
    }
