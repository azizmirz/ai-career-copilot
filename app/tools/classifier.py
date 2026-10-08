# app/tools/classifier.py

from groq import Groq

from app.core.config import settings
from app.core.logger import logger

client = Groq(api_key=settings.groq_api_key)


def classify_document(text: str) -> str:
    """
    Mətnin CV yoxsa Job Description olduğunu təyin edir.
    Sürətli, ucuz LLM çağırışı — yalnız "CV" və ya "JD" qaytarır.
    """
    prompt = f"""
Determine whether the following document is:
- "CV": a person's resume/CV (describes one individual's own skills, education, work history)
- "JD": a job description/posting (a company describing an open position and its requirements)

Respond with ONLY one word: CV or JD

DOCUMENT (excerpt):
{text[:2000]}
"""
    logger.info("LLM call: Document classification")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=5,
    )

    result = response.choices[0].message.content.strip().upper()
    logger.info(f"LLM done: Classification result={result}")

    return "CV" if "CV" in result else "JD"
