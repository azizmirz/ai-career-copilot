# app/core/cache.py

import hashlib
import json
from datetime import datetime, timedelta

_cache: dict[str, dict] = {}
_TTL_HOURS = 24  # Cache 24 saat saxlanılır


def _make_key(user_id: int, cv_text: str, jd_text: str) -> str:
    """
    user_id cache key-in bir hissəsidir —
    fərqli istifadəçilər eyni CV+JD versə belə
    bir-birinin nəticəsini görə bilməz.
    """
    combined = f"{user_id}|||{cv_text.strip()}|||{jd_text.strip()}"
    return hashlib.md5(combined.encode("utf-8")).hexdigest()


def get_cached_analysis(user_id: int, cv_text: str, jd_text: str) -> dict | None:
    """
    Bu CV+JD cütü üçün keşdə nəticə varmı?
    Varsa qaytarır, yoxsa None qaytarır.
    TTL bitibsə silib None qaytarır.
    """
    key = _make_key(user_id, cv_text, jd_text)
    entry = _cache.get(key)

    if entry is None:
        return None

    # TTL yoxlanışı
    if datetime.utcnow() > entry["expires_at"]:
        del _cache[key]
        return None

    return entry["data"]


def set_cached_analysis(user_id: int, cv_text: str, jd_text: str, analysis: dict) -> None:
    """Analiz nəticəsini keşə yaz."""
    key = _make_key(user_id, cv_text, jd_text)
    _cache[key] = {
        "data": analysis,
        "expires_at": datetime.utcnow() + timedelta(hours=_TTL_HOURS),
        "created_at": datetime.utcnow().isoformat(),
    }


def get_cache_stats() -> dict:
    """
    Cache statistikası — debug və monitoring üçün.
    """
    now = datetime.utcnow()
    active = sum(1 for e in _cache.values() if now <= e["expires_at"])
    return {
        "total_entries": len(_cache),
        "active_entries": active,
        "expired_entries": len(_cache) - active,
    }
