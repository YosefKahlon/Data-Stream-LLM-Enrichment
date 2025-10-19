from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Generate response from LLM."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if LLM service is available."""
        pass
