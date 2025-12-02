"""Sequence number manager for Genvex communication."""

import threading


class SequenceManager:
    """Manages sequence numbers for Genvex protocol communication.
    
    Sequence numbers are used to match requests with responses.
    They cycle from 0 to 255.
    """
    
    def __init__(self):
        """Initialize sequence manager."""
        self._sequence = 0
        self._lock = threading.Lock()
    
    def next(self) -> int:
        """Get next sequence number.
        
        Returns:
            int: Next sequence number (0-255)
        """
        with self._lock:
            current = self._sequence
            self._sequence = (self._sequence + 1) % 256
            return current
    
    def reset(self):
        """Reset sequence counter to 0."""
        with self._lock:
            self._sequence = 0
    
    @property
    def current(self) -> int:
        """Get current sequence number without incrementing.
        
        Returns:
            int: Current sequence number
        """
        with self._lock:
            return self._sequence
