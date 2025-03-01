"""Integration tests for disk information retrieval."""

import pytest
from wdnas.devices.ex2 import EX2UltraDevice
from wdnas.models.disk import DiskInfo


class TestDiskInfo:
    """Test disk information retrieval."""

    def test_get_disks(self, ex2_device: EX2UltraDevice) -> None:
        """Test retrieving disk information."""
        disks = ex2_device.get_disks()
        
        # Should return a list with at least one disk
        assert isinstance(disks, list)
        
        # Skip test if no disks found in integration environment
        if not disks:
            pytest.skip("No disks found in test environment")
            
        # Verify disk properties
        for disk in disks:
            assert isinstance(disk, DiskInfo)
            # id might start with a number (like "1") in dictionary-based APIs
            assert disk.id is not None and disk.id != ""
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
                assert 0 <= disk.smart_info.percent <= 100

    def test_get_disk_smart_details(self, ex2_device: EX2UltraDevice) -> None:
        """Test retrieving SMART information for a disk."""
        # First get available disks
        disks = ex2_device.get_disks()
        
        if not disks:
            pytest.skip("No disks available to test SMART info")
            
        # Get SMART info for the first disk
        first_disk_id = disks[0].id
        smart_info = ex2_device.get_disk_smart_details(first_disk_id)
        
        # Should return a dict with SMART attributes
        assert isinstance(smart_info, dict)
        
        # Skip detailed checks if no SMART data available
        if not smart_info or "rows" not in smart_info or not smart_info["rows"]:
            pytest.skip("No SMART data available for testing")
        
        # Verify format of a row if present
        first_row = smart_info["rows"][0]
        assert "_id" in first_row or "cell" in first_row  # Allow either format
