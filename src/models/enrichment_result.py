from dataclasses import dataclass
from typing import Optional, List
from src.models import Category


@dataclass
class EnrichmentResult:
    id: int
    success: bool
    category: Optional[Category] = None
    description: Optional[str] = None
    emails: Optional[List[str]] = None
    error: Optional[str] = None
