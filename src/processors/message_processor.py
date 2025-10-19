from src.config import logger
from typing import Optional
from src.models import Message, EnrichmentResult
from src.llm import LLMProvider, build_extraction_prompt
from src.validation import LLMResponseValidator, ValidatedLLMResponse


class MessageProcessor:
    """Processes individual messages through LLM enrichment pipeline."""

    def __init__(self, llm_client: LLMProvider, validator: Optional[LLMResponseValidator] = None):
        """Initialize message processor.

        Args:
            llm_client: LLM provider for making inference requests
            validator: Optional validator for LLM responses (injected for testability)
        """
        self.llm_client = llm_client
        self.validator = validator or LLMResponseValidator()
        logger.info("MessageProcessor initialized")

    def process(self, message: Message) -> EnrichmentResult:
        """
        Process a single message through the enrichment pipeline.
        
        Args:
            message: Message to process
            
        Returns:
            EnrichmentResult with success status and extracted data or error
        """
        try:
            logger.debug(f"Processing message {message.id}")

            # Build prompt for LLM
            prompt = build_extraction_prompt(message.text)

            # Call LLM
            llm_response = self.llm_client.generate(prompt)

            if llm_response is None:
                logger.warning(f"LLM returned no response for message {message.id}")
                return EnrichmentResult(
                    id=message.id,
                    success=False,
                    error="Failed to get LLM response"
                )

            # Validate and extract fields via validator
            validated: ValidatedLLMResponse = self.validator.validate(llm_response)

            if validated.category is None:
                logger.warning(f"Invalid category in LLM response for message {message.id}")
                return EnrichmentResult(
                    id=message.id,
                    success=False,
                    error="Invalid category in LLM response"
                )

            return EnrichmentResult(
                id=message.id,
                success=True,
                category=validated.category,
                description=validated.description,
                emails=validated.emails,
            )

        except Exception as e:
            logger.error(f"Error processing message {message.id}: {str(e)}")
            return EnrichmentResult(
                id=message.id,
                success=False,
                error=f"Processing error: {str(e)}"
            )
