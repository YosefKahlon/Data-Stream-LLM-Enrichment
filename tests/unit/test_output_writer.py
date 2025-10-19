"""Unit tests for Result Writer."""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.output_writer import ResultWriter, ResultWriterInterface
from src.models import EnrichmentResult, Category


@pytest.fixture
def sample_results():
    """Create sample enrichment results for testing."""
    return [
        EnrichmentResult(
            id=1,
            success=True,
            category=Category.internal,
            description="Internal message",
            emails=["user@company.com"]
        ),
        EnrichmentResult(
            id=2,
            success=False,
            error="Processing failed"
        )
    ]


@pytest.fixture
def temp_output_path():
    """Create temporary file path for testing."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


class TestResultWriter:
    """Test result writer functionality."""
    
    def test_write_success(self, sample_results, temp_output_path):
        """Test successful result writing - good scenario."""
        writer = ResultWriter(temp_output_path)
        
        writer.write(sample_results)
        
        assert Path(temp_output_path).exists()
        
        with open(temp_output_path, 'r', encoding='utf-8') as f:
            written_data = json.load(f)
        
        assert len(written_data) == 2
        
        # Check successful result
        result1 = written_data[0]
        assert result1["id"] == 1
        assert result1["success"] is True
        assert result1["category"] == "internal"
        assert result1["description"] == "Internal message"
        assert result1["emails"] == ["user@company.com"]
        assert "error" not in result1
        
        # Check failed result
        result2 = written_data[1]
        assert result2["id"] == 2
        assert result2["success"] is False
        assert result2["error"] == "Processing failed"
        assert "category" not in result2
    
