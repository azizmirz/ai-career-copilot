from pydantic import BaseModel, EmailStr


class JDParseRequest(BaseModel):
    text: str


class MatchRequest(BaseModel):
    session_id: str
    jd_text: str


class CVUploadResponse(BaseModel):
    session_id: str
    cv_owner: str
    chunks_count: int


class HealthResponse(BaseModel):
    status: str
    service: str


# ── Auth schema-ları ──────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    full_name: str | None
