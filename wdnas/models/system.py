"""System model for WD NAS devices."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional


@dataclass
class SystemInfo:
    """Information about the NAS system."""

    model: str
    name: str
    firmware_version: str
    serial_number: str
    cpu_usage: float
    memory_total: int
    memory_used: int
    uptime_seconds: int
    temperature: Optional[int] = None

    @property
    def memory_usage_percent(self) -> float:
        """Calculate memory usage percentage."""
        if self.memory_total == 0:
            return 0.0
        return (self.memory_used / self.memory_total) * 100

    @classmethod
    def from_xml(cls, xml_element: ET.Element) -> "SystemInfo":
        """Parse system info from XML element.

        Args:
            xml_element: XML element containing system information

        Returns:
            SystemInfo: Parsed system information object
        """

        # Handle potentially missing elements safely
        def get_text(xpath: str, default: str = "") -> str:
            element = xml_element.find(xpath)
            return element.text if element is not None and element.text is not None else default

        # Get uptime in seconds from the XML
        uptime_text = get_text("uptime", "0")
        try:
            # Parse uptime which might be in format "XX days, HH:MM:SS" or just seconds
            if "days" in uptime_text:
                days_part, time_part = uptime_text.split(",")
                days = int(days_part.strip().split()[0])
                hours, minutes, seconds = map(int, time_part.strip().split(":"))
                uptime_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds
            else:
                uptime_seconds = int(uptime_text)
        except (ValueError, IndexError):
            uptime_seconds = 0

        # Try to get temperature, may not be available on all models
        temp_str = get_text("temperature")
        temperature = int(temp_str) if temp_str and temp_str.isdigit() else None

        return cls(
            model=get_text("model", "Unknown"),
            name=get_text("name", "Unknown"),
            firmware_version=get_text("firmware/version", "Unknown"),
            serial_number=get_text("serial_number", "Unknown"),
            cpu_usage=float(get_text("cpu_usage", "0")),
            memory_total=int(get_text("memory/total", "0")),
            memory_used=int(get_text("memory/used", "0")),
            uptime_seconds=uptime_seconds,
            temperature=temperature,
        )
