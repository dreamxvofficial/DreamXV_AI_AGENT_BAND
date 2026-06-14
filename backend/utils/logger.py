from __future__ import annotations

import os
import sys
from loguru import logger

logger.remove()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

_FORMAT = (
    "<level>{level: <8}</level> | "
    "<cyan>DreamXV</cyan> | "
    "<white>{time:HH:mm:ss}</white> | "
    "<level>{message}</level>"
)

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
    return logger.bind(module=name)