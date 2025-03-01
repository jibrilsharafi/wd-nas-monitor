"""Unit tests for WDNasClient."""

import base64
from unittest.mock import MagicMock, patch

import pytest
import requests

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

    @patch("requests.Session.post")
    def test_authenticate_success(self, mock_post: MagicMock) -> None:
        """Test successful authentication."""
        # Mock a successful authentication response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.cookies = {"session_id": "test_session"}
        mock_post.return_value = mock_response

        client = WDNasClient(host="192.168.1.100", username="admin", password="password")
        result = client.authenticate()

        # Verify request was made correctly
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["username"] == "admin"
        assert kwargs["json"]["password"] == base64.b64encode(b"password").decode()

        # Verify results
        assert result is True
        assert client._authenticated is True
        assert client._cookies == {"session_id": "test_session"}

    @patch("requests.Session.post")
    def test_authenticate_failure(self, mock_post: MagicMock) -> None:
        """Test authentication failure."""
        # Mock a failed authentication response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Authentication failed"
        mock_post.return_value = mock_response

        client = WDNasClient(host="192.168.1.100", username="admin", password="password")

        with pytest.raises(AuthenticationError) as excinfo:
            client.authenticate()

        assert "Authentication failed" in str(excinfo.value)
        assert client._authenticated is False

    @patch("requests.Session.post")
    def test_authenticate_connection_error(self, mock_post: MagicMock) -> None:
        """Test authentication with connection error."""
        # Mock a connection error during authentication
        mock_post.side_effect = requests.exceptions.RequestException("Connection refused")

        client = WDNasClient(host="192.168.1.100", username="admin", password="password")

        with pytest.raises(ConnectionError) as excinfo:
            client.authenticate()

        assert "Failed to connect to NAS" in str(excinfo.value)
        assert client._authenticated is False

    def test_post_cgi_without_authentication(self) -> None:
        """Test _post_cgi method without authentication."""
        client = WDNasClient(host="192.168.1.100", username="admin", password="password")

        with pytest.raises(AuthenticationError) as excinfo:
            client._post_cgi("/cgi-bin/test.cgi", {"cmd": "test"})

        assert "You must authenticate before making API calls" in str(excinfo.value)

    @patch("requests.Session.post")
    def test_post_cgi_success(self, mock_post: MagicMock) -> None:
        """Test successful _post_cgi method call."""
        # Mock a successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<response>Success</response>"
        mock_post.return_value = mock_response

        # Prepare parsed XML response
        parsed_response = {"response": "Success"}

        with patch("xmltodict.parse", return_value=parsed_response) as mock_parse:
            client = WDNasClient(host="192.168.1.100", username="admin", password="password")
            client._authenticated = True
            client._cookies = {"session_id": "test_session"}

            response = client._post_cgi("/cgi-bin/test.cgi", {"cmd": "test"})

            # Verify the response is parsed correctly
            assert response == parsed_response
            mock_parse.assert_called_once_with("<response>Success</response>".strip())

    @patch("requests.Session.post")
    def test_parse_xml_response_as_dict(self, mock_post: MagicMock) -> None:
        """Test parse_xml_response_as_dict method."""
        client = WDNasClient(host="192.168.1.100", username="admin", password="password")

        xml_str = "<response>Success</response>"
        expected_dict = {"response": "Success"}

        with patch("xmltodict.parse", return_value=expected_dict) as mock_parse:
            result = client.parse_xml_response_as_dict(xml_str)
            assert result == expected_dict
            mock_parse.assert_called_once_with(xml_str.strip())

    @patch("requests.Session.post")
    def test_get_system_status(self, mock_post: MagicMock) -> None:
        """Test get_system_status method."""
        # Mock the system status response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<response><status>OK</status></response>"
        mock_post.return_value = mock_response

        parsed_response = {"response": {"status": "OK"}}

        with patch.object(WDNasClient, "parse_xml_response_as_dict", return_value=parsed_response):
            client = WDNasClient(host="192.168.1.100", username="admin", password="password")
            client._authenticated = True

            result = client.get_system_status()
            assert result == parsed_response
            mock_post.assert_called_once()

    @patch("requests.Session.post")
    def test_get_all_data(self, mock_post: MagicMock) -> None:
        """Test get_all_data method."""
        client = WDNasClient(host="192.168.1.100", username="admin", password="password")
        client._authenticated = True

        # Mock all the individual methods
        with (
            patch.object(client, "get_system_status", return_value={"status": "OK"}) as mock_status,
            patch.object(client, "get_device_info", return_value={"name": "MyNAS"}) as mock_device,
            patch.object(client, "get_system_logs", return_value=[{"logs": "data"}]) as mock_logs,
            patch.object(
                client, "get_firmware_version", return_value={"version": "1.0"}
            ) as mock_firmware,
            patch.object(client, "get_home_info", return_value={"cpu": "25%"}) as mock_home,
            patch.object(
                client, "get_disks_smart_info", return_value={"disk1": {"health": "good"}}
            ) as mock_disks,
            patch.object(client, "get_system_info", return_value={"model": "EX2"}) as mock_sysinfo,
        ):

            result = client.get_all_data()

            # Verify all methods were called
            mock_status.assert_called_once()
            mock_device.assert_called_once()
            mock_logs.assert_called_once()
            mock_firmware.assert_called_once()
            mock_home.assert_called_once()
            mock_disks.assert_called_once()
            mock_sysinfo.assert_called_once()

            # Verify the result contains all expected data
            assert result["system_status"] == {"status": "OK"}
            assert result["device_info"] == {"name": "MyNAS"}
            assert result["system_logs"] == [{"logs": "data"}]
            assert result["firmware_version"] == {"version": "1.0"}
            assert result["home_info"] == {"cpu": "25%"}
            assert result["disks_smart_info"] == {"disk1": {"health": "good"}}
            assert result["system_info"] == {"model": "EX2"}

    @patch("requests.Session.post")
    def test_parse_json_response(self, mock_post: MagicMock) -> None:
        """Test JSON parsing."""
        client = WDNasClient(host="192.168.1.100", username="admin", password="password")

        # Test successful parsing
        json_text = '{"key": "value", "number": 42}'
        result = client.parse_json_response(json_text)
        assert result == {"key": "value", "number": 42}

        # Test parsing failure
        with pytest.raises(ParseError) as excinfo:
            client.parse_json_response('{"invalid": json}')
        assert "Failed to parse JSON response" in str(excinfo.value)
