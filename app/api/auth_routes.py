# app/api/auth_routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.auth import (
    get_user_by_email,
    create_user,
    verify_password,
    create_access_token,
)
from app.api.schemas import RegisterRequest, LoginRequest, TokenResponse

auth_router = APIRouter(prefix="/auth")


@auth_router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Yeni istifadəçi qeydiyyatı.
    Email artıq mövcuddursa 400 qaytarır.
    Uğurlu olsa dərhal JWT token qaytarır (login tələb etmir).
    """
    existing = get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(400, "Bu email artıq qeydiyyatdadır.")

    user = create_user(db, payload.email, payload.password, payload.full_name)
    token = create_access_token(user.id, user.email)

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
    )


@auth_router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Email + şifrə ilə giriş.
    Uğurlu olsa JWT token qaytarır.
    """
    user = get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(401, "Email və ya şifrə yanlışdır.")

    token = create_access_token(user.id, user.email)

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
    )
