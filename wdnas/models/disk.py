"""Disk model for WD NAS devices."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional


@dataclass
class DiskInfo:
    """Information about a disk in the NAS."""

    id: str
    name: str
    vendor: str
    model: str
    serial: str
    size_bytes: int
    temperature: int
    healthy: bool
    smart_status: str

    @property
    def size_gb(self) -> float:
        """Get the size in GB."""
        return self.size_bytes / (1024**3)

    @classmethod
    def from_xml(cls, xml_element: ET.Element) -> "DiskInfo":
        """Parse disk info from XML element.

        Args:
            xml_element: XML element containing disk information

        Returns:
            DiskInfo: Parsed disk information object
        """

        # Handle potentially missing elements safely
        def get_text(xpath: str, default: str = "") -> str:
            element = xml_element.find(xpath)
            return element.text if element is not None and element.text is not None else default

        return cls(
            id=xml_element.get("id", ""),
            name=get_text("name", "Unknown"),
            vendor=get_text("vendor", "Unknown").strip(),
            model=get_text("model", "Unknown").strip(),
            serial=get_text("sn", "Unknown"),
            size_bytes=int(get_text("size", "0")),
            temperature=int(get_text("temp", "0")),
            healthy=bool(int(get_text("healthy", "0"))),
            smart_status=get_text("smart/result", "Unknown"),
        )
