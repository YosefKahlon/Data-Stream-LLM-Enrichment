from typing import List, Optional
import time
import json
from pathlib import Path
from src.config import logger, Config
from src.models import Message
from src.queues import MessageQueue, QueueFactory
from src.llm.client import LLMClient
from src.llm import LLMProvider
from src.processors.message_processor import MessageProcessor
from src.workers.worker import Worker
from src.handlers import OutputFileHandler


class EnrichmentApplication:
    """
    Main application class that orchestrates the LLM enrichment pipeline.
    
    Responsibilities:
    - Initialize and manage pipeline components (queue, LLM client, processor, etc.)
    - Load input dataset
    - Enqueue messages with idempotency support
    - Process messages 
    - Write results and report metrics
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = logger
        self.queue: Optional[MessageQueue] = None
        self.llm_client: Optional[LLMProvider] = None
        self.processor: Optional[MessageProcessor] = None
        self.worker: Optional[Worker] = None
        self.result_handler: Optional[OutputFileHandler] = None

    async def initialize_components(self) -> None:
        """Initialize all components needed for processing."""
        self.logger.info("Initializing components...")

        self.queue = await QueueFactory.create_queue(self.config)

        # Create LLM client
        self.llm_client = LLMClient(
            base_url=self.config.LLM_URL,
            model=self.config.MODEL_NAME,
            timeout=self.config.TIMEOUT_S
        )

        self.logger.info(
            f"LLM retry config: retries={self.config.RETRIES}, backoff_base_s={self.config.RETRY_BACKOFF_BASE_S}, "
            f"backoff_max_s={self.config.RETRY_BACKOFF_MAX_S}, jitter_s={self.config.RETRY_JITTER_S}, "
            f"retry_status_codes={self.config.RETRY_STATUS_CODES}"
        )

        # Health check LLM service
        if not self.llm_client.health_check():
            self.logger.error("LLM service health check failed")
            raise RuntimeError("LLM service is not available. Please ensure Ollama is running.")

        self.processor = MessageProcessor(self.llm_client)

        # Create and initialize result handler
        self.result_handler = OutputFileHandler(self.config.OUTPUT_PATH)

        # Create single worker
        self.worker = Worker(
            queue=self.queue,
            processor=self.processor,
        )

        self.logger.info("All components initialized successfully")

    async def load_dataset(self, dataset_path: str) -> List[Message]:
        """
        Load dataset from JSON file and convert to Message objects.
        
        Args:
            dataset_path: Path to the JSON dataset file
            
        Returns:
            List of Message objects
            
        Raises:
            FileNotFoundError: If dataset file doesn't exist
            Exception: If dataset parsing fails
        """
        self.logger.info(f"Loading dataset from {dataset_path}")

        try:
            dataset_file = Path(dataset_path)
            if not dataset_file.exists():
                raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

            with open(dataset_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            messages = []
            if isinstance(data, list):
                # Array of message objects
                for i, item in enumerate(data):
                    if isinstance(item, dict):
                        message = Message(
                            id=item.get('id', i),
                            text=item.get('text', item.get('message', ''))
                        )
                        messages.append(message)
                    elif isinstance(item, str):
                        # Simple array of strings
                        message = Message(id=i, text=item)
                        messages.append(message)
            elif isinstance(data, dict):
                # Single message object or object with messages array
                if 'messages' in data:
                    for i, item in enumerate(data['messages']):
                        message = Message(
                            id=item.get('id', i),
                            text=item.get('text', item.get('message', ''))
                        )
                        messages.append(message)
                else:
                    # Single message
                    message = Message(
                        id=data.get('id', 0),
                        text=data.get('text', data.get('message', ''))
                    )
                    messages.append(message)

            self.logger.info(f"Loaded {len(messages)} messages from dataset")
            return messages

        except Exception as e:
            self.logger.error(f"Failed to load dataset: {e}")
            raise

    async def enqueue_messages(self, messages: List[Message]) -> None:
        """
        Enqueue messages for processing.

        Args:
            messages: List of Message objects to enqueue
        """
        self.logger.info(f"Enqueueing {len(messages)} messages...")

        enqueued_count = 0

        for message in messages:

            try:
                await self.queue.enqueue(message)
                enqueued_count += 1
            except Exception as e:
                self.logger.error(f"Failed to enqueue message {message.id}: {e}")

        self.logger.info(f"Enqueued {enqueued_count} messages for processing")

    async def start_processing(self) -> None:
        """
        Start processing messages from the queue with streaming results.
        
        This method:
        1. Starts the worker to process messages from the queue
        2. Waits for worker to complete all messages
        3. Saves results to file
        4. Reports performance metrics
        
        """
        self.logger.info(f"Starting message processing ...")

        start_time = time.time()

        results = await self.worker.process_all()

        end_time = time.time()
        elapsed_time = end_time - start_time

        # Save results to file 
        self.logger.info("Saving results to file...")
        save_start = time.time()
        await self.result_handler.write(results)
        save_time = time.time() - save_start
        self.logger.info(f"Results saved in {save_time:.2f} seconds")

        # Calculate performance metrics
        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count
        messages_per_second = len(results) / elapsed_time if elapsed_time > 0 else 0
        avg_time_per_message = elapsed_time / len(results) if results else 0

        self.logger.info("=" * 70)
        self.logger.info("PROCESSING COMPLETE")
        self.logger.info("=" * 70)
        self.logger.info(f"Total messages: {len(results)}")
        self.logger.info(f"Successful: {success_count}")
        self.logger.info(f"Failed: {failure_count}")
        self.logger.info(f"Processing mode: Single worker with streaming results")
        self.logger.info("-" * 70)
        self.logger.info(f"Total time: {elapsed_time:.2f} seconds ({elapsed_time / 60:.2f} minutes)")
        self.logger.info(f"Average time per message: {avg_time_per_message:.2f} seconds")
        self.logger.info(f"Throughput: {messages_per_second:.2f} messages/second")
        self.logger.info("-" * 70)
        self.logger.info(f"Results streamed to: {self.config.OUTPUT_PATH}")
        self.logger.info("=" * 70)
