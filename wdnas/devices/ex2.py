"""Implementation for WD My Cloud EX2 Ultra."""

import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from ..exceptions import ParseError
from ..models.system import SystemInfo
from .base import WDNasDevice


class EX2UltraDevice(WDNasDevice):
    """Implementation for WD My Cloud EX2 Ultra."""

    def get_system_info(self) -> SystemInfo:
        """Get system information for EX2 Ultra.

        Returns:
            SystemInfo: System information for the device
        """
        # Get the system information from the sysinfo.xml endpoint
        xml_root = self.client.get_system_info()

        # EX2Ultra has a different XML format than the generic one
        # So we create a custom method to extract data
        return self._parse_system_info(xml_root)

    def _parse_system_info(self, xml_root: ET.Element) -> SystemInfo:
        """Parse system information from EX2 Ultra's specific XML format.

        Args:
            xml_root: XML root element

        Returns:
            SystemInfo: System information object
        """

        # Handle potentially missing elements safely
        def get_text(xpath: str, default: str = "") -> str:
            element = xml_root.find(xpath)
            return element.text if element is not None and element.text is not None else default

        # Extract firmware version from the XML
        firmware_version = get_text(".//firmware_version", "Unknown")

        # Parse uptime - the format might be different from what we expected
        uptime_text = get_text(".//uptime", "0")
        uptime_seconds = self._parse_uptime(uptime_text)

        # Extract memory information
        mem_info = xml_root.find(".//memory")
        memory_total = 0
        memory_used = 0

        if mem_info is not None:
            try:
                memory_total = int(get_text(".//memory/total", "0"))
                memory_used = int(get_text(".//memory/used", "0"))
            except (ValueError, TypeError):
                pass

        # Extract CPU usage
        cpu_usage = 0.0
        cpu_text = get_text(".//cpu_usage", "0")
        try:
            # Remove any '%' character and convert to float
            cpu_usage = float(cpu_text.replace("%", ""))
        except (ValueError, TypeError):
            pass

        # Extract temperature
        temp = None
        temp_text = get_text(".//temperature", "")
        if temp_text:
            try:
                temp = int(temp_text)
            except (ValueError, TypeError):
                pass

        return SystemInfo(
            model="WD My Cloud EX2 Ultra",
            name=get_text(".//name", "EX2Ultra"),
            firmware_version=firmware_version,
            serial_number=get_text(".//serial", "Unknown"),
            cpu_usage=cpu_usage,
            memory_total=memory_total,
            memory_used=memory_used,
            uptime_seconds=uptime_seconds,
            temperature=temp,
        )

    def _parse_uptime(self, uptime_text: str) -> int:
        """Parse uptime string into seconds.

        Args:
            uptime_text: Uptime text from the API

        Returns:
            int: Uptime in seconds
        """
        try:
            # Try direct conversion first
            return int(uptime_text)
        except (ValueError, TypeError):
            pass

        # Try parsing "X days, HH:MM:SS" format
        try:
            if "days" in uptime_text:
                days_part, time_part = uptime_text.split(",", 1)
                days_match = re.search(r"(\d+)", days_part)
                if days_match is None:
                    return 0
                days = int(days_match.group(1))

                # Handle HH:MM:SS format
                time_parts = time_part.strip().split(":")
                if len(time_parts) == 3:
                    hours, minutes, seconds = map(int, time_parts)
                    return days * 86400 + hours * 3600 + minutes * 60 + seconds

            # Handle raw "HH:MM:SS" format without days
            time_parts = uptime_text.strip().split(":")
            if len(time_parts) == 3:
                hours, minutes, seconds = map(int, time_parts)
                return hours * 3600 + minutes * 60 + seconds
        except (ValueError, AttributeError, IndexError):
            pass

        # Default to 0 if we can't parse it
        return 0

    def get_firmware_version(self) -> str:
        """Get the firmware version.

        Returns:
            str: The firmware version
        """
        # Use the specific firmware API endpoint
        xml_root = self.client.get_firmware_version()
        version = xml_root.find(".//version")
        return version.text if version is not None and version.text is not None else "Unknown"

    def get_storage_usage(self) -> Dict[str, float]:
        """Get storage usage information.

        Returns:
            Dict[str, float]: Dictionary with total, used and free space in GB
        """
        # Extract storage usage from home information
        xml_root = self.client.get_home_info()

        try:
            # Find the volume information
            volume = xml_root.find(".//volume")
            if volume is None:
                raise ParseError("Volume information not found")

            # Extract capacity information
            capacity = volume.find(".//capacity")
            used = volume.find(".//used")

            if capacity is None or capacity.text is None or used is None or used.text is None:
                raise ParseError("Capacity or used information not found")

            total_bytes = int(capacity.text)
            used_bytes = int(used.text)
            free_bytes = total_bytes - used_bytes

            # Convert to GB
            bytes_to_gb = lambda b: b / (1024**3)

            return {
                "total_gb": bytes_to_gb(total_bytes),
                "used_gb": bytes_to_gb(used_bytes),
                "free_gb": bytes_to_gb(free_bytes),
                "usage_percent": (used_bytes / total_bytes * 100) if total_bytes > 0 else 0,
            }
        except (AttributeError, TypeError, ValueError) as e:
            raise ParseError(f"Failed to parse storage usage: {str(e)}")

    def get_disk_smart_details(self, disk_id: str) -> Dict[str, Any]:
        """Get detailed SMART information for a disk.

        Args:
            disk_id: The disk ID (e.g., 'sda', 'sdb')

        Returns:
            Dict: Detailed SMART information
        """
        return self.client.get_disk_smart_info(disk_id)
