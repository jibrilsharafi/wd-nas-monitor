"""Custom exceptions for WD NAS Monitor."""


class WDNasException(Exception):
    """Base exception for all WD NAS related errors."""
    pass


class AuthenticationError(WDNasException):
    """Raised when authentication with the NAS fails."""
    pass


class ConnectionError(WDNasException):
    """Raised when there's an error connecting to the NAS."""
    pass


class ParseError(WDNasException):
    """Raised when there's an error parsing data from the NAS."""
    pass


class DeviceError(WDNasException):
    """Raised for device-specific errors."""
    pass
