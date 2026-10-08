# tests/test_api.py

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.session_store import save_session
from app.main import app

client = TestClient(app)


def test_health_check():
    """Backend-in çalışdığını yoxlayır."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_cv_rejects_non_pdf():
    """PDF olmayan fayl rədd edilməlidir."""
    response = client.post(
        "/v1/cv/upload",
        files={"file": ("cv.txt", b"plain text", "text/plain")},
        data={"session_id": "test-session"},
    )
    assert response.status_code == 400


@patch("app.api.routes.store_cv_chunks")
@patch("app.api.routes.parse_cv_with_llm")
@patch("app.api.routes.classify_document")
@patch("app.api.routes.get_cv_text")
def test_upload_cv_success(mock_get_text, mock_classify, mock_parse, mock_store):
    """
    Düzgün CV PDF göndərilərsə, parse edilib session yaranmalıdır.
    LLM və Qdrant çağırışları mock edilib.
    """
    mock_get_text.return_value = "fake cv text"
    mock_classify.return_value = "CV"
    mock_parse.return_value = {
        "name": "Test Candidate",
        "summary": "Engineer",
        "skills": ["Python"],
        "experience": [],
        "education": [],
        "projects": [],
        "extra_sections": {},
    }
    mock_store.return_value = None

    response = client.post(
        "/v1/cv/upload",
        files={"file": ("cv.pdf", b"%PDF-1.4 fake content", "application/pdf")},
        data={"session_id": "test-session-123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["cv_owner"] == "Test Candidate"
    assert data["session_id"] == "test-session-123"
    assert data["chunks_count"] == 2  # summary + skills


@patch("app.api.routes.classify_document")
@patch("app.api.routes.get_cv_text")
def test_upload_cv_rejects_jd_document(mock_get_text, mock_classify):
    """JD səhvən CV kimi yüklənibsə, rədd edilməlidir."""
    mock_get_text.return_value = "fake jd text"
    mock_classify.return_value = "JD"

    response = client.post(
        "/v1/cv/upload",
        files={"file": ("cv.pdf", b"%PDF-1.4 fake", "application/pdf")},
        data={"session_id": "test-session"},
    )

    assert response.status_code == 400
    assert "CV-yə bənzəmir" in response.json()["detail"]


@patch("app.api.routes.parse_jd_with_llm")
def test_parse_jd(mock_parse_jd):
    """JD parse endpoint-i strukturlaşdırılmış data qaytarmalıdır."""
    mock_parse_jd.return_value = {
        "job_title": "AI Engineer",
        "company": "TestCo",
        "required_skills": ["Python"],
        "search_queries": ["Python experience"],
    }

    response = client.post("/v1/jd/parse", json={"text": "some jd text"})

    assert response.status_code == 200
    assert response.json()["job_title"] == "AI Engineer"


@patch("app.api.routes.classify_document")
def test_validate_jd_true(mock_classify):
    mock_classify.return_value = "JD"
    response = client.post("/v1/jd/validate", json={"text": "some text"})
    assert response.json()["is_valid_jd"] is True


@patch("app.api.routes.classify_document")
def test_validate_jd_false(mock_classify):
    mock_classify.return_value = "CV"
    response = client.post("/v1/jd/validate", json={"text": "some text"})
    assert response.json()["is_valid_jd"] is False


def test_match_fails_with_unknown_session():
    """Mövcud olmayan session_id ilə match cəhdi 404 qaytarmalıdır."""
    response = client.post(
        "/v1/match",
        json={"session_id": "nonexistent-session", "jd_text": "text"},
    )
    assert response.status_code == 404


@patch("app.api.routes.analyze_match")
@patch("app.api.routes.parse_jd_with_llm")
@patch("app.api.routes.classify_document")
def test_match_success(mock_classify, mock_parse_jd, mock_analyze):
    """Mövcud session ilə tam match axını işləməlidir."""
    save_session("match-test-session", {"name": "Test User"}, "Test User")

    mock_classify.return_value = "JD"
    mock_parse_jd.return_value = {
        "job_title": "AI Engineer",
        "company": "TestCo",
        "search_queries": [],
    }
    mock_analyze.return_value = {
        "match_score": 80,
        "match_level": "Strong",
        "matched_skills": [],
        "missing_skills": [],
        "recommendations": [],
        "summary": "Great fit.",
    }

    response = client.post(
        "/v1/match",
        json={"session_id": "match-test-session", "jd_text": "some jd text"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["cv_owner"] == "Test User"
    assert data["analysis"]["match_score"] == 80


@patch("app.api.routes.classify_document")
def test_match_rejects_cv_text_as_jd(mock_classify):
    """JD sahəsinə CV mətni verilərsə, rədd edilməlidir."""
    save_session("session-with-cv-as-jd", {"name": "X"}, "X")
    mock_classify.return_value = "CV"

    response = client.post(
        "/v1/match",
        json={"session_id": "session-with-cv-as-jd", "jd_text": "looks like a cv"},
    )

    assert response.status_code == 400
