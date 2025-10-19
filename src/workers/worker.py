import asyncio
from typing import List
from src.queues.base import MessageQueue
from src.processors.message_processor import MessageProcessor
from src.models import EnrichmentResult
from src.config import logger


class Worker:
    """Worker that processes messages from a queue concurrently with other workers."""

    def __init__(self, worker_id: int, queue: MessageQueue, processor: MessageProcessor):
        """
        Initialize worker.
        
        Args:
            worker_id: Unique identifier for this worker
            queue: Message queue to pull from (shared across workers)
            processor: Message processor for enrichment
        """
        self.worker_id = worker_id
        self.queue = queue
        self.processor = processor
        self.results: List[EnrichmentResult] = []
        logger.info(f"Worker {self.worker_id} initialized")

    async def process_all(self) -> List[EnrichmentResult]:
        """
        Process messages from the queue until empty.
        This worker will compete with other workers for messages.
        
        Returns:
            List of enrichment results processed by this worker
        """
        logger.info(f"Worker {self.worker_id} starting to process messages...")

        processed_count = 0
        success_count = 0
        failure_count = 0

        while True:
            # Get next message from queue (thread-safe dequeue)
            message = await self.queue.dequeue()

            if message is None:
                # Queue is empty
                logger.info(f"Worker {self.worker_id}: No more messages in queue")
                break

            # Process the message (synchronous processor, run in executor to not block)
            loop = asyncio.get_event_loop()
            try:
                result = await loop.run_in_executor(None, self.processor.process, message)
            except Exception as e:
                logger.exception(
                    f"Worker {self.worker_id}: Unhandled exception processing message {getattr(message, 'id', None)}: {e}")
                # Synthesize a failure result so pipeline can continue
                result = EnrichmentResult(id=message.id if hasattr(message, 'id') else -1, success=False, error=str(e))

            self.results.append(result)

            processed_count += 1
            if result.success:
                success_count += 1
            else:
                failure_count += 1

            # Log progress every 10 messages per worker
            if processed_count % 10 == 0:
                logger.info(
                    f"Worker {self.worker_id} progress: {processed_count} processed "
                    f"({success_count} success, {failure_count} failed)"
                )
            # Cooperative yield to event loop on tight loops
            await asyncio.sleep(0)

        logger.info(
            f"Worker {self.worker_id} finished: {processed_count} total, "
            f"{success_count} success, {failure_count} failed"
        )
        return self.results

    def get_results(self) -> List[EnrichmentResult]:
        """Get all processing results."""
        return self.results
