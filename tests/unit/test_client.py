"""Unit tests for WDNasClient."""

import json
import xml.etree.ElementTree as ET
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import MockResponse, MockSession
from wdnas.client import WDNasClient
from wdnas.exceptions import AuthenticationError, ConnectionError, ParseError


class TestWDNasClient:
    """Tests for WDNasClient class."""

    def test_init(self) -> None:
        """Test client initialization."""
        client = WDNasClient(host="192.168.1.100", username="admin", password="password")

        assert client.host == "192.168.1.100"
        assert client.username == "admin"
        assert client.password == "password"
        assert client.http_port == 80
        assert client.https_port == 8543
        assert client.http_base_url == "http://192.168.1.100:80"
        assert client.https_base_url == "https://192.168.1.100:8543"
        assert client._authenticated is False
        assert client._cookies == {}

    def test_authenticate_success(self, mock_session: MockSession) -> None:
        """Test successful authentication."""
        # Mock a successful authentication response
        auth_url = "https://192.168.1.100:8543/nas/v1/auth"
        mock_cookies = {"session_id": "test_session"}
        mock_session.add_response(
            auth_url, "POST", MockResponse(status_code=200, text="", cookies=mock_cookies)
        )

        client = WDNasClient(host="192.168.1.100", username="admin", password="password")

        result = client.authenticate()

        assert result is True
        assert client._authenticated is True
        assert client._cookies == {"session_id": "test_session"}

    def test_authenticate_failure(self, mock_session: MockSession) -> None:
        """Test authentication failure."""
        # Mock a failed authentication response
        auth_url = "https://192.168.1.100:8543/nas/v1/auth"
        mock_session.add_response(
            auth_url, "POST", MockResponse(status_code=401, text="Authentication failed")
        )

        client = WDNasClient(host="192.168.1.100", username="admin", password="password")

        with pytest.raises(AuthenticationError) as excinfo:
            client.authenticate()

        assert "Authentication failed" in str(excinfo.value)
        assert client._authenticated is False

    def test_authenticate_connection_error(self, mock_session: MockSession) -> None:
        """Test authentication with connection error."""
        # Mock a connection error during authentication
        auth_url = "https://192.168.1.100:8543/nas/v1/auth"

        def raise_error(*args: Any, **kwargs: Any) -> None:
            raise ConnectionError("Connection refused")

        # Use patch to replace the request method
        with patch.object(mock_session, "request", side_effect=raise_error):
            client = WDNasClient(host="192.168.1.100", username="admin", password="password")

            with pytest.raises(ConnectionError):
                client.authenticate()

            assert client._authenticated is False

    def test_post_cgi_without_authentication(self) -> None:
        """Test _post_cgi method without authentication."""
        client = WDNasClient(host="192.168.1.100", username="admin", password="password")

        with pytest.raises(AuthenticationError) as excinfo:
            client._post_cgi("/cgi-bin/test.cgi", {"cmd": "test"})

        assert "You must authenticate before making API calls" in str(excinfo.value)

    def test_post_cgi_success(self, mock_session: MockSession) -> None:
        """Test successful _post_cgi method call."""
        # Mock a successful response
        cgi_url = "http://192.168.1.100:80/cgi-bin/test.cgi"
        mock_session.add_response(
            cgi_url, "POST", MockResponse(status_code=200, text="<response>Success</response>")
        )

        client = WDNasClient(host="192.168.1.100", username="admin", password="password")
        client._authenticated = True
        client._cookies = {"session_id": "test_session"}

        response = client._post_cgi("/cgi-bin/test.cgi", {"cmd": "test"})

        assert response == "<response>Success</response>"

    def test_parse_xml_response_success(self) -> None:
        """Test successful XML parsing."""
        client = WDNasClient(host="192.168.1.100", username="admin", password="password")

        xml_text = "<root><item>Test</item></root>"
        element = client.parse_xml_response(xml_text)

        assert element.tag == "root"
        item = element.find("item")
        assert item is not None
        assert item.text == "Test"

    def test_parse_xml_response_failure(self) -> None:
        """Test XML parsing failure."""
        client = WDNasClient(host="192.168.1.100", username="admin", password="password")

        invalid_xml = "<root><item>Test</root>"  # Missing closing tag

        with pytest.raises(ParseError) as excinfo:
            client.parse_xml_response(invalid_xml)

        assert "Failed to parse XML response" in str(excinfo.value)

    def test_parse_json_response_success(self) -> None:
        """Test successful JSON parsing."""
        client = WDNasClient(host="192.168.1.100", username="admin", password="password")

        json_text = '{"key": "value", "number": 42}'
        data = client.parse_json_response(json_text)

        assert data == {"key": "value", "number": 42}

    def test_parse_json_response_failure(self) -> None:
        """Test JSON parsing failure."""
        client = WDNasClient(host="192.168.1.100", username="admin", password="password")

        invalid_json = '{"key": "value", "number": 42'  # Missing closing brace

        with pytest.raises(ParseError) as excinfo:
            client.parse_json_response(invalid_json)

        assert "Failed to parse JSON response" in str(excinfo.value)

    def test_get_disks(self, mock_session: MockSession) -> None:
        """Test get_disks method."""
        # Mock the home info response
        home_url = "http://192.168.1.100:80/cgi-bin/home_mgr.cgi"
        with open("tests/fixtures/xml/home_info.xml", "r") as f:
            home_xml = f.read()

        mock_session.add_response(home_url, "POST", MockResponse(status_code=200, text=home_xml))

        client = WDNasClient(host="192.168.1.100", username="admin", password="password")
        client._authenticated = True

        disks = client.get_disks()

        assert len(disks) == 2
        assert disks[0].id == "sda"
        assert disks[0].name == "Disk 1"
        assert disks[0].size_gb == 931.3225746154785
        assert disks[1].id == "sdb"
        assert disks[1].name == "Disk 2"
