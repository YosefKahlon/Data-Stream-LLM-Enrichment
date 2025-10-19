import asyncio
from typing import Optional
from .base import MessageQueue
from ..models.message import Message


class InMemoryQueue(MessageQueue):
    def __init__(self, maxsize: int = 0):
        """
        Initialize the in-memory queue with asyncio.Queue.
        
        Args:
            maxsize: Maximum size of the queue. 0 means unlimited.
        """
        self._queue = asyncio.Queue(maxsize=maxsize)

    async def enqueue(self, message: Message) -> None:
        """
        Add a message to the queue asynchronously.

        This matches the async interface declared on `MessageQueue`.

        Args:
            message: The message to add to the queue.
        """
        try:
            await self._queue.put(message)
        except Exception as e:
            raise RuntimeError(f"Failed to enqueue message: {e}")

    async def dequeue(self) -> Optional[Message]:
        """
        Remove and return a message from the queue asynchronously.

        Returns:
            The message from the queue, or None if the queue is empty (non-blocking behaviour).
        """
        try:
            return self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    async def size(self) -> int:
        return self._queue.qsize()
