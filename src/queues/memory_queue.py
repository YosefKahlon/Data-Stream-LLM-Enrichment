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

    # Convenience synchronous, non-blocking method that mirrors the
    # previous behaviour. Use only from non-async code paths.
    def dequeue_nowait(self) -> Optional[Message]:
        """Get a message without awaiting; returns None if empty."""
        try:
            return self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return None
    
    async def size(self) -> int:
        """
        Get the current size of the queue.
        
        Returns:
            The number of messages currently in the queue.
        """
        return self._queue.qsize()
    
    async def enqueue_async(self, message: Message) -> None:
        """Compatibility wrapper: delegates to `enqueue`."""
        await self.enqueue(message)
    
    async def dequeue_async(self) -> Message:
        """Blocking async dequeue: wait until an item is available."""
        return await self._queue.get()
    
    async def dequeue_async_timeout(self, timeout: float) -> Optional[Message]:
        """
        Remove and return a message from the queue with a timeout.
        
        Args:
            timeout: Maximum time to wait for a message in seconds.
            
        Returns:
            The message from the queue, or None if timeout occurs.
        """
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
    
