"""Integration tests for disk information retrieval."""

import pytest
from wdnas.devices.ex2 import EX2UltraDevice
from wdnas.models.disk import DiskInfo, SmartInfo


class TestDiskInfo:
    """Test disk information retrieval."""

    def test_get_disks(self, ex2_device: EX2UltraDevice) -> None:
        """Test retrieving disk information."""
        # Make sure we have all data loaded
        ex2_device.get_all_data()
        
        disks = ex2_device.get_disks()
        
        # Should return a list with at least one disk
        assert isinstance(disks, list)
        
        # Skip test if no disks found in integration environment
        assert disks
            
        # Verify disk properties
        for disk in disks:
            assert isinstance(disk, DiskInfo)
            # name is the identifier in our implementation
            assert disk.name is not None and disk.name != ""
            assert disk.size_bytes > 0
            assert disk.size_gb > 0
            
            # Temperature should be reasonable if present (0-100°C)
            if disk.temperature:
                assert 0 <= disk.temperature <= 100
                
            # Verify fields have valid types
            assert isinstance(disk.scsi_path, str)
            assert isinstance(disk.connected, bool)
            assert isinstance(disk.revision, str)
            assert isinstance(disk.device_path, str)
            assert isinstance(disk.partition_count, int)
            assert isinstance(disk.allowed, bool)
            assert isinstance(disk.raid_uuid, str)
            assert isinstance(disk.failed, bool)
            assert isinstance(disk.removable, bool)
            assert isinstance(disk.roaming, str)
            assert isinstance(disk.over_temp, bool)
            assert isinstance(disk.sleep, bool)
            
            # If smart_info is present, verify its structure
            if disk.smart_info:
                assert disk.smart_info.test_type
                assert disk.smart_info.result
                assert 0 <= disk.smart_info.percent <= 1.0  # percent is stored as float 0.0-1.0

    def test_get_disk_smart_details(self, ex2_device: EX2UltraDevice) -> None:
        """Test retrieving SMART information for a disk."""
        # First get all data
        ex2_device.get_all_data()
        
        # Then get available disks
        disks = ex2_device.get_disks()
        
        assert disks
            
        smart_info = disks[0].smart_info
        
        # Should return a dict with SMART details
        assert isinstance(smart_info, SmartInfo)
        
        # Skip detailed checks if no SMART data available
        assert smart_info
        
        # Check for expected SMART fields
        assert smart_info.percent is not None
        assert smart_info.result is not None
        assert smart_info.test_type is not None
        assert smart_info.date is not None
        assert isinstance(smart_info.attributes, list)
        
        # Check an attribute if available
        if smart_info.attributes:
            attr = smart_info.attributes[0]
            assert attr.id is not None
            assert attr.name is not None
            assert attr.value is not None
            assert attr.worst is not None
            assert attr.threshold is not None
