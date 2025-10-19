from typing import Final

INSTRUCTION: Final[str] = (
    "You are an information extractor. Return ONLY JSON with keys: "
    "category (one of ['phishing','newsletter','internal']), "
    "description (<=25 words), emails (list of unique, lowercase emails mentioned)."
)

EMAIL_EXTRACTION_RULES: Final[str] = """Email extraction rules:"
    "- Only extract email addresses that appear exactly in the text."
    "- Do NOT create, guess, or correct email addresses."
    "- If an email is malformed (e.g. contains invalid characters, or multiple '@' symbols), DO NOT include it."
    "- The emails list MUST contain only syntactically valid emails found in the text."
    "- If no valid email addresses appear, return an empty list []."""


def build_extraction_prompt(message_text: str) -> str:
    return f"""{INSTRUCTION}

{EMAIL_EXTRACTION_RULES}

Message to analyze:
{message_text}"""
