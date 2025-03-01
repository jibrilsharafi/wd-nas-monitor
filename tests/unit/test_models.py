"""Unit tests for data models."""

import xml.etree.ElementTree as ET
from datetime import datetime

import pytest

from wdnas.models.disk import DiskInfo, SmartInfo
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
                <test>Short</test>
                <result>Pass [2023/05/15 12:30:45]</result>
                <percent>100</percent>
            </smart>
            <scsi_path>/dev/scsi/host0/bus0/target0/lun0</scsi_path>
            <connected>1</connected>
            <rev>1.0</rev>
            <dev>/dev/sda</dev>
            <part_cnt>2</part_cnt>
            <allowed>1</allowed>
            <raid_uuid>12345678-abcd-ef12-3456-789abcdef123</raid_uuid>
            <failed>0</failed>
            <removable>0</removable>
            <roaming>no</roaming>
            <over_temp>0</over_temp>
            <sleep>0</sleep>
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
        assert disk_info.smart_status == "Pass"
        
        # New field assertions
        assert disk_info.scsi_path == "/dev/scsi/host0/bus0/target0/lun0"
        assert disk_info.connected is True
        assert disk_info.revision == "1.0"
        assert disk_info.device_path == "/dev/sda"
        assert disk_info.partition_count == 2
        assert disk_info.allowed is True
        assert disk_info.raid_uuid == "12345678-abcd-ef12-3456-789abcdef123"
        assert disk_info.failed is False
        assert disk_info.removable is False
        assert disk_info.roaming == "no"
        assert disk_info.over_temp is False
        assert disk_info.sleep is False
        
        # Smart info assertions
        assert disk_info.smart_info is not None
        assert disk_info.smart_info.test_type == "Short"
        assert disk_info.smart_info.result == "Pass"
        assert disk_info.smart_info.percent == 100
        assert disk_info.smart_info.last_test_date == datetime(2023, 5, 15, 12, 30, 45)

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
        
        # Default values for new fields
        assert disk_info.scsi_path == ""
        assert disk_info.connected is False
        assert disk_info.revision == ""
        assert disk_info.device_path == ""
        assert disk_info.partition_count == 0
        assert disk_info.allowed is False
        assert disk_info.raid_uuid == ""
        assert disk_info.failed is False
        assert disk_info.removable is False
        assert disk_info.roaming == ""
        assert disk_info.over_temp is False
        assert disk_info.sleep is False
        assert disk_info.smart_info is None

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

    def test_smart_info_parsing(self) -> None:
        """Test parsing SmartInfo with different date formats."""
        xml_str = """
        <smart>
            <test>Long</test>
            <result>Pass [2023/05/15 12:30:45]</result>
            <percent>100</percent>
        </smart>
        """
        xml_element = ET.fromstring(xml_str)
        smart_info = SmartInfo.from_xml(xml_element)
        
        assert smart_info.test_type == "Long"
        assert smart_info.result == "Pass"
        assert smart_info.percent == 100
        assert smart_info.last_test_date == datetime(2023, 5, 15, 12, 30, 45)
        
        # Test with invalid date format
        xml_str = """
        <smart>
            <test>Short</test>
            <result>Pass [Invalid Date]</result>
            <percent>90</percent>
        </smart>
        """
        xml_element = ET.fromstring(xml_str)
        smart_info = SmartInfo.from_xml(xml_element)
        
        assert smart_info.result == "Pass [Invalid Date]"
        assert smart_info.last_test_date is None


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
