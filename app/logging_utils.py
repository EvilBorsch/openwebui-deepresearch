import logging
import os
from logging.handlers import TimedRotatingFileHandler
from typing import Optional

try:
    from rich.logging import RichHandler
    _HAS_RICH = True
except Exception:  # pragma: no cover
    _HAS_RICH = False


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    level_value = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(level_value)

    # Clear existing handlers (useful for reloads)
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    # Console handler
    if _HAS_RICH:
        console_handler = RichHandler(rich_tracebacks=False, show_time=False, show_level=True, show_path=False)
        console_handler.setLevel(level_value)
        console_handler.setFormatter(logging.Formatter(fmt))
    else:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level_value)
        console_handler.setFormatter(logging.Formatter(fmt))

    root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = TimedRotatingFileHandler(log_file, when="midnight", backupCount=7, encoding="utf-8")
        file_handler.setLevel(level_value)
        file_handler.setFormatter(logging.Formatter(fmt))
        root_logger.addHandler(file_handler)

    # Reduce noisy loggers
    logging.getLogger("httpx").setLevel(max(level_value, logging.WARNING))
    logging.getLogger("asyncio").setLevel(max(level_value, logging.INFO))


