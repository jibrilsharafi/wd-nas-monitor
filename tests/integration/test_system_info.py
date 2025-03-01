"""Integration tests for system information retrieval."""

import pytest

from wdnas.devices.ex2 import EX2UltraDevice
from wdnas.models.system import SystemInfo


class TestSystemInfo:
    """Test system information retrieval."""

    def test_get_system_info(self, ex2_device: EX2UltraDevice) -> None:
        """Test retrieving system information."""
        system_info = ex2_device.get_system_info()

        # Verify we got a valid SystemInfo object
        assert isinstance(system_info, SystemInfo)
        assert system_info.model != "Unknown"
        assert system_info.description != "Unknown"
        assert system_info.firmware_version != "Unknown"

        # Check that computed properties work
        assert 0 <= system_info.memory_usage_percent <= 100
        assert system_info.uptime_seconds > 0

    def test_get_firmware_version(self, ex2_device: EX2UltraDevice) -> None:
        """Test retrieving firmware version."""
        firmware = ex2_device.get_firmware_version()

        # Should return a non-empty string
        assert isinstance(firmware, str)
        assert firmware != "Unknown"
        assert firmware != ""

        # Should be in format like 2.31.204
        assert len(firmware.split(".")) >= 2
