"""Entry point for the LLM enrichment pipeline."""
import asyncio

from src.config import logger, config
from src.app import EnrichmentApplication


async def pipeline():
    """
    Main pipeline execution.
    
    Orchestrates the complete enrichment workflow:
    1. Initialize application components
    2. Load input dataset
    3. Enqueue messages (with idempotency)
    4. Process messages concurrently
    5. Write results and report metrics
    """
    app = EnrichmentApplication(config)
    await app.initialize_components()
    messages = await app.load_dataset(config.INPUT_PATH)
    await app.enqueue_messages(messages)
    await app.start_processing()


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("LLM ENRICHMENT PIPELINE - START")
    logger.info("=" * 70)

    asyncio.run(pipeline())

