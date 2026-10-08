# tests/test_evaluator.py

from app.tools.evaluator import (
    calculate_skill_coverage,
    calculate_critical_gap_rate,
    calculate_match_confidence,
    calculate_recommendation_quality,
    evaluate_analysis,
)

SAMPLE_ANALYSIS = {
    "match_score": 72,
    "matched_skills": [
        {"skill": "Python", "evidence": "Skills section"},
        {"skill": "FastAPI", "evidence": "Skills section"},
        {"skill": "RAG", "evidence": "Experience section"},
    ],
    "missing_skills": [
        {"skill": "Docker", "importance": "required"},
        {"skill": "Kubernetes", "importance": "nice-to-have"},
    ],
    "recommendations": [
        "Learn Docker for containerization",
        "Consider studying Kubernetes",
        "Improve communication skills",
    ],
    "summary": "Good candidate with some gaps.",
}


def test_skill_coverage_normal():
    """3 matched, 1 required missing → 3/(3+1)*100 = 75%"""
    coverage = calculate_skill_coverage(SAMPLE_ANALYSIS)
    assert coverage == 75.0


def test_skill_coverage_no_skills():
    """Heç bir skill yoxdursa → 100% (boş tələb)"""
    assert calculate_skill_coverage({}) == 100.0


def test_critical_gap_rate_normal():
    """1 required missing, 3 matched → 1/(3+1)*100 = 25%"""
    gap = calculate_critical_gap_rate(SAMPLE_ANALYSIS)
    assert gap == 25.0


def test_critical_gap_rate_no_gaps():
    """Missing skill yoxdursa → 0%"""
    analysis = {"matched_skills": [{"skill": "Python"}], "missing_skills": []}
    assert calculate_critical_gap_rate(analysis) == 0.0


def test_match_confidence_close_scores():
    """LLM=72, coverage=75 → fərq=3 → confidence=97%"""
    confidence = calculate_match_confidence(SAMPLE_ANALYSIS, 75.0)
    assert confidence == 97.0


def test_match_confidence_large_gap():
    """LLM=72, coverage=20 → fərq=52 → confidence=48%"""
    confidence = calculate_match_confidence(SAMPLE_ANALYSIS, 20.0)
    assert confidence == 48.0


def test_recommendation_quality_specific():
    """
    3 tövsiyədən 2-si missing skill adını ehtiva edir
    (Docker, Kubernetes) → 2/3*100 = 66.7%
    """
    quality = calculate_recommendation_quality(SAMPLE_ANALYSIS)
    assert quality == 66.7


def test_recommendation_quality_empty():
    """Tövsiyə yoxdursa → 0%"""
    assert calculate_recommendation_quality({}) == 0.0


def test_evaluate_analysis_returns_all_fields():
    """evaluate_analysis() bütün sahələri qaytarmalıdır."""
    result = evaluate_analysis(SAMPLE_ANALYSIS)
    assert "skill_coverage_rate" in result
    assert "critical_gap_rate" in result
    assert "match_confidence" in result
    assert "recommendation_quality" in result
    assert "overall_quality_score" in result
    assert "interpretation" in result


def test_evaluate_analysis_interpretation_good():
    """75% overall → 'Good' interpretation"""
    result = evaluate_analysis(SAMPLE_ANALYSIS)
    assert "Good" in result["interpretation"] or "Excellent" in result["interpretation"]
