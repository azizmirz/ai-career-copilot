import json
from pathlib import Path

from groq import Groq
from pypdf import PdfReader

from app.core.config import settings
from app.core.logger import logger

client = Groq(api_key=settings.groq_api_key)

FAKE_CV_TEXT = """
Cavid MAMMADOV
AI Engineer | Baku, Azerbaijan
Email: fakecavid_mammadov@email.com | GitHub: github.com/fakecavidmammadov

SUMMARY
AI Engineer with MSc in Computer Science (AI focus) from Khazar University.
Experienced in building RAG pipelines, LLM applications, and NLP systems.
Strong background in Python, FastAPI, and vector databases.

SKILLS
- Programming: Python, SQL, Bash
- AI/ML: LangChain, LangGraph, HuggingFace, Sentence Transformers
- Vector Databases: ChromaDB, Qdrant
- LLMs: Groq (LLaMA), Gemini, OpenAI API
- Backend: FastAPI, REST APIs
- Tools: Git, Docker (basic), VS Code, Jupyter

EXPERIENCE
AI Engineer Intern | TechCorp Baku | 2023 - 2024
- Built a document Q&A system using RAG pipeline with ChromaDB and LangChain
- Implemented multi-query retrieval with Reciprocal Rank Fusion (RRF)
- Reduced LLM API costs by 30% using semantic caching with Redis

Research Assistant | Khazar University | 2022 - 2023
- Developed NLP pipeline for scientific PDF extraction
- Used multimodal approach: text, table, and image extraction from PDFs
- Evaluated RAG system quality using RAGAS framework

EDUCATION
MSc Computer Science (AI Focus) | Khazar University | 2021 - 2024
BSc Computer Science | Baku State University | 2017 - 2021

PROJECTS
AI News Aggregator (github.com/cavidmammadov/ai-news-aggregator)
- Automated news collection and summarization using LLM agents
- FastAPI backend with async endpoints

Multimodal RAG System
- Scientific PDF processing with Gemini for image analysis
- Groq LLaMA for text and table summarization


"""


def extract_text_from_pdf(pdf_path: str) -> str:
    """PDF faylından raw text çıxarır."""

    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


def get_cv_text(pdf_path: str | None = None) -> str:
    """
    PDF varsa oxu, yoxdursa fake CV-ni qaytar.
    """
    if pdf_path and Path(pdf_path).exists():
        print("PDF tapıldı, oxunur...")
        return extract_text_from_pdf(pdf_path)

    print("PDF tapılmadı, fake CV istifadə olunur.")
    return FAKE_CV_TEXT


def parse_cv_with_llm(cv_text: str) -> dict:
    """
    CV mətnini Groq LLM-ə göndərir.
    LLM strukturlaşdırılmış JSON qaytarır.

    Niyə LLM-based?
    - Hardcoded section adları yoxdur
    - İstənilən CV formatını anlayır
    """

    prompt = f"""
You are a CV parser. Extract information from the CV below and return ONLY a valid JSON object.
Do not write any explanation, just the JSON.

Required JSON structure:
{{
  "name": "full name",
  "contact": {{
    "email": "email if found",
    "github": "github if found",
    "location": "location if found"
  }},
  "summary": "professional summary as a single string",
  "skills": ["skill1", "skill2"],
  "experience": [
    {{
      "title": "job title",
      "company": "company name",
      "period": "date range",
      "responsibilities": ["item1", "item2"]
    }}
  ],
  "education": [
    {{
      "degree": "degree name",
      "institution": "university name",
      "period": "date range"
    }}
  ],
  "projects": [
    {{
      "name": "project name",
      "description": ["detail1", "detail2"]
    }}
  ],
  "extra_sections": {{
    "SECTION_NAME": "full content as string"
  }}
}}

IMPORTANT: 
- If the CV contains sections not listed above (e.g. Certifications, Languages, 
  Publications, Awards, Volunteering etc.), add them ALL to extra_sections.
- If no extra sections exist, set extra_sections to empty dict {{}}.

CV TEXT:
{cv_text}
"""
    logger.info(f"LLM call: CV parse | model=llama-3.3-70b-versatile")

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

    parsed = json.loads(cleaned)

    usage = response.usage
    logger.info(
        f"LLM done: CV parse | "
        f"tokens=({usage.prompt_tokens}prompt + "
        f"{usage.completion_tokens}completion) | "
        f"total={usage.total_tokens}"
    )

    return parsed


def cv_to_chunks(parsed_cv: dict) -> list[dict]:
    """
    Strukturlaşdırılmış CV dict-ini
    Qdrant-a yazılmaq üçün chunk list-ə çevirir.

    Hər chunk: {'section': ..., 'text': ...}
    Bu formatda embedding + axtarış edilir.
    """

    chunks = []

    if parsed_cv.get("summary"):
        chunks.append({"section": "summary", "text": parsed_cv["summary"]})

    if parsed_cv.get("skills"):
        chunks.append({"section": "skills", "text": "Skills: " + ", ".join(parsed_cv["skills"])})

    for exp in parsed_cv.get("experience", []):
        text = f"{exp['title']} at {exp['company']} ({exp['period']}): "
        text += " ".join(exp.get("responsibilities", []))
        chunks.append({"section": "experience", "text": text})

    for edu in parsed_cv.get("education", []):
        text = f"{edu['degree']} at {edu['institution']} ({edu['period']})"
        chunks.append({"section": "education", "text": text})

    for proj in parsed_cv.get("projects", []):
        text = f"Project: {proj['name']}. "
        text += " ".join(proj.get("description", []))
        chunks.append({"section": "project", "text": text})

    for section_name, content in parsed_cv.get("extra_sections", {}).items():
        if content:
            chunks.append({"section": section_name.lower(), "text": f"{section_name}: {content}"})

    return chunks
