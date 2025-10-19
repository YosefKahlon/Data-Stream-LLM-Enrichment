import os
from pathlib import Path
from src.logging_config import setup_logger


class Config:
    # LLM service settings
    LLM_URL = os.getenv("LLM_URL", "http://localhost:11434")
    MODEL_NAME = os.getenv("MODEL_NAME", "llama3:latest")
    TIMEOUT_S = int(os.getenv("TIMEOUT_S", "60"))

    # Retry configuration
    RETRIES = int(os.getenv("RETRIES", "3"))
    RETRY_BACKOFF_BASE_S = float(os.getenv("RETRY_BACKOFF_BASE_S", "1.0"))
    RETRY_BACKOFF_MAX_S = float(os.getenv("RETRY_BACKOFF_MAX_S", "30.0"))
    RETRY_JITTER_S = float(os.getenv("RETRY_JITTER_S", "0.25"))
    # Comma-separated list of HTTP status codes to retry on
    RETRY_STATUS_CODES = tuple(
        int(code.strip()) for code in os.getenv("RETRY_STATUS_CODES", "429,500,502,503,504").split(",") if code.strip()
    )

    # Concurrency settings
    MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "1"))

    # File paths and queue settings
    INPUT_PATH = os.getenv("INPUT_PATH", str(Path(__file__).parent.parent / "data" / "dev_emails_150.json"))
    OUTPUT_PATH = os.getenv("OUTPUT_PATH", str(Path(__file__).parent.parent / "output" / "results.json"))

    # Queue settings
    QUEUE_TYPE = os.getenv("QUEUE_TYPE", "memory")  # Options: memory, rabbitmq


config = Config()
logger = setup_logger("Pipeline", "INFO")
