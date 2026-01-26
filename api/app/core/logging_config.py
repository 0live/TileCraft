import logging
import sys

from app.core.config import get_settings


def setup_logging():
    log_level = logging.DEBUG if get_settings().env == "dev" else logging.INFO

    logger = logging.getLogger("tilecraft")
    logger.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger


logger = setup_logging()
