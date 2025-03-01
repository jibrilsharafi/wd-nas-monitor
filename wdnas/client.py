"""Core client for interacting with Western Digital NAS devices."""

import base64
import json
import logging
import re
from typing import Any, Dict, List, Optional

import requests
import xmltodict
from requests.exceptions import RequestException

from .exceptions import AuthenticationError, ConnectionError, ParseError

TIMEOUT_REQUESTS = 10


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
                f"{self.https_base_url}/nas/v1/auth", json=auth_data, timeout=TIMEOUT_REQUESTS
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

    def _post_cgi(
        self, cgi_path: str, form_data: Dict[str, str], json_response: bool = False
    ) -> Dict[str, Any]:
        """Send a POST request to a CGI endpoint and parse the XML response.

        Args:
            cgi_path: The CGI path (e.g., '/cgi-bin/status_mgr.cgi')
            data: The form data to send

        Returns:
            Dict[str, Any]: The parsed XML response as a dictionary

        Raises:
            ConnectionError: If there was a problem connecting to the NAS
            AuthenticationError: If authentication is required but not completed
        """
        if not self._authenticated:
            raise AuthenticationError("You must authenticate before making API calls")

        try:
            # Use the https_base_url for CGI requests
            url = f"{self.https_base_url}{cgi_path}"
            headers = {"Content-Type": "application/x-www-form-urlencoded"} # All requests for WD NAS use this
            
            response = self.session.post(
                url,
                data=form_data,
                headers=headers,
                cookies=self._cookies,
                timeout=TIMEOUT_REQUESTS,
            )
            response.raise_for_status()

            # Immediately parse the XML response
            if json_response:
                return self.parse_json_response(response.text)
            else:
                return self.parse_xml_response_as_dict(response.text)

        except requests.HTTPError as e:
            if e.response.status_code == 401:
                self._authenticated = False
                raise AuthenticationError("Authentication expired or invalid")
            raise ConnectionError(f"HTTP error: {str(e)}")
        except RequestException as e:
            raise ConnectionError(f"Request failed: {str(e)}")

    def _get_xml(self, path: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get an XML response from a path and immediately parse to dictionary.

        Args:
            path: The path to the XML file (e.g., '/xml/sysinfo.xml')
            params: Optional query parameters

        Returns:
            Dict[str, Any]: The parsed XML as a dictionary
        """
        if not self._authenticated:
            raise AuthenticationError("You must authenticate before making API calls")

        try:
            url = f"{self.http_base_url}{path}"
            response = self.session.post(
                url, cookies=self._cookies, params=params, timeout=TIMEOUT_REQUESTS
            )
            response.raise_for_status()

            # Immediately parse the XML response
            return self.parse_xml_response_as_dict(response.text)

        except requests.HTTPError as e:
            if e.response.status_code == 401:
                self._authenticated = False
                raise AuthenticationError("Authentication expired or invalid")
            raise ConnectionError(f"HTTP error: {str(e)}")
        except RequestException as e:
            raise ConnectionError(f"Request failed: {str(e)}")

    def parse_xml_response_as_dict(self, xml_text: str) -> Dict[str, Any]:
        """Parse an XML response and convert it to a dictionary.

        Args:
            xml_text: The XML text to parse

        Returns:
            Dict: The parsed XML as a dictionary

        Raises:
            ParseError: If the response couldn't be parsed as XML
        """
        try:
            result = xmltodict.parse(xml_text.strip())
            if not isinstance(result, dict):
                raise ParseError(f"Expected dict result, got {type(result)}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to parse XML response: {str(e)}")
            self.logger.debug(f"Raw response: {xml_text[:200]}...")
            raise ParseError(f"Failed to parse XML response: {str(e)}")

    def parse_json_response(self, json_text: str) -> Dict[str, Any]:
        """Parse a JSON response.

        Args:
            json_text: The JSON text to parse

        Returns:
            Dict: The parsed JSON as a dictionary

        Raises:
            ParseError: If the response couldn't be parsed as JSON
        """
        try:
            response = json.loads(json_text)
            if isinstance(response, dict):  # No simple lists expected in this context
                return response
            else:
                raise ParseError(f"Unexpected JSON structure: {type(response)}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {str(e)}")
            self.logger.debug(f"Raw response: {json_text[:200]}...")
            raise ParseError(f"Failed to parse JSON response: {str(e)}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get system status information.

        Returns:
            Dict: System status information
        """
        return self._post_cgi("/cgi-bin/status_mgr.cgi", {"cmd": "resource"})

    def get_device_info(self) -> Dict[str, Any]:
        """Get device information.

        Returns:
            Dict: Device information
        """
        return self._post_cgi("/cgi-bin/system_mgr.cgi", {"cmd": "cgi_get_device_info"})

    def get_system_logs(self, max_pages: int = 10) -> List[Dict[str, List[Dict[str, Any]]]]:
        """Get system logs with pagination.

        Args:
            max_pages: Maximum number of pages to retrieve (default: 10)

        Returns:
            List[Dict]: System logs information from all available pages up to max_pages
        """
        all_logs: List[Dict[str, List[Dict[str, Any]]]] = []
        page = 1

        while page <= max_pages:
            data = {
                "page": str(page),
                "cmd": "cgi_log_system",
            }
            response = self._post_cgi("/cgi-bin/system_mgr.cgi", data, json_response=True)

            all_logs.append(response)
            if not response.get("rows"):
                break

            page += 1

        return all_logs

    def get_firmware_version(self) -> Dict[str, Any]:
        """Get firmware version information.

        Returns:
            Dict[str, Any]: Firmware version information as dictionary
        """
        return self._post_cgi("/cgi-bin/system_mgr.cgi", {"cmd": "get_firm_v_xml"})

    def get_home_info(self) -> Dict[str, Any]:
        """Get home information.

        Returns:
            Dict[str, Any]: Home information as dictionary
        """
        return self._post_cgi("/cgi-bin/home_mgr.cgi", {"cmd": "2"})

    def get_disks_smart_info(self) -> Dict[str, Dict[str, Any]]:
        """Get SMART information for a disk.

        Args:
            disk_id: The disk ID (e.g., 'sda', 'sdb')

        Returns:
            Dict: SMART information for the disk
        """
        disks_info: Dict[str, Dict[str, Any]] = {}

        LIST_DISKS = ["sda", "sdb"]  # TODO: get this from the NAS

        for disk_id in LIST_DISKS:
            data = {"f_field": disk_id, "cmd": "cgi_Status_SMART_HD_Info"}
            response = self._post_cgi("/cgi-bin/smart.cgi", data)
            if response["rows"].get("row"):
                disks_info[disk_id] = response
            else:
                break

        return disks_info

    def get_system_info(self) -> Dict[str, Any]:
        """Get detailed system information.

        Returns:
            Dict[str, Any]: System information as dictionary
        """
        # The id parameter appears to be a timestamp or random number
        import time

        params = {"id": str(int(time.time()))}
        return self._get_xml("/xml/sysinfo.xml", params)

    def get_all_data(self) -> Dict[str, Any]:
        """Get all data from the NAS.

        Returns:
            Dict[str, Any]: All data as dictionary
        """
        return {
            "system_status": self.get_system_status(),
            "device_info": self.get_device_info(),
            "system_logs": self.get_system_logs(),
            "firmware_version": self.get_firmware_version(),
            "home_info": self.get_home_info(),
            "disks_smart_info": self.get_disks_smart_info(),
            "system_info": self.get_system_info(),
        }
