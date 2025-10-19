from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from src.models import Category


@dataclass
class EnrichmentResult:
    id: int
    success: bool
    category: Optional[Category] = None
    description: Optional[str] = None
    emails: Optional[List[str]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        if self.success:
            return {
                "id": self.id,
                "success": self.success,
                "category": self.category,
                "description": self.description,
                "emails": self.emails or []
            }
        else:
            return {
                "id": self.id,
                "success": self.success,
                "error": self.error
            }




