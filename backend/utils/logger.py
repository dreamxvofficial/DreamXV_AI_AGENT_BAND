import os
import sys
from loguru import logger

logger.remove()

logger.add(
    sys.stderr,
    level="INFO",
    colorize=False,
    backtrace=False,
    diagnose=False,
)

def get_logger(name="dreamxv"):
    return logger.bind(module=name)