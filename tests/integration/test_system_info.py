"""Integration tests for system information retrieval."""

import pytest

from wdnas.devices.ex2 import EX2UltraDevice
from wdnas.models.system import SystemInfo


class TestSystemInfo:
    """Test system information retrieval."""

    def test_get_system_info(self, ex2_device: EX2UltraDevice) -> None:
        """Test retrieving system information."""
        # First make sure we have all data loaded
        ex2_device.get_all_data()
        
        system_info = ex2_device.get_system_info()

        # Verify we got a valid SystemInfo object
        assert isinstance(system_info, SystemInfo)
        
        # Check basic properties
        assert system_info.serial_number is not None and system_info.serial_number != ""
        assert system_info.name is not None and system_info.name != ""
        assert system_info.firmware_version is not None and system_info.firmware_version != ""
        
        # Check ranges for numeric values
        assert system_info.memory_total > 0
        assert 0 <= system_info.cpu_usage <= 1.0  # CPU usage is 0.0-1.0 in our model
        
        # Check memory calculations
        memory_percent = system_info.memory_usage_percent
        assert 0 <= memory_percent <= 100
        
        # Verify RAID information if present
        if system_info.raids:
            raid = system_info.raids[0]
            assert raid.id is not None
            assert raid.level is not None
            
        # Verify volume information if present
        if system_info.volumes:
            vol = system_info.volumes[0]
            assert vol.id is not None
            assert vol.name is not None
            assert vol.mount_point is not None

        # Verify logs if present
        if system_info.logs:
            log = system_info.logs[0]
            assert log.timestamp is not None
            assert log.level is not None
            assert log.message is not None