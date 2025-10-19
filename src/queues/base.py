from abc import ABC, abstractmethod
from typing import Optional

from src.models import Message


class MessageQueue(ABC):
    @abstractmethod
    async def enqueue(self, message: Message) -> None:
        pass

    @abstractmethod
    async def dequeue(self) -> Optional[Message]:
        pass

    @abstractmethod
    async def size(self) -> int:
        pass
