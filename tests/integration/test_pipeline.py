import json
import pytest
import pytest_asyncio
from pathlib import Path
from src.app import EnrichmentApplication
from src.config import Config
from src.models import Category


class IntegrationTestConfig(Config):

    def __init__(self, test_dir: Path):
        super().__init__()
        self.INPUT_PATH = str(test_dir / "test_data.json")
        self.OUTPUT_PATH = str(test_dir / "test_results.json")
        self.MAX_CONCURRENCY = 1
        self.TIMEOUT_S = 60


@pytest.fixture(scope="module")  # ← Run ONCE for entire module
def test_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("shared_integration_test")


@pytest.fixture(scope="module")
def test_input(test_dir):
    import shutil
    source = Path(__file__).parent / "test_data.json"
    dest = test_dir / "test_data.json"
    shutil.copy(source, dest)
    return dest


@pytest.fixture(scope="module")
def test_config(test_dir, test_input):
    return IntegrationTestConfig(test_dir)


@pytest_asyncio.fixture(scope="module")
async def shared_results(test_config):
    """Run the pipeline once and share the results across tests in this module."""
    app = EnrichmentApplication(test_config)

    # Run pipeline once
    await app.initialize_components()
    messages = await app.load_dataset(test_config.INPUT_PATH)
    await app.enqueue_messages(messages)
    await app.start_processing()

    # Load and return results
    output_file = Path(test_config.OUTPUT_PATH)
    with open(output_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    return results


class TestPipeline:
    """Integration tests that share pipeline execution to save time."""

    @pytest.mark.asyncio
    async def test_pipeline_basic_validation(self, shared_results):

        assert len(shared_results) == 4, "Should have 4 results"

        for result in shared_results:
            assert "id" in result
            assert "success" in result
            assert isinstance(result["id"], int)
            assert isinstance(result["success"], bool)

            if result["success"]:
                assert "category" in result
                assert "description" in result
                assert "emails" in result
                assert isinstance(result["emails"], list)
            else:
                assert "error" in result
                assert isinstance(result["error"], str)

        success_count = sum(1 for r in shared_results if r["success"])
        assert success_count > 0, "At least some messages should succeed"

    @pytest.mark.asyncio
    async def test_validates_categories(self, shared_results):
        """Test category validation (uses shared results)."""
        valid_categories = {cat.value for cat in Category}

        for result in shared_results:
            if result["success"] and result.get("category"):
                assert result["category"] in valid_categories, \
                    f"Category '{result['category']}' is not valid"

    @pytest.mark.asyncio
    async def test_validates_emails(self, shared_results):
        """Test email validation (uses shared results)."""
        import re
        email_pattern = re.compile(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$')

        for result in shared_results:
            if result["success"]:
                emails = result.get("emails", [])

                for email in emails:
                    assert email_pattern.match(email), \
                        f"Email '{email}' has invalid format"
                    assert "@@" not in email, f"Email '{email}' contains @@"
                    assert ".." not in email, f"Email '{email}' contains .."
                    assert email == email.lower(), f"Email '{email}' should be lowercase"

                assert len(emails) == len(set(emails)), \
                    f"Emails should be unique, got duplicates: {emails}"

    @pytest.mark.asyncio
    async def test_description_word_limit(self, shared_results):
        """Test description word limits (uses shared results)."""
        for result in shared_results:
            if result["success"] and result.get("description"):
                word_count = len(result["description"].split())
                assert word_count <= 25, \
                    f"Description has {word_count} words, should be <= 25"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
