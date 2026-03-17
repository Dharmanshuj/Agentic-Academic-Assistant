import logging
import os

# Create logs directory if not exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "ai_audit.log")

logger = logging.getLogger("ai_audit")

if not logger.handlers:
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)


def log_tool_usage(tool_name: str, query: str):
    logger.info(f"TOOL_USED={tool_name} | QUERY={query}")


def log_security_event(event: str, details: str):
    logger.warning(f"SECURITY_EVENT={event} | DETAILS={details}")