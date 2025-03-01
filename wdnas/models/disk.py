"""Disk model for WD NAS devices."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SmartInfo:
    """SMART information for a disk."""

    test_type: str
    result: str
    percent: int
    last_test_date: Optional[datetime] = None

    @classmethod
    def from_xml(cls, xml_element: ET.Element) -> "SmartInfo":
        """Parse SMART info from XML element."""
        result = xml_element.findtext("result", "Unknown")
        # Extract date from result string if present (e.g., "Pass [2025/02/28 04:04:26]")
        last_test_date = None
        if "[" in result and "]" in result:
            try:
                date_str = result[result.find("[") + 1 : result.find("]")]
                last_test_date = datetime.strptime(date_str, "%Y/%m/%d %H:%M:%S")
                result = result[: result.find("[")].strip()
            except ValueError:
                pass

        return cls(
            test_type=xml_element.findtext("test", "unknown"),
            result=result,
            percent=int(xml_element.findtext("percent", "0")),
            last_test_date=last_test_date,
        )


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
    scsi_path: str = ""
    connected: bool = False
    revision: str = ""
    device_path: str = ""
    partition_count: int = 0
    allowed: bool = False
    raid_uuid: str = ""
    failed: bool = False
    removable: bool = False
    roaming: str = ""
    over_temp: bool = False
    sleep: bool = False
    smart_info: Optional[SmartInfo] = None

    @property
    def size_gb(self) -> float:
        """Get the size in GB."""
        return self.size_bytes / (1024**3)

    @classmethod
    def from_xml(cls, xml_element: ET.Element) -> "DiskInfo":
        """Parse disk info from XML element."""

        def get_text(xpath: str, default: str = "") -> str:
            element = xml_element.find(xpath)
            return element.text if element is not None and element.text is not None else default

        def get_bool(xpath: str) -> bool:
            return bool(int(get_text(xpath, "0")))

        smart_element = xml_element.find("smart")
        smart_info = SmartInfo.from_xml(smart_element) if smart_element is not None else None

        return cls(
            id=xml_element.get("id", ""),
            name=get_text("name", "Unknown"),
            vendor=get_text("vendor", "Unknown").strip(),
            model=get_text("model", "Unknown").strip(),
            serial=get_text("sn", "Unknown"),
            size_bytes=int(get_text("size", "0")),
            temperature=int(get_text("temp", "0")),
            healthy=get_bool("healthy"),
            smart_status=smart_info.result if smart_info else "Unknown",
            scsi_path=get_text("scsi_path"),
            connected=get_bool("connected"),
            revision=get_text("rev"),
            device_path=get_text("dev"),
            partition_count=int(get_text("part_cnt", "0")),
            allowed=get_bool("allowed"),
            raid_uuid=get_text("raid_uuid"),
            failed=get_bool("failed"),
            removable=get_bool("removable"),
            roaming=get_text("roaming"),
            over_temp=get_bool("over_temp"),
            sleep=get_bool("sleep"),
            smart_info=smart_info,
        )
