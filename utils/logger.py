# utils/logger.py
"""
Centralised logging setup.
Every module gets a logger with the same format by importing this.

Usage in any module:
    from utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("VectorDB built with %d chunks", n)
"""

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:          # avoid duplicate handlers on re-import
        return logger

    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    ))

    logger.addHandler(handler)
    logger.propagate = False
    return logger