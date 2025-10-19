import json
from abc import ABC, abstractmethod
from src.config import logger
from pathlib import Path
from typing import List
from src.models import EnrichmentResult


class ResultWriterInterface(ABC):
    """Abstract base class for writing enrichment results."""

    @abstractmethod
    def write(self, results: List[EnrichmentResult]) -> None:
        """
        Write results to output.
        
        Args:
            results: List of enrichment results to write
        """
        pass


class ResultWriter(ResultWriterInterface):
    """Writes enrichment results to JSON file."""

    def __init__(self, output_path: str):
        """
        Initialize result writer.
        
        Args:
            output_path: Path to output JSON file
        """
        self.output_path = Path(output_path)
        logger.info(f"ResultWriter initialized: {self.output_path}")

    def write(self, results: List[EnrichmentResult]) -> None:
        """
        Write results to JSON file.
        
        Args:
            results: List of enrichment results to write
        """
        try:
            # Ensure output directory exists
            self.output_path.parent.mkdir(parents=True, exist_ok=True)

            output_data = []
            for result in results:
                result_dict = {
                    "id": result.id,
                    "success": result.success
                }

                if result.success:
                    result_dict["category"] = result.category.value
                    result_dict["description"] = result.description
                    result_dict["emails"] = result.emails
                else:
                    result_dict["error"] = result.error

                output_data.append(result_dict)

            # Write to file
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Successfully wrote {len(results)} results to {self.output_path}")

        except Exception as e:
            logger.error(f"Failed to write results: {e}")
            raise
