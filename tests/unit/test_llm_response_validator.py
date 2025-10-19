import pytest
from src.validation.llm_response_validator import LLMResponseValidator

@pytest.fixture
def validator():
    return LLMResponseValidator()

def test_email_extraction_and_normalization(validator):
    llm_output = {
        "category": "internal",
        "description": "This is a valid description.",
        "emails": [
            "Admin@Company.com",  # should be lowercased
            "user@@company.com",  # invalid
            "admin@company.com",  # duplicate (after normalization)
            "user@company..com",  # invalid
            "valid.user@company.com"
        ]
    }
    result = validator.validate(llm_output)
    # Only valid, lowercased, deduped emails remain
    assert set(result.emails) == {"admin@company.com", "valid.user@company.com"}
    assert all(e == e.lower() for e in result.emails)
    assert not any("@@" in e or ".." in e for e in result.emails)

def test_category_and_description_validation(validator):
    llm_output = {
        "category": "internal",  # valid category
        "description": "word " * 30,  # too long
        "emails": []
    }
    result = validator.validate(llm_output)
    # Description should be trimmed to 25 words
    assert len(result.description.split()) <= 25
    assert result.category == "internal"

    # Invalid category
    bad_output = dict(llm_output)
    bad_output["category"] = "not_a_category"
    with pytest.raises(ValueError):
        validator.validate(bad_output)

        


