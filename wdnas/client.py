"""Core client for interacting with Western Digital NAS devices."""

import base64
import json
import logging
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Union

import requests
from requests.exceptions import RequestException

from .exceptions import AuthenticationError, ConnectionError, ParseError
from .models.disk import DiskInfo


class WDNasClient:
    """Base client for interacting with Western Digital NAS devices."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        http_port: int = 80,
        https_port: int = 8543,
        verify_ssl: bool = True,
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
                f"{self.https_base_url}/nas/v1/auth", json=auth_data, timeout=10, verify=False
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
            response = self.session.post(
                url, data=data, cookies=self._cookies, timeout=10, verify=False
            )
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
            response = self.session.post(
                url, cookies=self._cookies, params=params, timeout=10, verify=False
            )
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
        xml_root = self.parse_xml_response(response)
        # Convert XML to dictionary
        return self._xml_to_dict(xml_root)

    def _xml_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """Convert an XML element to a dictionary.

        Args:
            element: The XML element to convert

        Returns:
            Dict: The converted dictionary
        """
        result: Dict[str, Any] = {}
        for child in element:
            if len(child) == 0:
                result[child.tag] = child.text or ""
            else:
                result[child.tag] = self._xml_to_dict(child)
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

    def get_firmware_version(self) -> ET.Element:
        """Get firmware version information.

        Returns:
            ElementTree.Element: Firmware version information
        """
        response = self._post_cgi("/cgi-bin/system_mgr.cgi", {"cmd": "get_firm_v_xml"})
        return self.parse_xml_response(response)

    def get_home_info(self) -> ET.Element:
        """Get home information.

        Returns:
            ElementTree.Element: Home information
        """
        response = self._post_cgi("/cgi-bin/home_mgr.cgi", {"cmd": "2"})
        return self.parse_xml_response(response)

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

    def get_system_info(self) -> ET.Element:
        """Get detailed system information.

        Returns:
            ElementTree.Element: System information
        """
        # The id parameter appears to be a timestamp or random number
        import time

        params = {"id": str(int(time.time()))}
        response = self._get_xml("/xml/sysinfo.xml", params)
        return self.parse_xml_response(response)

    def get_disks(self) -> List[DiskInfo]:
        """Get information about all disks in the NAS.

        Returns:
            List[DiskInfo]: List of disk information objects

        Raises:
            Various exceptions from underlying methods
        """
        # Extract disk information from home information
        home_xml = self.get_home_info()
        disks_xml = home_xml.findall(".//disk")

        if not disks_xml:
            self.logger.warning("No disks found in home information")
            return []

        return [DiskInfo.from_xml(disk_xml) for disk_xml in disks_xml]
