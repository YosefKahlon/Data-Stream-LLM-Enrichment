from typing import List, Optional
import asyncio
import time
import json
from pathlib import Path

from src.config import logger, Config
from src.models import Message
from src.queues import MessageQueue, InMemoryQueue
from src.llm.client import LLMClient
from src.llm import LLMProvider
from src.processors.message_processor import MessageProcessor
from src.workers.worker import Worker
from src.output_writer import ResultWriter, ResultWriterInterface


class EnrichmentApplication:
    """
    Main application class that orchestrates the LLM enrichment pipeline.
    
    Responsibilities:
    - Initialize and manage pipeline components (queue, LLM client, workers, etc.)
    - Load input dataset
    - Enqueue messages with idempotency support
    - Coordinate concurrent message processing
    - Write results and report metrics
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logger
        self.queue: Optional[MessageQueue] = None
        self.llm_client: Optional[LLMProvider] = None
        self.processor: Optional[MessageProcessor] = None
        self.workers: List[Worker] = []
        self.output_writer: Optional[ResultWriterInterface] = None

    async def initialize_components(self) -> None:
        """Initialize all components needed for processing."""
        self.logger.info("Initializing components...")
        
        self.queue = await self._create_queue()
        
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
        
        num_workers = self.config.MAX_CONCURRENCY
        self.logger.info(f"Creating {num_workers} concurrent workers...")
        self.workers = []
        for i in range(num_workers):
            worker = Worker(worker_id=(i + 1), queue=self.queue, processor=self.processor)
            self.workers.append(worker)

        # Create output writer
        self.output_writer = ResultWriter(self.config.OUTPUT_PATH)
        
        self.logger.info("All components initialized successfully")

    async def _create_queue(self) -> MessageQueue:
        """Create and configure message queue based on configuration."""
        if self.config.QUEUE_TYPE == "memory":
            return InMemoryQueue()
        else:
            raise ValueError(f"Unsupported queue type: {self.config.QUEUE_TYPE}")

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

    def _load_processed_ids(self) -> set[int]:
        """
        Load set of already-processed message IDs from output file.
        
        Implements idempotency by reading existing results and extracting
        IDs of successfully completed messages. This allows the pipeline
        to safely restart after crashes without re-processing messages.
        
        Returns:
            Set of message IDs that have been successfully processed.
            Returns empty set if file doesn't exist or can't be parsed.
        """
        output_path = Path(self.config.OUTPUT_PATH)
        
        # Return empty set if output file doesn't exist yet
        if not output_path.exists():
            self.logger.debug("Output file does not exist yet - no messages processed")
            return set()
        
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # Extract IDs of successfully processed messages only
            processed_ids = {
                r['id'] for r in results 
                if isinstance(r, dict) and r.get('success') is True
            }
            
            self.logger.info(f"Found {len(processed_ids)} already processed messages")
            return processed_ids
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"Could not parse output file (corrupted JSON): {e}")
            self.logger.warning("Treating all messages as new")
            return set()
        except Exception as e:
            self.logger.warning(f"Could not load processed IDs: {e}")
            self.logger.warning("Treating all messages as new")
            return set()

    async def enqueue_messages(self, messages: List[Message]) -> None:
        """
        Enqueue messages for processing, skipping already processed ones.
        
        Implements idempotency by checking existing results before enqueueing.
        Messages that have already been successfully processed are skipped.
        
        Args:
            messages: List of Message objects to enqueue
        """
        self.logger.info(f"Enqueueing {len(messages)} messages...")

        # Load already processed message IDs for idempotency
        processed_ids = self._load_processed_ids()

        enqueued_count = 0
        skipped_count = 0

        for message in messages:
            # Skip if already successfully processed
            if message.id in processed_ids:
                skipped_count += 1
                continue

            try:
                await self.queue.enqueue(message)
                enqueued_count += 1
            except Exception as e:
                self.logger.error(f"Failed to enqueue message {message.id}: {e}")

        self.logger.info(f"Enqueued {enqueued_count} messages, skipped {skipped_count} already processed")

    async def start_processing(self) -> None:
        """
        Start processing messages from the queue with concurrent workers.
        
        This method:
        1. Launches all workers concurrently
        2. Waits for all workers to complete
        3. Collects and sorts results
        4. Writes results to output file
        5. Reports performance metrics
        """
        num_workers = len(self.workers)
        self.logger.info(f"Starting message processing with {num_workers} concurrent workers...")
        
        # Start timing
        start_time = time.time()
        
        # Start all workers concurrently
        tasks = []
        for worker in self.workers:
            task = asyncio.create_task(worker.process_all())
            tasks.append(task)
        worker_results = await asyncio.gather(*tasks)

        # End timing
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Combine results from all workers
        all_results = []
        for results in worker_results:
            all_results.extend(results)
        
        # Sort results by message ID for consistent output
        all_results.sort(key=lambda r: r.id)
        
        # Write results to output file
        self.output_writer.write(all_results)
        
        # Print summary
        success_count = sum(1 for r in all_results if r.success)
        failure_count = len(all_results) - success_count
        
        # Calculate performance metrics
        messages_per_second = len(all_results) / elapsed_time if elapsed_time > 0 else 0
        avg_time_per_message = elapsed_time / len(all_results) if all_results else 0
        
        self.logger.info("=" * 70)
        self.logger.info("PROCESSING COMPLETE")
        self.logger.info("=" * 70)
        self.logger.info(f"Total messages: {len(all_results)}")
        self.logger.info(f"Successful: {success_count}")
        self.logger.info(f"Failed: {failure_count}")
        self.logger.info(f"Workers used: {num_workers}")
        self.logger.info("-" * 70)
        self.logger.info(f"Total time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
        self.logger.info(f"Average time per message: {avg_time_per_message:.2f} seconds")
        self.logger.info(f"Throughput: {messages_per_second:.2f} messages/second")
        self.logger.info("-" * 70)
        self.logger.info(f"Results saved to: {self.config.OUTPUT_PATH}")
        self.logger.info("=" * 70)
