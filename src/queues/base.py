from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from src.models import Message


class MessageQueue(ABC):
    """
    Abstract base class for message queues.
    
    Designed to support easy migration from in-memory queues to 
    production-ready systems like Kafka or RabbitMQ without 
    changing application code.
    """
    
    @abstractmethod
    async def enqueue(self, message: Message) -> None:
        """Enqueue a single message."""
        pass

    @abstractmethod
    async def dequeue(self) -> Optional[Message]:
        """Dequeue a single message. Returns None if no message available."""
        pass

    @abstractmethod
    async def size(self) -> int:
        """Get approximate queue size."""
        pass

