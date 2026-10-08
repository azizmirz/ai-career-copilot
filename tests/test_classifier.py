# tests/test_classifier.py

from unittest.mock import MagicMock, patch

from app.tools.classifier import classify_document


def make_fake_groq_response(content: str):
    """Groq API-nin cavab strukturunu imitasiya edir."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=content))]
    return mock_response


@patch("app.tools.classifier.client.chat.completions.create")
def test_classify_document_returns_cv(mock_create):
    mock_create.return_value = make_fake_groq_response("CV")
    result = classify_document("some resume text...")
    assert result == "CV"


@patch("app.tools.classifier.client.chat.completions.create")
def test_classify_document_returns_jd(mock_create):
    mock_create.return_value = make_fake_groq_response("JD")
    result = classify_document("some job posting text...")
    assert result == "JD"


@patch("app.tools.classifier.client.chat.completions.create")
def test_classify_document_handles_extra_words(mock_create):
    """LLM tək söz əvəzinə cümlə qaytarsa belə düzgün parse olunmalıdır."""
    mock_create.return_value = make_fake_groq_response("This is a JD document.")
    result = classify_document("text")
    assert result == "JD"
