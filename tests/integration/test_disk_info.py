"""Integration tests for disk information retrieval."""

import pytest
from wdnas.devices.ex2 import EX2UltraDevice
from wdnas.models.disk import DiskInfo


class TestDiskInfo:
    """Test disk information retrieval."""

    # FIXME: this test is failing
    def test_get_disks(self, ex2_device: EX2UltraDevice) -> None:
        """Test retrieving disk information."""
        disks = ex2_device.get_disks()
        
        # Should return a list with at least one disk
        assert isinstance(disks, list)
        assert len(disks) > 0
        
        # Verify disk properties
        for disk in disks:
            assert isinstance(disk, DiskInfo)
            assert disk.id.startswith("sd")
            assert disk.size_bytes > 0
            assert disk.size_gb > 0
            
            # Temperature should be reasonable if present (0-100°C)
            if disk.temperature:
                assert 0 <= disk.temperature <= 100
                
            # Verify new fields have valid types
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
                # last_test_date might be None, but if present it should be a datetime

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
        assert "rows" in smart_info
        assert isinstance(smart_info["rows"], list)
        
        # Should contain some SMART attributes
        if smart_info["rows"]:
            # Verify format of a row
            first_row = smart_info["rows"][0]
            assert "id" in first_row
            assert "cell" in first_row
            assert isinstance(first_row["cell"], list)
