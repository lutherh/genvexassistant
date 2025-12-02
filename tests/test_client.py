"""Tests for Genvex client."""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from genvexassistant.client import GenvexClient
from genvexassistant.protocol import Packet, PacketType, U_NOTIFY, U_CRYPT, U_REQUEST
from genvexassistant.exceptions import CommunicationError, TimeoutError, ProtocolError


class TestGenvexClient:
    """Test GenvexClient class."""
    
    def test_init(self):
        """Test client initialization."""
        client = GenvexClient(port="/dev/ttyUSB0")
        assert client.port == "/dev/ttyUSB0"
        assert client.baudrate == 9600
        assert client.timeout == 2.0
        assert client.max_retries == 10
        assert client.retry_delay == 0.1
        assert not client.is_connected()
    
    def test_init_custom_params(self):
        """Test client initialization with custom parameters."""
        client = GenvexClient(
            port="/dev/ttyUSB1",
            baudrate=19200,
            timeout=5.0,
            max_retries=20,
            retry_delay=0.2
        )
        assert client.port == "/dev/ttyUSB1"
        assert client.baudrate == 19200
        assert client.timeout == 5.0
        assert client.max_retries == 20
        assert client.retry_delay == 0.2
    
    @patch('genvexassistant.client.serial.Serial')
    def test_connect_success(self, mock_serial):
        """Test successful connection."""
        client = GenvexClient(port="/dev/ttyUSB0")
        client.connect()
        
        assert client.is_connected()
        mock_serial.assert_called_once()
    
    @patch('genvexassistant.client.serial.Serial')
    @patch('genvexassistant.client.serial.SerialException', Exception)
    def test_connect_failure(self, mock_serial):
        """Test connection failure."""
        import serial
        mock_serial.side_effect = serial.SerialException("Port not found")
        
        client = GenvexClient(port="/dev/ttyUSB0")
        
        with pytest.raises(CommunicationError):
            client.connect()
        
        assert not client.is_connected()
    
    @patch('genvexassistant.client.serial.Serial')
    def test_disconnect(self, mock_serial):
        """Test disconnection."""
        mock_instance = MagicMock()
        mock_instance.is_open = True
        mock_serial.return_value = mock_instance
        
        client = GenvexClient(port="/dev/ttyUSB0")
        client.connect()
        assert client.is_connected()
        
        client.disconnect()
        mock_instance.close.assert_called_once()
        assert not client.is_connected()
    
    @patch('genvexassistant.client.serial.Serial')
    def test_context_manager(self, mock_serial):
        """Test context manager usage."""
        mock_instance = MagicMock()
        mock_instance.is_open = True
        mock_serial.return_value = mock_instance
        
        with GenvexClient(port="/dev/ttyUSB0") as client:
            assert client.is_connected()
        
        mock_instance.close.assert_called_once()
    
    def test_send_command_not_connected(self):
        """Test sending command when not connected."""
        client = GenvexClient(port="/dev/ttyUSB0")
        
        with pytest.raises(CommunicationError):
            client.send_command(b'\x01\x02\x03')
    
    @patch('genvexassistant.client.serial.Serial')
    def test_send_command_no_response(self, mock_serial):
        """Test sending command without waiting for response."""
        mock_instance = MagicMock()
        mock_instance.is_open = True
        mock_serial.return_value = mock_instance
        
        client = GenvexClient(port="/dev/ttyUSB0")
        client.connect()
        
        result = client.send_command(b'\x01\x02\x03', wait_for_response=False)
        
        assert result is None
        mock_instance.write.assert_called_once()
        mock_instance.flush.assert_called_once()


