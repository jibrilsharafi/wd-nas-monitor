"""System model for WD NAS devices."""

from dataclasses import dataclass
from typing import List


@dataclass
class LogEntry:
    """Log entry for the NAS system."""

    timestamp: str
    level: str
    service: str
    message: str


@dataclass
class VolumeInfo:
    """Information about a volume in the NAS."""

    id: int
    name: str
    label: str
    mount_point: str
    encrypted: bool
    device_path: str
    unlocked: bool
    mounted: bool
    size: int
    uuid: str
    roaming: bool
    used_size: int
    raid_level: str
    raid_state: str
    raid_state_detail: str
    state: str


@dataclass
class RaidInfo:
    """RAID information for the NAS system."""

    id: int
    level: str
    chunk_size: int
    num_of_total_disks: int
    num_of_raid_disks: int
    num_of_active_disks: int
    num_of_working_disks: int
    num_of_spare_disks: int
    num_of_failed_disks: int
    raid_disks: str
    spare_disks: str
    failed_disks: str
    rebuilding_disks: str
    size: int
    used_size: int
    min_req_size: int
    state: str
    state_detail: str
    uuid: str
    dev: str
    ar: int
    expand_size: int
    expand_no_replace: int
    migrate_from: str
    migrate_to: str
    recover_failed: int
    reshape_failed: int
    dirty: int


@dataclass
class SystemInfo:
    """Information about the NAS system."""

    serial_number: str
    name: str
    workgroup: str
    description: str
    firmware_version: str
    oled: str
    fan_speed: int
    lan_r_speed: int
    lan_t_speed: int
    lan2_r_speed: int
    lan2_t_speed: int
    memory_total: int
    memory_free: int
    memory_buffers: int
    memory_cached: int
    cpu_usage: float
    raids: List[RaidInfo]
    volumes: List[VolumeInfo]
    logs: List[LogEntry]

    @property
    def memory_usage_percent(self) -> float:
        """Calculate memory usage percentage."""
        return (
            100.0 * (self.memory_total - self.memory_free) / self.memory_total
            if self.memory_total > 0
            else 0.0
        )
