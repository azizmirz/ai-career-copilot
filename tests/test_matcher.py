# tests/test_matcher.py

import json
from unittest.mock import MagicMock, patch

from app.tools.matcher import analyze_match, build_context


def make_fake_groq_response(content: str):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=content))]
    return mock_response


@patch("app.tools.matcher.search_cv")
def test_build_context_includes_search_results(mock_search):
    """search_cv nəticələri context mətninə düzgün əlavə olunmalıdır."""
    mock_search.return_value = [
        {"section": "skills", "score": 0.8, "text": "Skills: Python, FastAPI"},
    ]
    parsed_jd = {"search_queries": ["Python experience"]}

    context = build_context(parsed_jd, session_id="test-session")

    assert "Python experience" in context
    assert "Python, FastAPI" in context


@patch("app.tools.matcher.search_cv")
def test_build_context_empty_when_no_results(mock_search):
    """Heç nə tapılmasa, requirement context-ə əlavə olunmamalıdır."""
    mock_search.return_value = []
    parsed_jd = {"search_queries": ["Kubernetes experience"]}

    context = build_context(parsed_jd, session_id="test-session")

    assert "Kubernetes experience" not in context


@patch("app.tools.matcher.client.chat.completions.create")
@patch("app.tools.matcher.search_cv")
def test_analyze_match_returns_parsed_json(mock_search, mock_create):
    """analyze_match() LLM-in JSON cavabını düzgün parse edib qaytarmalıdır."""
    mock_search.return_value = [{"section": "skills", "score": 0.7, "text": "Skills: Python"}]

    fake_llm_json = {
        "match_score": 75,
        "match_level": "Good",
        "matched_skills": [{"skill": "Python", "evidence": "Skills section"}],
        "missing_skills": [{"skill": "Docker", "importance": "required"}],
        "recommendations": ["Learn Docker"],
        "summary": "Solid candidate with some gaps.",
    }
    mock_create.return_value = make_fake_groq_response(json.dumps(fake_llm_json))

    parsed_cv = {"name": "Test", "summary": "Engineer", "skills": ["Python"]}
    parsed_jd = {
        "job_title": "Backend Dev",
        "company": "TestCo",
        "required_skills": ["Python", "Docker"],
        "nice_to_have_skills": [],
        "search_queries": ["Python experience"],
    }

    result = analyze_match(parsed_cv, parsed_jd, session_id="test-session")

    assert result["match_score"] == 75
    assert result["matched_skills"][0]["skill"] == "Python"


@patch("app.tools.matcher.client.chat.completions.create")
@patch("app.tools.matcher.search_cv")
def test_analyze_match_strips_markdown_code_fences(mock_search, mock_create):
    """LLM JSON-u ```json ... ``` ilə əhatə etsə belə düzgün təmizlənməlidir."""
    mock_search.return_value = []

    fake_json_str = (
        '```json\n{"match_score": 50, "match_level": "Fair", '
        '"matched_skills": [], "missing_skills": [], '
        '"recommendations": [], "summary": "test"}\n```'
    )
    mock_create.return_value = make_fake_groq_response(fake_json_str)

    parsed_cv = {"name": "Test"}
    parsed_jd = {
        "job_title": "X",
        "company": "Y",
        "required_skills": [],
        "nice_to_have_skills": [],
        "search_queries": [],
    }

    result = analyze_match(parsed_cv, parsed_jd, session_id="test")

    assert result["match_score"] == 50
