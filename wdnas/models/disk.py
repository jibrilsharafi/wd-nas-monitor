"""Disk model for WD NAS devices."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class SmartAttribute:
    """Represents a single SMART attribute."""

    id: int
    name: str
    value: int
    worst: int
    threshold: int


@dataclass
class SmartInfo:
    """SMART information for a disk."""

    result: str
    test_type: str
    date: datetime
    percent: float
    attributes: List[SmartAttribute]


@dataclass
class DiskInfo:
    """Information about a disk in the NAS."""

    name: str
    scsi_path: str
    connected: bool
    vendor: str
    model: str
    revision: str
    serial: str
    device_path: str
    size_bytes: int
    partition_count: int
    allowed: bool
    raid_uuid: str
    failed: bool
    healthy: bool
    removable: bool
    roaming: str
    smart_info: Optional[SmartInfo]
    temperature: int
    over_temp: bool
    sleep: bool

    @property
    def size_gb(self) -> float:
        """Get the size in GB."""
        return self.size_bytes / (1024**3)
