"""Protocol definitions for Genvex communication."""

from enum import IntEnum
from dataclasses import dataclass
from typing import Optional
import struct


class PacketType(IntEnum):
    """Packet types used in Genvex protocol."""
    U_NOTIFY = 0x34  # Notification packet
    U_CRYPT = 0x35   # Encrypted/data packet
    U_REQUEST = 0x30 # Request packet


@dataclass
class Packet:
    """Base class for Genvex packets."""
    packet_type: PacketType
    sequence: int
    data: bytes
    
    def to_bytes(self) -> bytes:
        """Convert packet to bytes for transmission."""
        # Basic packet structure: [STX][TYPE][SEQ][LENGTH][DATA][CHECKSUM][ETX]
        stx = 0x02
        etx = 0x03
        length = len(self.data)
        
        # Build packet
        packet = struct.pack('BBB', stx, self.packet_type, self.sequence)
        packet += struct.pack('H', length)
        packet += self.data
        
        # Calculate checksum (simple XOR of all bytes except STX)
        checksum = 0
        for byte in packet[1:]:
            checksum ^= byte
        
        packet += struct.pack('BB', checksum, etx)
        return packet
    
    @classmethod
    def from_bytes(cls, data: bytes) -> Optional['Packet']:
        """Parse packet from bytes."""
        if len(data) < 7:  # Minimum packet size
            return None
        
        if data[0] != 0x02 or data[-1] != 0x03:  # STX/ETX check
            return None
        
        packet_type = PacketType(data[1])
        sequence = data[2]
        length = struct.unpack('H', data[3:5])[0]
        
        if len(data) < 7 + length:
            return None
        
        packet_data = data[5:5+length]
        checksum = data[5+length]
        
        # Verify checksum
        calc_checksum = 0
        for byte in data[1:5+length]:
            calc_checksum ^= byte
        
        if calc_checksum != checksum:
            return None
        
        return cls(packet_type=packet_type, sequence=sequence, data=packet_data)


class U_NOTIFY(Packet):
    """Notification packet (Type 0x34)."""
    def __init__(self, sequence: int, data: bytes = b''):
        super().__init__(PacketType.U_NOTIFY, sequence, data)


class U_CRYPT(Packet):
    """Data/response packet (Type 0x35)."""
    def __init__(self, sequence: int, data: bytes):
        super().__init__(PacketType.U_CRYPT, sequence, data)


class U_REQUEST(Packet):
    """Request packet (Type 0x30)."""
    def __init__(self, sequence: int, data: bytes):
        super().__init__(PacketType.U_REQUEST, sequence, data)
