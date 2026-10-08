# app/tools/jd_parser.py

import json

from groq import Groq

from app.core.config import settings
from app.core.logger import logger

client = Groq(api_key=settings.groq_api_key)

FAKE_JD_TEXT = """
Job Title: AI Engineer
Company: TechBank Baku

About the Role:
We are looking for an experienced AI Engineer to join our growing team.
You will be responsible for building and maintaining AI-powered systems
that serve millions of customers.

Requirements:
- 2+ years of experience with Python
- Strong knowledge of LLMs and prompt engineering
- Experience with vector databases (Pinecone, Qdrant, or similar)
- FastAPI or similar backend framework experience
- Experience building RAG pipelines
- Familiarity with LangChain or LangGraph
- Git version control

Nice to Have:
- Experience with Kubernetes or Docker
- Knowledge of AWS or Azure cloud platforms
- MLOps experience (model monitoring, deployment pipelines)
- Experience with Redis caching

Responsibilities:
- Design and implement LLM-powered features
- Build and optimize RAG systems
- Collaborate with product team to deliver AI solutions
- Monitor and improve model performance in production
"""


def get_jd_text(jd_text: str | None = None) -> str:
    """
    JD mətni verilibsə onu istifadə et,
    yoxdursa fake JD qaytar.
    """
    if jd_text:
        return jd_text
    print("JD verilmədi, fake JD istifadə olunur.")
    return FAKE_JD_TEXT


def parse_jd_with_llm(jd_text: str) -> dict:
    """
    JD mətnini LLM-ə göndərir.
    Tələblər, bacarıqlar, məsuliyyətlər strukturlaşdırılır.
    """

    prompt = f"""
You are a Job Description analyzer. Extract structured information from the job description below.
Return ONLY a valid JSON object, no explanation.

Required JSON structure:
{{
  "job_title": "position name",
  "company": "company name if mentioned",
  "required_skills": ["skill1", "skill2"],
  "nice_to_have_skills": ["skill1", "skill2"],
  "experience_requirements": ["requirement1", "requirement2"],
  "responsibilities": ["responsibility1", "responsibility2"],
  "search_queries": [
    "natural language query to search CV for requirement 1",
    "natural language query to search CV for requirement 2"
  ]
}}

IMPORTANT for search_queries:
- Generate one search query per major requirement
- Write them as natural language phrases (not keywords)
- These will be used to search the candidate's CV
- Generate between 5-8 queries covering the most important requirements

JOB DESCRIPTION:
{jd_text}
"""
    logger.info(f"LLM call: JD parse | model=llama-3.3-70b-versatile")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    raw_response = response.choices[0].message.content

    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()

    usage = response.usage
    logger.info(
        f"LLM done: JD parse | "
        f"tokens=({usage.prompt_tokens}prompt + "
        f"{usage.completion_tokens}completion) | "
        f"total={usage.total_tokens}"
    )

    return json.loads(cleaned)
