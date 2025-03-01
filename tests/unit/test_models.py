"""Unit tests for data models."""

from datetime import datetime

import pytest

from wdnas.models.disk import DiskInfo, SmartAttribute, SmartInfo
from wdnas.models.system import LogEntry, RaidInfo, SystemInfo, VolumeInfo


class TestDiskInfo:
    """Tests for DiskInfo model."""

    def test_size_gb_property(self) -> None:
        """Test size_gb property calculation."""
        # Create a disk with 2 GB size
        disk_info = DiskInfo(
            name="sda",
            scsi_path="/dev/scsi/host0/bus0/target0/lun0",
            connected=True,
            vendor="WDC",
            model="WD10EFRX-68FYTN0",
            revision="1.0",
            serial="WD-XYZ123456789",
            device_path="/dev/sda",
            size_bytes=2147483648,  # 2 GB
            partition_count=2,
            allowed=True,
            raid_uuid="12345678-abcd-ef12-3456-789abcdef123",
            failed=False,
            healthy=True,
            removable=False,
            roaming="no",
            smart_info=None,
            temperature=40,
            over_temp=False,
            sleep=False,
        )

        assert disk_info.size_gb == 2.0

    def test_smart_info(self) -> None:
        """Test SmartInfo and SmartAttribute classes."""
        attributes = [
            SmartAttribute(id=1, name="Raw Read Error Rate", value=100, worst=100, threshold=16),
            SmartAttribute(
                id=5, name="Reallocated Sectors Count", value=100, worst=100, threshold=10
            ),
        ]

        smart_info = SmartInfo(
            result="Pass",
            test_type="Short",
            date=datetime(2023, 5, 15, 12, 30, 45),
            percent=0.95,
            attributes=attributes,
        )

        assert smart_info.result == "Pass"
        assert smart_info.test_type == "Short"
        assert smart_info.date == datetime(2023, 5, 15, 12, 30, 45)
        assert smart_info.percent == 0.95
        assert len(smart_info.attributes) == 2
        assert smart_info.attributes[0].id == 1
        assert smart_info.attributes[0].name == "Raw Read Error Rate"


class TestSystemInfo:
    """Tests for SystemInfo model."""

    def test_memory_usage_percent_property(self) -> None:
        """Test memory_usage_percent property calculation."""
        # Create minimal SystemInfo with memory settings
        system_info = SystemInfo(
            serial_number="WD-1234",
            name="MyNAS",
            workgroup="WORKGROUP",
            description="Test NAS",
            firmware_version="2.31.204",
            oled="1.0",
            fan_speed=4000,
            lan_r_speed=1000,
            lan_t_speed=1000,
            lan2_r_speed=0,
            lan2_t_speed=0,
            memory_total=1000,
            memory_free=250,
            memory_buffers=50,
            memory_cached=200,
            cpu_usage=25.5,
            raids=[],
            volumes=[],
            logs=[],
        )

        # Memory usage should be (total - free) / total = (1000 - 250) / 1000 = 0.75 = 75%
        assert system_info.memory_usage_percent == 75.0

        # Test with zero total memory (should not raise division by zero)
        system_info.memory_total = 0
        assert system_info.memory_usage_percent == 0.0

    def test_raid_volume_log_structures(self) -> None:
        """Test the structures of RaidInfo, VolumeInfo, and LogEntry."""
        # Create a RaidInfo instance
        raid = RaidInfo(
            id=1,
            level="raid1",
            chunk_size=512,
            num_of_total_disks=2,
            num_of_raid_disks=2,
            num_of_active_disks=2,
            num_of_working_disks=2,
            num_of_spare_disks=0,
            num_of_failed_disks=0,
            raid_disks="sda, sdb",
            spare_disks="",
            failed_disks="",
            rebuilding_disks="",
            size=1000000000,
            used_size=500000000,
            min_req_size=1000000000,
            state="clean",
            state_detail="",
            uuid="12345678-abcd-ef12-3456-789abcdef123",
            dev="md0",
            ar=0,
            expand_size=0,
            expand_no_replace=0,
            migrate_from="",
            migrate_to="",
            recover_failed=0,
            reshape_failed=0,
            dirty=0,
        )

        # Create a VolumeInfo instance
        volume = VolumeInfo(
            id=1,
            name="Volume_1",
            label="NAS_Volume",
            mount_point="/mnt/HD/HD_a2",
            encrypted=False,
            device_path="/dev/md0",
            unlocked=True,
            mounted=True,
            size=1000000000,
            uuid="12345678-abcd-ef12-3456-789abcdef123",
            roaming=False,
            used_size=500000000,
            raid_level="raid1",
            raid_state="clean",
            raid_state_detail="",
            state="normal",
        )

        # Create a LogEntry instance
        log = LogEntry(
            timestamp="2023-05-15 12:30:45",
            level="INFO",
            service="system",
            message="System started",
        )

        # Check that all attributes are correctly stored
        assert raid.level == "raid1"
        assert raid.num_of_raid_disks == 2
        assert raid.state == "clean"

        assert volume.name == "Volume_1"
        assert volume.mount_point == "/mnt/HD/HD_a2"
        assert volume.encrypted is False

        assert log.timestamp == "2023-05-15 12:30:45"
        assert log.level == "INFO"
        assert log.message == "System started"
