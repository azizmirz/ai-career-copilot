# tests/test_cv_parser.py

from app.tools.cv_parser import cv_to_chunks


def test_cv_to_chunks_full_cv():
    """Bütün section-ları olan tam CV-ni test edir."""
    parsed_cv = {
        "name": "Test User",
        "summary": "Experienced engineer",
        "skills": ["Python", "FastAPI"],
        "experience": [
            {
                "title": "Engineer",
                "company": "TechCo",
                "period": "2020-2023",
                "responsibilities": ["Built APIs", "Led team"],
            }
        ],
        "education": [{"degree": "BSc CS", "institution": "MIT", "period": "2016-2020"}],
        "projects": [{"name": "AI Bot", "description": ["Built chatbot"]}],
        "extra_sections": {},
    }

    chunks = cv_to_chunks(parsed_cv)

    assert len(chunks) == 5
    sections = [c["section"] for c in chunks]
    assert "summary" in sections
    assert "skills" in sections
    assert "experience" in sections
    assert "education" in sections
    assert "project" in sections


def test_cv_to_chunks_skills_format():
    """Skills chunk-ının mətn formatını dəqiq yoxlayır."""
    parsed_cv = {"skills": ["Python", "SQL"]}
    chunks = cv_to_chunks(parsed_cv)

    assert len(chunks) == 1
    assert chunks[0]["text"] == "Skills: Python, SQL"


def test_cv_to_chunks_empty_cv():
    """Boş CV — heç bir chunk yaranmamalıdır."""
    assert cv_to_chunks({}) == []


def test_cv_to_chunks_empty_skills_list():
    """Boş skills siyahısı (None deyil, []) — chunk yaranmamalıdır."""
    parsed_cv = {"skills": []}
    assert cv_to_chunks(parsed_cv) == []


def test_cv_to_chunks_multiple_experience_entries():
    """Birdən çox iş təcrübəsi — hər biri AYRI chunk olmalıdır."""
    parsed_cv = {
        "experience": [
            {"title": "Junior Dev", "company": "A", "period": "2018-2020", "responsibilities": []},
            {"title": "Senior Dev", "company": "B", "period": "2020-2023", "responsibilities": []},
        ]
    }
    chunks = cv_to_chunks(parsed_cv)
    assert len(chunks) == 2
    assert all(c["section"] == "experience" for c in chunks)


def test_cv_to_chunks_extra_sections_dynamic():
    """
    extra_sections-da olan naməlum bölmələr (məs. Certifications)
    avtomatik chunk-a çevrilməlidir — hardcoded olmadan.
    """
    parsed_cv = {
        "extra_sections": {
            "CERTIFICATIONS": "AWS Certified Solutions Architect",
            "LANGUAGES": "English, Azerbaijani",
        }
    }
    chunks = cv_to_chunks(parsed_cv)

    assert len(chunks) == 2
    sections = [c["section"] for c in chunks]
    assert "certifications" in sections
    assert "languages" in sections


def test_cv_to_chunks_extra_sections_skips_empty_content():
    """Boş məzmunlu extra_section chunk yaratmamalıdır."""
    parsed_cv = {
        "extra_sections": {
            "AWARDS": "",
            "CERTIFICATIONS": "Real content here",
        }
    }
    chunks = cv_to_chunks(parsed_cv)
    assert len(chunks) == 1
    assert chunks[0]["section"] == "certifications"
