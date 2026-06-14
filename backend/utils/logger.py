"""
DreamXV AI Studio — Structured Logger
======================================
Dream XV branded logging using loguru.
"""

from __future__ import annotations

import sys
from loguru import logger

# ─── Remove default handler ────────────────────────────────────────────────
logger.remove()

# ─── Console handler with Dream XV formatting ─────────────────────────────
_FORMAT = (
    "<level>{level: <8}</level> | "
    "<cyan>DreamXV</cyan> | "
    "<white>{time:HH:mm:ss}</white> | "
    "<level>{message}</level>"
)

logger.add(
    sys.stderr,
    format=_FORMAT,
    level="DEBUG",
    colorize=True,
    backtrace=True,
    diagnose=False,
)

# ─── File handler for persistent logs ──────────────────────────────────────
logger.add(
    "logs/dreamxv_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    level="INFO",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    enqueue=True,
)


def get_logger(name: str = "dreamxv"):
    """Return a contextual logger bound with a module name."""
    return logger.bind(module=name)
