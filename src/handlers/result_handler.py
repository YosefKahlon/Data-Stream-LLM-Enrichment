import json
import os
from abc import ABC, abstractmethod
from pathlib import Path

from src.models import EnrichmentResult
from src.config import logger


class ResultHandler(ABC):
    """Abstract base class for handling processing results."""

 
    @abstractmethod
    async def write(self, results: list[EnrichmentResult]) -> None:
        """Called when all processing is complete with all results."""
        pass


class OutputFileHandler(ResultHandler):

    def __init__(self, output_path: str):
        self.output_path = output_path



    async def write(self, results: list[EnrichmentResult]) -> None:
        """Write all results to file, overwriting any existing data."""
        try:
            # Convert results to dictionaries
            new_results = [result.to_dict() for result in results]

            # Ensure output directory exists
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

            # Write all results to file (overwrite)
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(new_results, f, indent=2, ensure_ascii=False)

            logger.info(f"Total results written: {len(new_results)}")
        except Exception as e:
            logger.error(f"Failed to write results to {self.output_path}: {e}")


