"""Custom exceptions for Genvex Assistant."""


class GenvexException(Exception):
    """Base exception for Genvex Assistant."""
    pass


class CommunicationError(GenvexException):
    """Exception raised when communication with device fails."""
    pass


class TimeoutError(GenvexException):
    """Exception raised when operation times out."""
    pass


class ProtocolError(GenvexException):
    """Exception raised when protocol error occurs."""
    pass
