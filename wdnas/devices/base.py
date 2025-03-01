"""Base device class for WD NAS devices."""

from typing import List

from ..client import WDNasClient
from ..models.disk import DiskInfo
from ..models.system import SystemInfo


class WDNasDevice:
    """Base class for all WD NAS devices."""

    def __init__(self, client: WDNasClient):
        """Initialize the device with a client.

        Args:
            client: The WD NAS client to use for API communication
        """
        self.client = client

    def get_system_info(self) -> SystemInfo:
        """Get system information.

        Returns:
            SystemInfo: System information for the device

        Raises:
            NotImplementedError: If the subclass doesn't implement this method
        """
        raise NotImplementedError("Subclasses must implement this")

    def get_disks(self) -> List[DiskInfo]:
        """Get information about all disks.

        Returns:
            List[DiskInfo]: List of disk information objects
        """
        raise NotImplementedError("Subclasses must implement this")
