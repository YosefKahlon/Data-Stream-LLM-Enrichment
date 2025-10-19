import pytest
from unittest.mock import Mock, patch
from requests.exceptions import RequestException
from src.llm.client import LLMClient
from src.llm.llm_provider import LLMProvider


@pytest.fixture
def llm_client() -> LLMProvider:
    return LLMClient(
        base_url="http://localhost:11434",
        model="llama3",
        timeout=30
    )


class TestLLMClient:
    """Test LLM client functionality."""

    def test_implements_llm_provider_interface(self, llm_client):
        """Test that LLMClient implements LLMProvider interface."""
        assert isinstance(llm_client, LLMProvider)
        assert hasattr(llm_client, 'generate')
        assert hasattr(llm_client, 'health_check')
        assert callable(llm_client.generate)
        assert callable(llm_client.health_check)

    @patch('requests.post')
    def test_generate_success(self, mock_post, llm_client):
        """Test successful LLM generation - good scenario."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": '{"category": "internal", "description": "Test message", "emails": ["test@example.com"]}'
        }
        mock_post.return_value = mock_response
        prompt = "Analyze this message: Hello world"

        result = llm_client.generate(prompt)

        assert result is not None
        assert result["category"] == "internal"
        assert result["description"] == "Test message"
        assert result["emails"] == ["test@example.com"]

    @patch('requests.post')
    def test_generate_failure(self, mock_post, llm_client):
        """Test LLM generation failure - bad scenario."""
        mock_post.side_effect = RequestException("Service unavailable")

        with pytest.raises(RequestException):
            llm_client.generate("test prompt")
