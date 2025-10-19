from typing import Dict, Type
from src.config import Config
from .base import MessageQueue
from .memory_queue import InMemoryQueue


class QueueFactory:
    """
    Factory for creating message queue instances.
    
    Supports easy migration between queue types by centralizing
    queue creation logic. To add a new queue type:
    1. Implement the MessageQueue interface
    2. Register it in _queue_types
    3. Add configuration in Config class
    """

    _queue_types: Dict[str, Type[MessageQueue]] = {
        "memory": InMemoryQueue,
        # Future queue types will be added here:
        # "kafka": KafkaQueue,
        # "rabbitmq": RabbitMQQueue,
    }

    @classmethod
    async def create_queue(cls, config: Config) -> MessageQueue:
        """
        Create a queue instance based on configuration.
        
        Args:
            config: Application configuration containing queue settings
            
        Returns:
            MessageQueue instance of the configured type
            
        Raises:
            ValueError: If queue type is not supported
        """
        queue_type = config.QUEUE_TYPE.lower()

        if queue_type not in cls._queue_types:
            available_types = ", ".join(cls._queue_types.keys())
            raise ValueError(
                f"Unsupported queue type: '{queue_type}'. "
                f"Available types: {available_types}"
            )

        queue_class = cls._queue_types[queue_type]

        # Create queue with type-specific configuration
        if queue_type == "memory":
            queue = queue_class(maxsize=config.MEMORY_QUEUE_MAX_SIZE)
        # Future queue implementations will have their own config:
        # elif queue_type == "kafka":
        # elif queue_type == "rabbitmq":
        else:
            # Fallback for new queue types without custom configuration
            queue = queue_class()


        return queue

    @classmethod
    def register_queue_type(cls, name: str, queue_class: Type[MessageQueue]) -> None:
        """
        Register a new queue type.
        
        This allows external packages to register custom queue implementations.
        
        Args:
            name: Queue type name (used in configuration)
            queue_class: Queue implementation class
        """
        cls._queue_types[name] = queue_class

    @classmethod
    def get_available_types(cls) -> list[str]:
        """Get list of available queue types."""
        return list(cls._queue_types.keys())
