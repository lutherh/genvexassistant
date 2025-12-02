"""Tests for sequence manager."""

import pytest
from threading import Thread
from genvexassistant.sequence import SequenceManager


class TestSequenceManager:
    """Test SequenceManager class."""
    
    def test_initial_sequence(self):
        """Test initial sequence number is 0."""
        manager = SequenceManager()
        assert manager.current == 0
    
    def test_next_sequence(self):
        """Test getting next sequence number."""
        manager = SequenceManager()
        assert manager.next() == 0
        assert manager.next() == 1
        assert manager.next() == 2
    
    def test_sequence_wraps_at_256(self):
        """Test sequence wraps around at 256."""
        manager = SequenceManager()
        
        # Set to 254
        for _ in range(254):
            manager.next()
        
        assert manager.next() == 254
        assert manager.next() == 255
        assert manager.next() == 0  # Wraps around
        assert manager.next() == 1
    
    def test_reset(self):
        """Test resetting sequence counter."""
        manager = SequenceManager()
        
        manager.next()
        manager.next()
        manager.next()
        
        manager.reset()
        assert manager.current == 0
        assert manager.next() == 0
    
    def test_current_does_not_increment(self):
        """Test that current property doesn't increment."""
        manager = SequenceManager()
        
        manager.next()  # Increment to 1
        
        assert manager.current == 1
        assert manager.current == 1  # Still 1
        assert manager.current == 1  # Still 1
    
    def test_thread_safety(self):
        """Test thread-safe operation."""
        manager = SequenceManager()
        results = []
        
        def get_sequences():
            for _ in range(100):
                results.append(manager.next())
        
        # Create multiple threads
        threads = [Thread(target=get_sequences) for _ in range(10)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check we got 1000 unique sequence numbers (with wrapping)
        assert len(results) == 1000
        # Check all values are in valid range
        assert all(0 <= seq < 256 for seq in results)
        # Check we have no duplicates in first 256 entries
        # (before wrapping could occur)
        first_256 = results[:256]
        assert len(set(first_256)) == 256
