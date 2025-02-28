"""Unit tests for data models."""

import xml.etree.ElementTree as ET

import pytest

from wdnas.models.disk import DiskInfo
from wdnas.models.system import SystemInfo


class TestDiskInfo:
    """Tests for DiskInfo model."""

    def test_from_xml_with_complete_data(self) -> None:
        """Test parsing disk info from complete XML."""
        xml_str = """
        <disk id="sda">
            <name>Disk 1</name>
            <vendor>WDC</vendor>
            <model>WD10EFRX-68FYTN0</model>
            <sn>WD-XYZ123456789</sn>
            <size>1000000000000</size>
            <temp>40</temp>
            <healthy>1</healthy>
            <smart>
                <result>PASS</result>
            </smart>
        </disk>
        """
        xml_element = ET.fromstring(xml_str)
        disk_info = DiskInfo.from_xml(xml_element)

        assert disk_info.id == "sda"
        assert disk_info.name == "Disk 1"
        assert disk_info.vendor == "WDC"
        assert disk_info.model == "WD10EFRX-68FYTN0"
        assert disk_info.serial == "WD-XYZ123456789"
        assert disk_info.size_bytes == 1000000000000
        assert disk_info.temperature == 40
        assert disk_info.healthy is True
        assert disk_info.smart_status == "PASS"

    def test_from_xml_with_missing_data(self) -> None:
        """Test parsing disk info from incomplete XML."""
        xml_str = """
        <disk id="sda">
            <name>Disk 1</name>
            <model>WD10EFRX-68FYTN0</model>
            <size>1000000000000</size>
        </disk>
        """
        xml_element = ET.fromstring(xml_str)
        disk_info = DiskInfo.from_xml(xml_element)

        assert disk_info.id == "sda"
        assert disk_info.name == "Disk 1"
        assert disk_info.vendor == "Unknown"
        assert disk_info.model == "WD10EFRX-68FYTN0"
        assert disk_info.serial == "Unknown"
        assert disk_info.size_bytes == 1000000000000
        assert disk_info.temperature == 0
        assert disk_info.healthy is False
        assert disk_info.smart_status == "Unknown"

    def test_size_gb_property(self) -> None:
        """Test size_gb property calculation."""
        disk_info = DiskInfo(
            id="sda",
            name="Disk 1",
            vendor="WDC",
            model="Test",
            serial="123",
            size_bytes=1073741824,  # 1 GB
            temperature=40,
            healthy=True,
            smart_status="PASS",
        )

        assert disk_info.size_gb == 1.0


class TestSystemInfo:
    """Tests for SystemInfo model."""

    def test_from_xml_with_complete_data(self) -> None:
        """Test parsing system info from complete XML."""
        xml_str = """
        <system>
            <model>WD My Cloud EX2 Ultra</model>
            <name>MyNAS</name>
            <firmware>
                <version>2.31.204</version>
            </firmware>
            <serial_number>WD1234567890</serial_number>
            <cpu_usage>25</cpu_usage>
            <memory>
                <total>512000000</total>
                <used>256000000</used>
            </memory>
            <uptime>1 days, 12:34:56</uptime>
            <temperature>42</temperature>
        </system>
        """
        xml_element = ET.fromstring(xml_str)
        system_info = SystemInfo.from_xml(xml_element)

        assert system_info.model == "WD My Cloud EX2 Ultra"
        assert system_info.name == "MyNAS"
        assert system_info.firmware_version == "2.31.204"
        assert system_info.serial_number == "WD1234567890"
        assert system_info.cpu_usage == 25.0
        assert system_info.memory_total == 512000000
        assert system_info.memory_used == 256000000
        assert system_info.temperature == 42
        # Uptime should be 1 day (86400s) + 12 hours (43200s) + 34 minutes (2040s) + 56 seconds = 131696 seconds
        assert system_info.uptime_seconds == 131696

    def test_from_xml_with_missing_data(self) -> None:
        """Test parsing system info from incomplete XML."""
        xml_str = """
        <system>
            <model>WD My Cloud EX2 Ultra</model>
            <name>MyNAS</name>
        </system>
        """
        xml_element = ET.fromstring(xml_str)
        system_info = SystemInfo.from_xml(xml_element)

        assert system_info.model == "WD My Cloud EX2 Ultra"
        assert system_info.name == "MyNAS"
        assert system_info.firmware_version == "Unknown"
        assert system_info.serial_number == "Unknown"
        assert system_info.cpu_usage == 0.0
        assert system_info.memory_total == 0
        assert system_info.memory_used == 0
        assert system_info.uptime_seconds == 0
        assert system_info.temperature is None

    def test_memory_usage_percent_property(self) -> None:
        """Test memory_usage_percent property calculation."""
        system_info = SystemInfo(
            model="Test",
            name="Test",
            firmware_version="1.0",
            serial_number="123",
            cpu_usage=50.0,
            memory_total=1000,
            memory_used=250,
            uptime_seconds=3600,
            temperature=40,
        )

        assert system_info.memory_usage_percent == 25.0

        # Test with zero total memory (should not raise division by zero)
        system_info.memory_total = 0
        assert system_info.memory_usage_percent == 0.0
