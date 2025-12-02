"""Tests for protocol module."""

import pytest
from genvexassistant.protocol import Packet, PacketType, U_NOTIFY, U_CRYPT, U_REQUEST


class TestPacketType:
    """Test PacketType enum."""
    
    def test_packet_types(self):
        """Test packet type values."""
        assert PacketType.U_NOTIFY == 0x34
        assert PacketType.U_CRYPT == 0x35
        assert PacketType.U_REQUEST == 0x30


class TestPacket:
    """Test Packet class."""
    
    def test_packet_to_bytes(self):
        """Test packet serialization."""
        packet = Packet(PacketType.U_REQUEST, 1, b'\x01\x02\x03')
        packet_bytes = packet.to_bytes()
        
        # Check STX
        assert packet_bytes[0] == 0x02
        # Check packet type
        assert packet_bytes[1] == PacketType.U_REQUEST
        # Check sequence
        assert packet_bytes[2] == 1
        # Check ETX
        assert packet_bytes[-1] == 0x03
    
    def test_packet_from_bytes(self):
        """Test packet deserialization."""
        # Create a valid packet
        original = Packet(PacketType.U_CRYPT, 5, b'\xAA\xBB\xCC')
        packet_bytes = original.to_bytes()
        
        # Parse it back
        parsed = Packet.from_bytes(packet_bytes)
        
        assert parsed is not None
        assert parsed.packet_type == PacketType.U_CRYPT
        assert parsed.sequence == 5
        assert parsed.data == b'\xAA\xBB\xCC'
    
    def test_packet_from_bytes_invalid_stx(self):
        """Test parsing packet with invalid STX."""
        invalid_packet = b'\xFF\x30\x01\x00\x00\x00\x03'
        parsed = Packet.from_bytes(invalid_packet)
        assert parsed is None
    
    def test_packet_from_bytes_invalid_etx(self):
        """Test parsing packet with invalid ETX."""
        invalid_packet = b'\x02\x30\x01\x00\x00\x00\xFF'
        parsed = Packet.from_bytes(invalid_packet)
        assert parsed is None
    
    def test_packet_from_bytes_too_short(self):
        """Test parsing packet that's too short."""
        invalid_packet = b'\x02\x30'
        parsed = Packet.from_bytes(invalid_packet)
        assert parsed is None
    
    def test_packet_roundtrip(self):
        """Test packet serialization and deserialization roundtrip."""
        original = Packet(PacketType.U_NOTIFY, 42, b'\x11\x22\x33\x44\x55')
        packet_bytes = original.to_bytes()
        parsed = Packet.from_bytes(packet_bytes)
        
        assert parsed is not None
        assert parsed.packet_type == original.packet_type
        assert parsed.sequence == original.sequence
        assert parsed.data == original.data


class TestU_NOTIFY:
    """Test U_NOTIFY class."""
    
    def test_u_notify_creation(self):
        """Test U_NOTIFY packet creation."""
        notify = U_NOTIFY(10, b'\x01\x02')
        assert notify.packet_type == PacketType.U_NOTIFY
        assert notify.sequence == 10
        assert notify.data == b'\x01\x02'
    
    def test_u_notify_empty_data(self):
        """Test U_NOTIFY packet with empty data."""
        notify = U_NOTIFY(5)
        assert notify.packet_type == PacketType.U_NOTIFY
        assert notify.sequence == 5
        assert notify.data == b''


class TestU_CRYPT:
    """Test U_CRYPT class."""
    
    def test_u_crypt_creation(self):
        """Test U_CRYPT packet creation."""
        crypt = U_CRYPT(20, b'\xAA\xBB\xCC\xDD')
        assert crypt.packet_type == PacketType.U_CRYPT
        assert crypt.sequence == 20
        assert crypt.data == b'\xAA\xBB\xCC\xDD'


class TestU_REQUEST:
    """Test U_REQUEST class."""
    
    def test_u_request_creation(self):
        """Test U_REQUEST packet creation."""
        request = U_REQUEST(30, b'\xFF\xEE\xDD')
        assert request.packet_type == PacketType.U_REQUEST
        assert request.sequence == 30
        assert request.data == b'\xFF\xEE\xDD'
