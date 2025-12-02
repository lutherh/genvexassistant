"""Genvex Assistant - Control Genvex Ventilation systems."""

from .client import GenvexClient
from .protocol import PacketType, U_NOTIFY, U_CRYPT
from .exceptions import GenvexException, CommunicationError, TimeoutError

__version__ = "0.1.0"
__all__ = [
    "GenvexClient",
    "PacketType",
    "U_NOTIFY",
    "U_CRYPT",
    "GenvexException",
    "CommunicationError",
    "TimeoutError",
]
