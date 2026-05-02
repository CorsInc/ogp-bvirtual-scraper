"""Logging utility with colors and levels for the scraper."""

import logging
import os
import sys
from datetime import datetime


# ANSI color codes
class Colors:
    GRAY = "\033[90m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


LEVEL_COLORS = {
    logging.DEBUG: Colors.GRAY,
    logging.INFO: Colors.GREEN,
    logging.WARNING: Colors.YELLOW,
    logging.ERROR: Colors.RED,
    logging.CRITICAL: Colors.RED + Colors.BOLD,
}

LEVEL_ICONS = {
    logging.DEBUG: "🔍",
    logging.INFO: "ℹ️",
    logging.WARNING: "⚠️",
    logging.ERROR: "❌",
    logging.CRITICAL: "🔥",
}


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and icons."""

    def format(self, record):
        color = LEVEL_COLORS.get(record.levelno, Colors.RESET)
        icon = LEVEL_ICONS.get(record.levelno, "")
        record.levelname_colored = f"{color}{record.levelname}{Colors.RESET}"
        record.icon = icon
        # Truncate name for alignment
        name = record.name.split(".")[-1][:12]
        record.short_name = f"{name:12s}"
        return super().format(record)


def setup_logger(name: str = "ogp_scraper", level=None) -> logging.Logger:
    """Set up and return a colored logger.

    Level defaults to INFO, or DEBUG if OGP_DEBUG=1 is set.
    """
    if level is None:
        level = logging.DEBUG if os.getenv("OGP_DEBUG") == "1" else logging.INFO

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    fmt = ColoredFormatter(
        "%(icon)s %(levelname_colored)s %(short_name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(fmt)
    logger.addHandler(handler)

    return logger


# Default logger
log = setup_logger()
