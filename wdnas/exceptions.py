"""Exceptions for WD NAS Monitor."""


class WDNasError(Exception):
    """Base exception for WD NAS Monitor."""


class ConnectionError(WDNasError):
    """Raised when connection to the NAS fails."""


class AuthenticationError(WDNasError):
    """Raised when authentication fails."""


class ParseError(WDNasError):
    """Raised when parsing a response fails."""
