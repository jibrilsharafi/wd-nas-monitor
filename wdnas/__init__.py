"""WD NAS Monitor - A library for monitoring Western Digital NAS devices."""

from .client import WDNasClient
from .devices.ex2 import EX2UltraDevice

__version__ = "0.1.0"


def get_device(model_type: str, client: WDNasClient) -> EX2UltraDevice:
    """Factory method to get the appropriate device implementation."""
    if model_type.lower() == "ex2ultra":
        return EX2UltraDevice(client)
    else:
        raise ValueError(f"Unsupported model: {model_type}")
