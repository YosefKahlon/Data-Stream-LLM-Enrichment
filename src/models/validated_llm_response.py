from dataclasses import dataclass
from typing import Optional, List
from src.models import Category


@dataclass(frozen=True)
class ValidatedLLMResponse:
    """Normalized, validated fields extracted from an LLM response."""
    category: Optional[Category]
    description: str
    emails: List[str]