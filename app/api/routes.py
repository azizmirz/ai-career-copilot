# app/api/routes.py

import os
import tempfile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.api.schemas import CVUploadResponse, JDParseRequest, MatchRequest
from app.core.session_store import get_session, save_session
from app.core.vector_store import store_cv_chunks
from app.tools.classifier import classify_document
from app.tools.cv_parser import cv_to_chunks, get_cv_text, parse_cv_with_llm
from app.tools.jd_parser import parse_jd_with_llm
from app.tools.matcher import analyze_match
from app.db.auth import get_current_user
from app.db.models import User, AnalysisHistory
from app.db.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from app.core.cache import get_cached_analysis, set_cached_analysis
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from app.tools.evaluator import evaluate_analysis
from app.core.logger import logger
import json

router = APIRouter(prefix="/v1")
limiter = Limiter(key_func=get_remote_address)


@router.post("/cv/upload", response_model=CVUploadResponse)
@limiter.limit("5/minute")
async def upload_cv(
    request: Request,
    file: UploadFile = File(...),
    session_id: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    """
    CV-ni PDF formatında qəbul edir, parse edir, Qdrant-a yazır.
    Əvvəlcə sənəd növünü yoxlayır — JD səhvən CV kimi yüklənibsə rədd edir.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Yalnız PDF faylları qəbul olunur")

    content = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        cv_text = get_cv_text(tmp_path)

        # ── Sənəd növü yoxlanışı ──
        doc_type = classify_document(cv_text)
        if doc_type != "CV":
            raise HTTPException(400, "Bu sənəd CV-yə bənzəmir" "Zəhmət olmasa CV-nizi yükləyin.")

        parsed_cv = parse_cv_with_llm(cv_text)
        chunks = cv_to_chunks(parsed_cv)
        cv_owner = parsed_cv.get("name", "unknown")
        store_cv_chunks(chunks, cv_owner=cv_owner, session_id=session_id)
        save_session(session_id, parsed_cv, cv_owner)
    finally:
        os.unlink(tmp_path)
        logger.info(
            f"CV uploaded | user={current_user.email} | " f"owner={cv_owner} | chunks={len(chunks)}"
        )

    return CVUploadResponse(
        session_id=session_id,
        cv_owner=cv_owner,
        chunks_count=len(chunks),
    )


@router.post("/jd/parse")
async def parse_jd(payload: JDParseRequest):
    """JD mətnini parse edir, strukturlaşdırılmış JSON qaytarır."""
    return parse_jd_with_llm(payload.text)


@router.post("/jd/validate")
async def validate_jd(payload: JDParseRequest):
    """
    JD mətninin Job Description olub-olmadığını yoxlayır
    """
    doc_type = classify_document(payload.text)
    return {"is_valid_jd": doc_type == "JD", "detected_type": doc_type}


@router.post("/match")
@limiter.limit("10/minute")
async def match(
    request: Request,
    payload: MatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_session(payload.session_id)
    if session is None:
        raise HTTPException(404, "Session tapılmadı. Əvvəlcə CV-nizi yükləyin.")

    doc_type = classify_document(payload.jd_text)
    if doc_type != "JD":
        raise HTTPException(
            400,
            "Yüklədiyiniz mətn İş elanına bənzəmir — CV kimi görünür. "
            "Zəhmət olmasa düzgün iş elanı mətnini daxil edin.",
        )

    # ── Cache yoxlanışı ──────────────────────────────────
    cv_text_for_cache = session["parsed_cv"].get("summary", "") + str(
        session["parsed_cv"].get("skills", [])
    )
    cached = get_cached_analysis(current_user.id, cv_text_for_cache, payload.jd_text)

    if cached:
        logger.info(f"Match from cache | user={current_user.email}")
        evaluation = evaluate_analysis(cached["analysis"])
        return {
            "cv_owner": session["cv_owner"],
            "parsed_jd": cached["parsed_jd"],
            "analysis": cached["analysis"],
            "evaluation": evaluation,
            "from_cache": True,
        }
    # ────────────────────────────────────────────────────

    parsed_jd = parse_jd_with_llm(payload.jd_text)
    analysis = analyze_match(session["parsed_cv"], parsed_jd, session_id=payload.session_id)

    # ── Nəticəni keşə yaz ───────────────────────────────
    set_cached_analysis(
        current_user.id,
        cv_text_for_cache,
        payload.jd_text,
        {"parsed_jd": parsed_jd, "analysis": analysis},
    )
    # ────────────────────────────────────────────────────

    history = AnalysisHistory(
        user_id=current_user.id,
        cv_owner=session["cv_owner"],
        job_title=parsed_jd.get("job_title"),
        company=parsed_jd.get("company"),
        match_score=analysis["match_score"],
        match_level=analysis["match_level"],
        summary=analysis.get("summary"),
        matched_skills_json=json.dumps(analysis.get("matched_skills", [])),
        missing_skills_json=json.dumps(analysis.get("missing_skills", [])),
        recommendations_json=json.dumps(analysis.get("recommendations", [])),
    )
    db.add(history)
    db.commit()

    evaluation = evaluate_analysis(analysis)

    logger.info(
        f"Match completed | user={current_user.email} | "
        f"score={analysis['match_score']}% | "
        f"level={analysis['match_level']} | "
        f"from_cache={False}"
    )

    return {
        "cv_owner": session["cv_owner"],
        "parsed_jd": parsed_jd,
        "analysis": analysis,
        "evaluation": evaluation,
        "from_cache": False,
    }


@router.get("/history")
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    İstifadəçinin keçmiş analiz nəticələrini qaytarır.
    Yalnız öz tarixçəsini görə bilər.
    """
    records = (
        db.query(AnalysisHistory)
        .filter(AnalysisHistory.user_id == current_user.id)
        .order_by(AnalysisHistory.created_at.desc())
        .all()
    )

    return [
        {
            "id": r.id,
            "cv_owner": r.cv_owner,
            "job_title": r.job_title,
            "company": r.company or "Naməlum Şirkət",
            "match_score": r.match_score,
            "match_level": r.match_level,
            "summary": r.summary,
            "matched_skills": json.loads(r.matched_skills_json or "[]"),
            "missing_skills": json.loads(r.missing_skills_json or "[]"),
            "recommendations": json.loads(r.recommendations_json or "[]"),
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]
