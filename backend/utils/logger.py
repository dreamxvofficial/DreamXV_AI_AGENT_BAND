"""
DreamXV AI Studio — Structured Logger
======================================
Dream XV branded logging using loguru.
Vercel Serverless Compatible.
"""

from __future__ import annotations

import os
import sys
from loguru import logger

# Remove default logger
logger.remove()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

_FORMAT = (
    "<level>{level: <8}</level> | "
    "<cyan>DreamXV</cyan> | "
    "<white>{time:HH:mm:ss}</white> | "
    "<level>{message}</level>"
)

# Vercel-compatible console logger
logger.add(
    sys.stdout,
    format=_FORMAT,
    level=LOG_LEVEL,
    colorize=True,
    backtrace=True,
    diagnose=False,
    enqueue=True,
)

def get_logger(name: str = "dreamxv"):
    """Return contextual DreamXV logger."""
    return logger.bind(module=name)