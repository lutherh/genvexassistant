"""Genvex client for communicating with Genvex ventilation systems."""

import serial
import time
import logging
from typing import Optional, List
from .protocol import Packet, PacketType, U_REQUEST, U_CRYPT, U_NOTIFY
from .sequence import SequenceManager
from .exceptions import CommunicationError, TimeoutError, ProtocolError

logger = logging.getLogger(__name__)


class GenvexClient:
    """Client for communicating with Genvex ventilation systems.
    
    This client handles the specifics of the Genvex Optima 270 protocol,
    including:
    - U_NOTIFY packets (Type 0x34) that precede actual responses
    - Automatic retry/loop mechanism to consume notifications
    - Sequence number management
    """
    
    def __init__(
        self,
        port: str,
        baudrate: int = 9600,
        timeout: float = 2.0,
        max_retries: int = 10,
        retry_delay: float = 0.1
    ):
        """Initialize Genvex client.
        
        Args:
            port: Serial port path (e.g., "/dev/ttyUSB0")
            baudrate: Baud rate for serial communication (default: 9600)
            timeout: Timeout for serial operations in seconds (default: 2.0)
            max_retries: Maximum number of retries for handling U_NOTIFY packets (default: 10)
            retry_delay: Delay between retries in seconds (default: 0.1)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self._serial: Optional[serial.Serial] = None
        self._sequence_manager = SequenceManager()
        self._connected = False
    
    def connect(self):
        """Connect to the Genvex device.
        
        Raises:
            CommunicationError: If connection fails
        """
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            self._connected = True
            logger.info(f"Connected to Genvex device on {self.port}")
        except serial.SerialException as e:
            raise CommunicationError(f"Failed to connect to {self.port}: {e}")
    
    def disconnect(self):
        """Disconnect from the Genvex device."""
        if self._serial and self._serial.is_open:
            self._serial.close()
            self._connected = False
            logger.info("Disconnected from Genvex device")
    
    def is_connected(self) -> bool:
        """Check if connected to device.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self._connected and self._serial and self._serial.is_open
    
    def send_command(self, data: bytes, wait_for_response: bool = True) -> Optional[U_CRYPT]:
        """Send command to Genvex device and optionally wait for response.
        
        This method handles the device's behavior of sending U_NOTIFY packets
        before the actual U_CRYPT response. It implements a retry/loop mechanism
        to consume these notifications and wait for the actual data.
        
        Args:
            data: Command data to send
            wait_for_response: Whether to wait for response (default: True)
        
        Returns:
            U_CRYPT packet if wait_for_response is True, None otherwise
        
        Raises:
            CommunicationError: If communication fails
            TimeoutError: If response timeout occurs
            ProtocolError: If protocol error occurs
        """
        if not self.is_connected():
            raise CommunicationError("Not connected to device")
        
        # Get next sequence number
        sequence = self._sequence_manager.next()
        
        # Create and send request packet
        request = U_REQUEST(sequence, data)
        self._send_packet(request)
        
        if not wait_for_response:
            return None
        
        # Wait for response with retry mechanism for U_NOTIFY packets
        return self._receive_response_with_retry(sequence)
    
    def _send_packet(self, packet: Packet):
        """Send packet to device.
        
        Args:
            packet: Packet to send
        
        Raises:
            CommunicationError: If send fails
        """
        try:
            packet_bytes = packet.to_bytes()
            self._serial.write(packet_bytes)
            self._serial.flush()
            logger.debug(f"Sent packet: type={packet.packet_type}, seq={packet.sequence}, len={len(packet.data)}")
        except serial.SerialException as e:
            raise CommunicationError(f"Failed to send packet: {e}")
    
    def _receive_packet(self) -> Optional[Packet]:
        """Receive packet from device.
        
        Returns:
            Received packet or None if timeout
        
        Raises:
            CommunicationError: If receive fails
            ProtocolError: If packet parsing fails
        """
        try:
            # Read STX byte
            stx = self._serial.read(1)
            if not stx or stx[0] != 0x02:
                return None
            
            # Read header (type, seq, length)
            header = self._serial.read(4)
            if len(header) < 4:
                return None
            
            # Parse length
            length = (header[3] << 8) | header[2]
            
            # Read data, checksum, and ETX
            remaining = self._serial.read(length + 2)
            if len(remaining) < length + 2:
                return None
            
            # Reconstruct full packet
            packet_bytes = stx + header + remaining
            
            # Parse packet
            packet = Packet.from_bytes(packet_bytes)
            if packet:
                logger.debug(f"Received packet: type={packet.packet_type}, seq={packet.sequence}, len={len(packet.data)}")
            else:
                raise ProtocolError("Failed to parse received packet")
            
            return packet
            
        except serial.SerialException as e:
            raise CommunicationError(f"Failed to receive packet: {e}")
    
    def _receive_response_with_retry(self, expected_sequence: int) -> U_CRYPT:
        """Receive response with retry mechanism for U_NOTIFY packets.
        
        The Genvex Optima 270 device often responds with U_NOTIFY packets (Type 0x34)
        before sending the actual U_CRYPT response. This method implements a
        retry/loop mechanism to consume these notifications and wait for the
        actual data response.
        
        Args:
            expected_sequence: Expected sequence number of the response
        
        Returns:
            U_CRYPT packet with actual response data
        
        Raises:
            TimeoutError: If no valid response received after max_retries
            ProtocolError: If protocol error occurs
        """
        notify_packets: List[U_NOTIFY] = []
        
        for attempt in range(self.max_retries):
            packet = self._receive_packet()
            
            if packet is None:
                # No packet received, wait and retry
                time.sleep(self.retry_delay)
                continue
            
            # Check sequence number
            if packet.sequence != expected_sequence:
                logger.warning(f"Sequence mismatch: expected={expected_sequence}, got={packet.sequence}")
                time.sleep(self.retry_delay)
                continue
            
            # Handle packet type
            if packet.packet_type == PacketType.U_NOTIFY:
                # U_NOTIFY packet - consume and continue waiting for actual response
                logger.debug(f"Received U_NOTIFY packet (attempt {attempt + 1}/{self.max_retries})")
                notify_packets.append(U_NOTIFY(packet.sequence, packet.data))
                time.sleep(self.retry_delay)
                continue
            
            elif packet.packet_type == PacketType.U_CRYPT:
                # U_CRYPT packet - this is the actual response
                logger.info(f"Received U_CRYPT response after {len(notify_packets)} U_NOTIFY packets")
                return U_CRYPT(packet.sequence, packet.data)
            
            else:
                # Unexpected packet type
                raise ProtocolError(f"Unexpected packet type: {packet.packet_type}")
        
        # Max retries exceeded
        raise TimeoutError(
            f"Timeout waiting for response: received {len(notify_packets)} U_NOTIFY packets, "
            f"but no U_CRYPT response after {self.max_retries} attempts"
        )
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
