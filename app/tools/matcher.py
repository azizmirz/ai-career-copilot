# app/tools/matcher.py

import json

from groq import Groq

from app.core.config import settings
from app.core.vector_store import search_cv
from app.core.logger import logger

client = Groq(api_key=settings.groq_api_key)


def build_context(parsed_jd: dict, session_id: str) -> str:
    """session_id ilə yalnız bu session-ın CV-si axtarılır."""
    context_parts = []

    for query in parsed_jd["search_queries"]:
        results = search_cv(query, session_id=session_id, top_k=2)
        if results:
            context_parts.append(f"Requirement: {query}")
            for r in results:
                context_parts.append(
                    f"  CV Match [{r['section']}] " f"(score={r['score']}): {r['text']}"
                )
            context_parts.append("")

    return "\n".join(context_parts)


def analyze_match(parsed_cv: dict, parsed_jd: dict, session_id: str) -> dict:
    cv_summary = f"""
Candidate: {parsed_cv.get('name')}
Summary: {parsed_cv.get('summary')}
Skills: {', '.join(parsed_cv.get('skills', []))}
"""

    jd_summary = f"""
Position: {parsed_jd.get('job_title')} at {parsed_jd.get('company')}
Required Skills: {', '.join(parsed_jd.get('required_skills', []))}
Nice to Have: {', '.join(parsed_jd.get('nice_to_have_skills', []))}
"""

    cv_context = build_context(parsed_jd, session_id)

    prompt = f"""
You are an expert technical recruiter and career advisor.
Analyze how well this candidate matches the job description.
Return ONLY a valid JSON object, no explanation.

CANDIDATE PROFILE:
{cv_summary}

JOB DESCRIPTION:
{jd_summary}

CV EVIDENCE (semantic search results from candidate's CV):
{cv_context}

Return this exact JSON structure:
{{
  "match_score": <integer 0-100>,
  "match_level": "<Poor/Fair/Good/Strong/Excellent>",
  "matched_skills": [
    {{"skill": "skill name", "evidence": "where found in CV"}}
  ],
  "missing_skills": [
    {{"skill": "skill name", "importance": "<required/nice-to-have>"}}
  ],
  "recommendations": [
    "specific actionable advice to improve CV or skills"
  ],
  "summary": "2-3 sentence overall assessment"
}}

Be specific and honest. Base your assessment on the CV evidence provided.
"""
    logger.info(f"LLM call: Match analysis | model=llama-3.3-70b-versatile")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    usage = response.usage
    logger.info(
        f"LLM done: Match analysis | "
        f"tokens=({usage.prompt_tokens}prompt + "
        f"{usage.completion_tokens}completion) | "
        f"total={usage.total_tokens}"
    )

    return json.loads(raw)
