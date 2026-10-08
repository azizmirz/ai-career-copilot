# app/core/session_store.py

"""
MÜVƏQQƏTİ in-memory session store.

Niyə müvəqqəti?
- Server yenidən başlayanda (restart) data itir
- Backend-i test etmək üçündür
"""

_sessions: dict[str, dict] = {}


def save_session(session_id: str, parsed_cv: dict, cv_owner: str):
    _sessions[session_id] = {
        "parsed_cv": parsed_cv,
        "cv_owner": cv_owner,
    }


def get_session(session_id: str) -> dict | None:
    return _sessions.get(session_id)
