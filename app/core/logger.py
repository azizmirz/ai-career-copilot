# app/core/logger.py

import sys
from loguru import logger
from pathlib import Path

# Log qovluğu
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


logger.remove()

# ── Terminal (rəngli, oxunaqlı) ───────────────────────────
logger.add(
    sys.stdout,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    ),
    level="INFO",
    colorize=True,
)

# ── Fayla (JSON, strukturlu — production üçün) ────────────
logger.add(
    LOG_DIR / "app.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} | {message}",
    level="INFO",
    rotation="10 MB",  # 10MB-dan böyük olsa yeni fayl
    retention="7 days",  # 7 gündən köhnə logları sil
    compression="zip",  
)

# ── Xəta faylı (yalnız ERROR və yuxarısı) ─────────────────
logger.add(
    LOG_DIR / "errors.log",
    level="ERROR",
    rotation="5 MB",
    retention="30 days",
    compression="zip",
)
