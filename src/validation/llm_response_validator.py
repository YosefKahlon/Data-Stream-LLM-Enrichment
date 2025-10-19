from __future__ import annotations
import re
from typing import List
from src.models import Category, ValidatedLLMResponse


class LLMResponseValidator:
    """Validator for normalizing and validating LLM response payloads."""

    def __init__(self, description_word_limit: int = 25) -> None:
        self.description_word_limit = description_word_limit
        self._email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    def validate(self, llm_response: dict) -> ValidatedLLMResponse:
        """Validate and normalize all relevant fields from the LLM response."""
        category = self._extract_category(llm_response)
        description = self._extract_description(llm_response)
        emails = self._extract_emails(llm_response)
        return ValidatedLLMResponse(
            category=category,
            description=description,
            emails=emails,
        )

    @staticmethod
    def _extract_category(llm_response: dict) -> Category:
        raw = llm_response.get('category', '')
        if not isinstance(raw, str):
            raise ValueError(f"Category must be a string, got {type(raw).__name__}")
        value = raw.lower().strip()
        try:
            return Category(value)
        except ValueError:
            raise ValueError(f"Invalid category: '{raw}'. Must be one of {[c.value for c in Category]}")

    def _extract_description(self, llm_response: dict) -> str:
        raw = llm_response.get('description', '')
        if not raw:
            return ''
        text = str(raw).strip()
        words = text.split()
        if self.description_word_limit and len(words) > self.description_word_limit:
            return ' '.join(words[: self.description_word_limit])
        return text

    def _extract_emails(self, llm_response: dict) -> List[str]:
        raw = llm_response.get('emails', [])
        if not isinstance(raw, list):
            return []
        normalized_emails: set[str] = set()
        for item in raw:
            if not isinstance(item, str):
                continue
            email = item.lower().strip()
            if self._is_valid_email(email):
                normalized_emails.add(email)
        return sorted(normalized_emails)

    def _is_valid_email(self, email: str) -> bool:
        if not self._email_pattern.match(email):
            return False
        if '@@' in email or '..' in email:
            return False
        return True