class TestRetryMechanism:
    """Test retry mechanism for U_NOTIFY packets."""
    
    @patch('genvexassistant.client.serial.Serial')
    def test_receive_response_direct_crypt(self, mock_serial):
        """Test receiving U_CRYPT response directly without U_NOTIFY."""
        mock_instance = MagicMock()
        mock_instance.is_open = True
        mock_serial.return_value = mock_instance
        
        # Create U_CRYPT response packet
        crypt_packet = U_CRYPT(0, b'\xAA\xBB\xCC')
        crypt_bytes = crypt_packet.to_bytes()
        
        # Mock serial read to return the packet
        mock_instance.read.side_effect = [
            crypt_bytes[0:1],  # STX
            crypt_bytes[1:5],  # Header
            crypt_bytes[5:]    # Rest
        ]
        
        client = GenvexClient(port="/dev/ttyUSB0")
        client.connect()
        
        response = client.send_command(b'\x01\x02', wait_for_response=True)
        
        assert response is not None
        assert response.packet_type == PacketType.U_CRYPT
        assert response.data == b'\xAA\xBB\xCC'
    
    @patch('genvexassistant.client.serial.Serial')
    @patch('genvexassistant.client.time.sleep')
    def test_receive_response_with_notify(self, mock_sleep, mock_serial):
        """Test receiving U_CRYPT response after U_NOTIFY packets."""
        mock_instance = MagicMock()
        mock_instance.is_open = True
        mock_serial.return_value = mock_instance
        
        # Create U_NOTIFY and U_CRYPT packets
        notify1 = U_NOTIFY(0, b'')
        notify2 = U_NOTIFY(0, b'')
        crypt = U_CRYPT(0, b'\xDD\xEE\xFF')
        
        notify1_bytes = notify1.to_bytes()
        notify2_bytes = notify2.to_bytes()
        crypt_bytes = crypt.to_bytes()
        
        # Mock serial read to return NOTIFY, NOTIFY, then CRYPT
        read_sequence = []
        
        # First NOTIFY
        read_sequence.extend([
            notify1_bytes[0:1],
            notify1_bytes[1:5],
            notify1_bytes[5:]
        ])
        # Second NOTIFY
        read_sequence.extend([
            notify2_bytes[0:1],
            notify2_bytes[1:5],
            notify2_bytes[5:]
        ])
        # Finally CRYPT
        read_sequence.extend([
            crypt_bytes[0:1],
            crypt_bytes[1:5],
            crypt_bytes[5:]
        ])
        
        mock_instance.read.side_effect = read_sequence
        
        client = GenvexClient(port="/dev/ttyUSB0", retry_delay=0.05)
        client.connect()
        
        response = client.send_command(b'\x01', wait_for_response=True)
        
        assert response is not None
        assert response.packet_type == PacketType.U_CRYPT
        assert response.data == b'\xDD\xEE\xFF'
        
        # Verify sleep was called for each NOTIFY (2 times)
        assert mock_sleep.call_count == 2
    
    @patch('genvexassistant.client.serial.Serial')
    @patch('genvexassistant.client.time.sleep')
    def test_receive_response_max_retries_exceeded(self, mock_sleep, mock_serial):
        """Test timeout when max retries exceeded."""
        mock_instance = MagicMock()
        mock_instance.is_open = True
        mock_serial.return_value = mock_instance
        
        # Return only U_NOTIFY packets
        notify = U_NOTIFY(0, b'')
        notify_bytes = notify.to_bytes()
        
        # Mock to always return NOTIFY
        def read_side_effect(size):
            if size == 1:
                return notify_bytes[0:1]
            elif size == 4:
                return notify_bytes[1:5]
            else:
                return notify_bytes[5:]
        
        mock_instance.read.side_effect = read_side_effect
        
        client = GenvexClient(port="/dev/ttyUSB0", max_retries=5, retry_delay=0.01)
        client.connect()
        
        with pytest.raises(TimeoutError) as exc_info:
            client.send_command(b'\x01', wait_for_response=True)
        
        assert "5 attempts" in str(exc_info.value)
        assert "U_NOTIFY packets" in str(exc_info.value)
    
    @patch('genvexassistant.client.serial.Serial')
    @patch('genvexassistant.client.time.sleep')
    def test_receive_response_sequence_mismatch(self, mock_sleep, mock_serial):
        """Test handling sequence number mismatch."""
        mock_instance = MagicMock()
        mock_instance.is_open = True
        mock_serial.return_value = mock_instance
        
        # Create packets with wrong sequence, then correct sequence
        wrong_crypt = U_CRYPT(99, b'\x11')
        correct_crypt = U_CRYPT(0, b'\x22')
        
        wrong_bytes = wrong_crypt.to_bytes()
        correct_bytes = correct_crypt.to_bytes()
        
        read_sequence = [
            # Wrong sequence packet
            wrong_bytes[0:1],
            wrong_bytes[1:5],
            wrong_bytes[5:],
            # Correct sequence packet
            correct_bytes[0:1],
            correct_bytes[1:5],
            correct_bytes[5:]
        ]
        
        mock_instance.read.side_effect = read_sequence
        
        client = GenvexClient(port="/dev/ttyUSB0", retry_delay=0.01)
        client.connect()
        
        response = client.send_command(b'\x01', wait_for_response=True)
        
        assert response is not None
        assert response.sequence == 0
        assert response.data == b'\x22'
