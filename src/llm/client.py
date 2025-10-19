import json
from src.config import logger
from typing import Optional, Dict, Any
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError as ReqConnectionError
from src.config import config
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception, RetryCallState
from .llm_provider import LLMProvider


def _is_retryable_exception(exc: Exception) -> bool:
    """Check if exception is retryable."""
    # Retry on timeouts, connection errors, retryable HTTP status, and JSON decode errors
    if isinstance(exc, (Timeout, ReqConnectionError, json.JSONDecodeError, ValueError)):
        return True
    if isinstance(exc, RequestException):
        # Check for retryable HTTP status codes in the exception message
        for code in config.RETRY_STATUS_CODES:
            if str(code) in str(exc):
                return True
    return False


def _log_retry(retry_state: RetryCallState):
    logger.warning(
        f"LLM retrying (attempt {retry_state.attempt_number}) after exception: {retry_state.outcome.exception()}"
    )


class LLMClient(LLMProvider):
    """Client for interacting with Ollama LLM service."""

    def __init__(self, base_url: str, model: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.endpoint = f"{self.base_url}/api/generate"

        logger.info(f"LLM Client initialized: {self.endpoint}, model={self.model}")

    @retry(
        stop=stop_after_attempt(max(1, config.RETRIES + 1)),
        wait=wait_exponential_jitter(
            initial=config.RETRY_BACKOFF_BASE_S,
            max=config.RETRY_BACKOFF_MAX_S,
            jitter=config.RETRY_JITTER_S
        ),
        retry=retry_if_exception(_is_retryable_exception),
        after=_log_retry,
        reraise=True
    )
    def generate(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Send prompt to LLM and get response.
        Args:
            prompt: Text prompt to send to LLM
        Returns:
            Parsed JSON response from LLM, or None if failed
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"  # Expecting JSON formatted response
        }

        response = requests.post(
            self.endpoint,
            json=payload,
            timeout=self.timeout
        )
        if response.status_code in config.RETRY_STATUS_CODES:
            raise RequestException(f"Retryable HTTP status: {response.status_code}")
        response.raise_for_status()
        result = response.json()
        llm_output = result.get('response', '')
        if not llm_output:
            raise ValueError("LLM returned empty response")
        parsed = json.loads(llm_output)
        logger.info("LLM response parsed successfully")
        return parsed

    def health_check(self) -> bool:
        """
        Check if Ollama service is reachable.
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            logger.info("LLM service health check: OK")
            return True
        except Exception as e:
            logger.error(f"LLM service health check failed: {str(e)}")
            return False
