# app/tools/evaluator.py

"""
Manual Evaluation Framework — Ragas-a alternativ.

Dörd metrika ilə matching nəticəsinin keyfiyyətini ölçür:
1. Skill Coverage Rate
2. Critical Gap Rate
3. Match Confidence
4. Recommendation Quality
"""


def calculate_skill_coverage(analysis: dict) -> float:
    """
    CV-nin JD tələblərini nə qədər qarşıladığını ölçür.

    Nümunə:
      matched: [Python, FastAPI, RAG]  → 3
      missing required: [Docker, K8s]  → 2
      coverage = 3 / (3+2) * 100 = 60%
    """
    matched = len(analysis.get("matched_skills", []))
    missing_required = sum(
        1 for s in analysis.get("missing_skills", []) if s.get("importance") == "required"
    )
    total = matched + missing_required
    if total == 0:
        return 100.0
    return round(matched / total * 100, 1)


def calculate_critical_gap_rate(analysis: dict) -> float:
    """
    Vacib tələblərdən nə qədəri çatışmır?
    Aşağı olduqca yaxşıdır.

    Nümunə:
      missing required: [Docker, K8s]     → 2
      missing nice-to-have: [Terraform]   → 1
      total required = matched(3) + missing_req(2) = 5
      gap rate = 2/5 * 100 = 40%
    """
    matched = len(analysis.get("matched_skills", []))
    missing_required = sum(
        1 for s in analysis.get("missing_skills", []) if s.get("importance") == "required"
    )
    total_required = matched + missing_required
    if total_required == 0:
        return 0.0
    return round(missing_required / total_required * 100, 1)


def calculate_match_confidence(analysis: dict, coverage_score: float) -> float:
    """
    LLM-in verdiyi score ilə bizim hesabladığımız coverage arasındakı
    uyğunluğu ölçür.

    Fərq az olduqca → LLM-ə etibar yüksəkdir.
    100 - fərq = confidence score

    Nümunə:
      LLM score: 72%
      Bizim coverage: 60%
      Fərq: 12
      Confidence: 100 - 12 = 88%
    """
    llm_score = analysis.get("match_score", 0)
    diff = abs(llm_score - coverage_score)
    confidence = max(0.0, 100.0 - diff)
    return round(confidence, 1)


def calculate_recommendation_quality(analysis: dict) -> float:
    """
    Tövsiyələrin nə qədəri konkret (missing skill-lərə aid)?
    Ümumi tövsiyələr ("improve your skills") deyil,
    spesifik tövsiyələr ("Learn Docker for containerization") daha dəyərlidir.

    Yoxlama: tövsiyə missing skill adını ehtiva edirmi?
    """
    recommendations = analysis.get("recommendations", [])
    if not recommendations:
        return 0.0

    missing_skills = [s["skill"].lower() for s in analysis.get("missing_skills", [])]

    if not missing_skills:
        return 100.0

    specific_count = 0
    for rec in recommendations:
        rec_lower = rec.lower()
        if any(skill in rec_lower for skill in missing_skills):
            specific_count += 1

    return round(specific_count / len(recommendations) * 100, 1)


def evaluate_analysis(analysis: dict) -> dict:
    """
    Bütün metrikalrı hesablayıb structured nəticə qaytarır.

    analysis: analyze_match() funksiyasının nəticəsi
    """
    coverage = calculate_skill_coverage(analysis)
    gap_rate = calculate_critical_gap_rate(analysis)
    confidence = calculate_match_confidence(analysis, coverage)
    rec_quality = calculate_recommendation_quality(analysis)

    # Ümumi keyfiyyət skoru (4 metrikadan ortalama)
    # Gap rate-i tərsinə çeviririk (aşağı gap = yaxşı)
    overall = round((coverage + (100 - gap_rate) + confidence + rec_quality) / 4, 1)

    return {
        "skill_coverage_rate": coverage,
        "critical_gap_rate": gap_rate,
        "match_confidence": confidence,
        "recommendation_quality": rec_quality,
        "overall_quality_score": overall,
        "interpretation": _interpret(overall),
    }


def _interpret(score: float) -> str:
    """Ümumi keyfiyyət skorunu oxunaqlı formata çevirir."""
    if score >= 85:
        return "Excellent — analiz çox etibarlıdır"
    elif score >= 70:
        return "Good — analiz etibarlıdır"
    elif score >= 55:
        return "Fair — analiz qəbul edilə bilər"
    else:
        return "Poor — analiz nəticəsinə ehtiyatla yanaşın"
