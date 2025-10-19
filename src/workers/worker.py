from typing import List
from src.queues.base import MessageQueue
from src.processors.message_processor import MessageProcessor
from src.models import EnrichmentResult
from src.config import logger


class Worker:
    """Worker that processes messages from a queue."""

    def __init__(self, queue: MessageQueue, processor: MessageProcessor):
        """
        Initialize worker.
        
        Args:
            queue: Message queue to pull from
            processor: Message processor for enrichment
        """
        self.queue = queue
        self.processor = processor
        self.results: List[EnrichmentResult] = []
        

    async def process_all(self) -> List[EnrichmentResult]:
        """
        Process messages from the queue until empty.
        
        Returns:
            List of enrichment results processed by this worker
        """
        logger.info(f"Worker starting to process messages...")

        processed_count = 0
        success_count = 0
        failure_count = 0

        while True:
            # Get next message from queue
            message = await self.queue.dequeue()

            if message is None:
                # Queue is empty
                logger.info("No more messages in queue")
                break

            # Process the message directly
            try:
                result = self.processor.process(message)
            except Exception as e:
                logger.exception(
                    f"Unhandled exception processing message {getattr(message, 'id', None)}: {e}")
                result = EnrichmentResult(id=message.id, success=False, error=str(e))

            # Collect the result
            self.results.append(result)

            processed_count += 1
            if result.success:
                success_count += 1
            else:
                failure_count += 1

            # Log progress every 10 messages
            if processed_count % 10 == 0:
                logger.info(
                    f"Progress: {processed_count} processed "
                    f"({success_count} success, {failure_count} failed)"
                )

        logger.info(
            f"{processed_count} total, "
            f"{success_count} success, {failure_count} failed"
        )
        return self.results

    def get_results(self) -> List[EnrichmentResult]:
        """Get all processing results."""
        return self.results
