"""Unit tests for Message Processor."""
import pytest
from unittest.mock import Mock

from src.processors.message_processor import MessageProcessor
from src.models import Message, EnrichmentResult, Category
from src.validation.llm_response_validator import ValidatedLLMResponse


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    return Mock()


@pytest.fixture
def mock_validator():
    """Create mock validator."""
    return Mock()


@pytest.fixture
def sample_message():
    """Create sample message for testing."""
    return Message(id=1, text="Hello, please contact admin@company.com for support.")


class TestMessageProcessor:
    """Test message processor functionality."""
    
    def test_process_message_success(self, mock_llm_client, mock_validator, sample_message):
        """Test successful message processing - good scenario."""
        # Arrange
        mock_llm_response = {
            "category": "internal",
            "description": "Support request message",
            "emails": ["admin@company.com"]
        }
        sample_validated_response = ValidatedLLMResponse(
            category=Category.internal,
            description="Support request message",
            emails=["admin@company.com"]
        )
        mock_llm_client.generate.return_value = mock_llm_response
        mock_validator.validate.return_value = sample_validated_response

        processor = MessageProcessor(mock_llm_client, mock_validator)

        # Act
        result = processor.process(sample_message)

        # Assert
        assert isinstance(result, EnrichmentResult)
        assert result.success is True
        assert result.id == sample_message.id
        assert result.category == Category.internal
        assert result.description == "Support request message"
        assert result.emails == ["admin@company.com"]
        assert result.error is None

        # Verify interactions
        mock_llm_client.generate.assert_called_once()
        mock_validator.validate.assert_called_once_with(mock_llm_response)
    
    def test_process_message_failure(self, mock_llm_client, mock_validator, sample_message):
        """Test message processing failure - bad scenario."""
        # Arrange
        mock_llm_client.generate.side_effect = Exception("LLM service error")
        processor = MessageProcessor(mock_llm_client, mock_validator)
        
        # Act
        result = processor.process(sample_message)
        
        # Assert
        assert result.success is False
        assert result.id == sample_message.id
        assert "Processing error: LLM service error" in result.error
        assert result.category is None
        
        # Validator should not be called
        mock_validator.validate.assert_not_called()