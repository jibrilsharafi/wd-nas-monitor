"""Core client for interacting with Western Digital NAS devices."""

import base64
from datetime import datetime
import json
import logging
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Union

import requests
from requests.exceptions import RequestException

from .exceptions import AuthenticationError, ConnectionError, ParseError
from .models.disk import DiskInfo, SmartInfo


class WDNasClient:
    """Base client for interacting with Western Digital NAS devices."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        http_port: int = 80,
        https_port: int = 8543,
        verify_ssl: bool = False,
    ):
        """Initialize the WD NAS client.

        Args:
            host: The hostname or IP address of the NAS
            username: The username for authentication
            password: The password for authentication
            http_port: The HTTP port to connect to (default: 80)
            https_port: The HTTPS port to connect to (default: 8543)
        """
        self.host = host
        self.username = username
        self.password = password
        self.http_port = http_port
        self.https_port = https_port
        self.session = requests.Session()
        self.logger = logging.getLogger("wdnas")
        self._authenticated = False
        self._cookies: Dict[str, str] = {}

        # Build the base URLs
        self.http_base_url = f"http://{host}:{http_port}"
        self.https_base_url = f"https://{host}:{https_port}"

        self.session.verify = verify_ssl  # Allow SSL verification to be configurable

        # Validate host format
        if not re.match(r"^[\w.-]+$", host):
            raise ValueError("Invalid host format")

    def authenticate(self) -> bool:
        """Authenticate with the NAS.

        This method performs authentication using the WD EX2 Ultra API
        which requires a JSON payload sent to an HTTPS endpoint.

        Returns:
            bool: True if authentication was successful

        Raises:
            AuthenticationError: If authentication failed
            ConnectionError: If there was a problem connecting to the NAS
        """
        try:
            # WD EX2 Ultra expects a JSON payload with username and password
            # The password appears to be base64 encoded in the Postman collection
            auth_data = {
                "username": self.username,
                "password": base64.b64encode(self.password.encode()).decode(),
            }

            # Disable SSL verification since the NAS often uses a self-signed certificate
            # In production, you might want to provide the correct certificate instead
            response = self.session.post(
                f"{self.https_base_url}/nas/v1/auth", json=auth_data, timeout=10
            )

            if response.status_code == 200:
                # Store cookies for subsequent requests
                self._cookies = dict(response.cookies)
                self._authenticated = True
                self.logger.info("Successfully authenticated with NAS")
                return True
            else:
                self.logger.error(f"Authentication failed with status code {response.status_code}")
                raise AuthenticationError(
                    f"Authentication failed: {response.status_code} {response.text}"
                )

        except RequestException as e:
            self.logger.error(f"Connection error during authentication: {str(e)}")
            raise ConnectionError(f"Failed to connect to NAS: {str(e)}")

    def _post_cgi(self, cgi_path: str, data: Dict[str, str]) -> str:
        """Send a POST request to a CGI endpoint.

        Args:
            cgi_path: The CGI path (e.g., '/cgi-bin/status_mgr.cgi')
            data: The form data to send

        Returns:
            str: The raw response text

        Raises:
            ConnectionError: If there was a problem connecting to the NAS
            AuthenticationError: If authentication is required but not completed
        """
        if not self._authenticated:
            raise AuthenticationError("You must authenticate before making API calls")

        try:
            # Use the http_base_url for CGI requests
            url = f"{self.http_base_url}{cgi_path}"
            response = self.session.post(url, data=data, cookies=self._cookies, timeout=10)
            response.raise_for_status()
            return str(response.text)
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                self._authenticated = False
                raise AuthenticationError("Authentication expired or invalid")
            raise ConnectionError(f"HTTP error: {str(e)}")
        except RequestException as e:
            raise ConnectionError(f"Request failed: {str(e)}")

    def _get_xml(self, path: str, params: Optional[Dict[str, str]] = None) -> str:
        """Get an XML response from a path.

        Args:
            path: The path to the XML file (e.g., '/xml/sysinfo.xml')
            params: Optional query parameters

        Returns:
            str: The raw XML response text
        """
        if not self._authenticated:
            raise AuthenticationError("You must authenticate before making API calls")

        try:
            url = f"{self.http_base_url}{path}"
            response = self.session.post(url, cookies=self._cookies, params=params, timeout=10)
            response.raise_for_status()
            return str(response.text)
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                self._authenticated = False
                raise AuthenticationError("Authentication expired or invalid")
            raise ConnectionError(f"HTTP error: {str(e)}")
        except RequestException as e:
            raise ConnectionError(f"Request failed: {str(e)}")

    def parse_xml_response(self, xml_text: str) -> ET.Element:
        """Parse an XML response.

        Args:
            xml_text: The XML text to parse

        Returns:
            ElementTree.Element: The parsed XML root element

        Raises:
            ParseError: If the response couldn't be parsed as XML
        """
        try:
            return ET.fromstring(xml_text)
        except ET.ParseError as e:
            self.logger.error(f"Failed to parse XML response: {str(e)}")
            self.logger.debug(f"Raw response: {xml_text[:200]}...")
            raise ParseError(f"Failed to parse XML response: {str(e)}")

    def parse_xml_response_as_dict(self, xml_text: str) -> Dict[str, Any]:
        """Parse an XML response and convert it to a dictionary.

        Args:
            xml_text: The XML text to parse

        Returns:
            Dict: The parsed XML as a dictionary

        Raises:
            ParseError: If the response couldn't be parsed as XML
        """
        root = self.parse_xml_response(xml_text)
        return self._xml_to_dict(root)

    def parse_json_response(self, json_text: str) -> Dict[str, Any]:
        """Parse a JSON response.

        Args:
            json_text: The JSON text to parse

        Returns:
            Dict: The parsed JSON data

        Raises:
            ParseError: If the response couldn't be parsed as JSON
        """
        try:
            response: Dict[str, Any] = json.loads(json_text)
            return response
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {str(e)}")
            self.logger.debug(f"Raw response: {json_text[:200]}...")
            raise ParseError(f"Failed to parse JSON response: {str(e)}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get system status information.

        Returns:
            Dict: System status information
        """
        response = self._post_cgi("/cgi-bin/status_mgr.cgi", {"cmd": "resource"})
        return self.parse_xml_response_as_dict(response)

    def _xml_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """Convert an XML element to a dictionary.

        Args:
            element: The XML element to convert

        Returns:
            Dict: The converted dictionary
        """
        result: Dict[str, Any] = {}

        # Add attributes if present
        if element.attrib:
            result.update(element.attrib)

        # Handle child elements
        children_by_tag: Dict[str, Union[Any, List[Any]]] = {}
        for child in element:
            child_data = self._xml_to_dict(child)
            if child.tag in children_by_tag:
                # If we've seen this tag before, ensure it becomes a list
                if isinstance(children_by_tag[child.tag], list):
                    children_by_tag[child.tag].append(child_data)
                else:
                    children_by_tag[child.tag] = [children_by_tag[child.tag], child_data]
            else:
                children_by_tag[child.tag] = child_data

        # Add all child data to result
        result.update(children_by_tag)

        # Handle element text
        if element.text and element.text.strip():
            if not result:  # If there are no children or attributes
                result = {"text": element.text.strip()}
            else:
                result["text"] = element.text.strip()

        return result

    def get_system_logs(self) -> Dict[str, Any]:
        """Get system logs.

        Returns:
            Dict: System logs information
        """
        data = {
            "page": "1",
            "rp": "10",
            "sortname": "",
            "sortorder": "asc",
            "query": "",
            "qtype": "",
            "f_field": "false",
            "cmd": "cgi_log_system",
            "user": "",
        }
        response = self._post_cgi("/cgi-bin/system_mgr.cgi", data)
        return self.parse_json_response(response)

    def get_firmware_version(self) -> Dict[str, Any]:
        """Get firmware version information.

        Returns:
            Dict[str, Any]: Firmware version information as dictionary
        """
        response = self._post_cgi("/cgi-bin/system_mgr.cgi", {"cmd": "get_firm_v_xml"})
        return self.parse_xml_response_as_dict(response)

    def get_home_info(self) -> Dict[str, Any]:
        """Get home information.

        Returns:
            Dict[str, Any]: Home information as dictionary
        """
        response = self._post_cgi("/cgi-bin/home_mgr.cgi", {"cmd": "2"})
        return self.parse_xml_response_as_dict(response)

    def get_disk_smart_info(self, disk_id: str) -> Dict[str, Any]:
        """Get SMART information for a disk.

        Args:
            disk_id: The disk ID (e.g., 'sda', 'sdb')

        Returns:
            Dict: SMART information for the disk
        """
        data = {"f_field": disk_id, "cmd": "cgi_Status_SMART_HD_Info"}
        response = self._post_cgi("/cgi-bin/smart.cgi", data)
        return self.parse_json_response(response)

    def get_system_info(self) -> Dict[str, Any]:
        """Get detailed system information.

        Returns:
            Dict[str, Any]: System information as dictionary
        """
        # The id parameter appears to be a timestamp or random number
        import time

        params = {"id": str(int(time.time()))}
        response = self._get_xml("/xml/sysinfo.xml", params)
        return self.parse_xml_response_as_dict(response)

    def get_disks(self) -> List[DiskInfo]:
        """Get information about all disks in the NAS.

        Returns:
            List[DiskInfo]: List of disk information objects

        Raises:
            Various exceptions from underlying methods
        """
        # Extract disk information from home information
        home_data = self.get_home_info()

        # Navigate to disks in the dictionary structure
        # The structure might be {'disks': {'disk': [...]}} or something with direct 'disk' key
        disks_data = None
        if "disks" in home_data and "disk" in home_data["disks"]:
            disks_data = home_data["disks"]["disk"]
        elif "disk" in home_data:
            disks_data = home_data["disk"]

        # Check if we found any disks
        if not disks_data:
            self.logger.warning("No disks found in home information")
            return []

        # If there's only one disk, make sure it's in a list
        if not isinstance(disks_data, list):
            disks_data = [disks_data]

        result = []
        for disk_data in disks_data:
            # Create DiskInfo from dictionary data
            disk_info = self._create_disk_info_from_dict(disk_data)
            result.append(disk_info)

        return result

    def _get_nested_value(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Extract a value from possibly nested dictionary structure.
        
        Args:
            data: Dictionary to extract from
            key: Key to extract
            default: Default value if key not found
            
        Returns:
            The value at the key, or default if not found
        """
        if key not in data:
            return default
            
        value = data[key]
        # If value is a dict with just a 'text' key, return the text value
        if isinstance(value, dict) and "text" in value and len(value) == 1:
            return value["text"]
        return value

    def _create_disk_info_from_dict(self, disk_data: Dict[str, Any]) -> DiskInfo:
        """Create a DiskInfo object from dictionary data.

        Args:
            disk_data: Dictionary containing disk information

        Returns:
            DiskInfo: A disk information object
        """
        # Extract smart info if available
        smart_info = None
        if "smart" in disk_data:
            smart_data = disk_data["smart"]
            result_raw = self._get_nested_value(smart_data, "result", "Unknown")
            test_type = self._get_nested_value(smart_data, "test", "unknown")
            percent_str = self._get_nested_value(smart_data, "percent", "0")
            
            smart_info = SmartInfo(
                test_type=test_type,
                result=self._extract_smart_result(result_raw),
                percent=int(percent_str),
                last_test_date=self._extract_smart_date(result_raw),
            )

        # Get values with helper method that handles nested structure
        return DiskInfo(
            id=disk_data.get("id", ""),  # id is typically an attribute, not nested
            name=self._get_nested_value(disk_data, "name", "Unknown"),
            vendor=self._get_nested_value(disk_data, "vendor", "Unknown").strip(),
            model=self._get_nested_value(disk_data, "model", "Unknown").strip(),
            serial=self._get_nested_value(disk_data, "sn", "Unknown"),
            size_bytes=int(self._get_nested_value(disk_data, "size", "0")),
            temperature=int(self._get_nested_value(disk_data, "temp", "0")),
            healthy=bool(int(self._get_nested_value(disk_data, "healthy", "0"))),
            smart_status=smart_info.result if smart_info else "Unknown",
            scsi_path=self._get_nested_value(disk_data, "scsi_path", ""),
            connected=bool(int(self._get_nested_value(disk_data, "connected", "0"))),
            revision=self._get_nested_value(disk_data, "rev", ""),
            device_path=self._get_nested_value(disk_data, "dev", ""),
            partition_count=int(self._get_nested_value(disk_data, "part_cnt", "0")),
            allowed=bool(int(self._get_nested_value(disk_data, "allowed", "0"))),
            raid_uuid=self._get_nested_value(disk_data, "raid_uuid", ""),
            failed=bool(int(self._get_nested_value(disk_data, "failed", "0"))),
            removable=bool(int(self._get_nested_value(disk_data, "removable", "0"))),
            roaming=self._get_nested_value(disk_data, "roaming", ""),
            over_temp=bool(int(self._get_nested_value(disk_data, "over_temp", "0"))),
            sleep=bool(int(self._get_nested_value(disk_data, "sleep", "0"))),
            smart_info=smart_info,
        )

    def _extract_smart_result(self, result_str: str) -> str:
        """Extract the actual result from a SMART result string.

        Args:
            result_str: The SMART result string which may contain a date

        Returns:
            str: The clean result string
        """
        if "[" in result_str and "]" in result_str:
            return result_str[: result_str.find("[")].strip()
        return result_str

    def _extract_smart_date(self, result_str: str) -> Optional[datetime]:
        """Extract the date from a SMART result string.

        Args:
            result_str: The SMART result string which may contain a date

        Returns:
            Optional[datetime]: The extracted date or None
        """
        from datetime import datetime

        if "[" in result_str and "]" in result_str:
            try:
                date_str = result_str[result_str.find("[") + 1 : result_str.find("]")]
                return datetime.strptime(date_str, "%Y/%m/%d %H:%M:%S")
            except ValueError:
                pass
        return None
