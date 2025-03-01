"""Integration tests for authentication."""

from typing import Any, Dict
import pytest

from wdnas.client import WDNasClient
from wdnas.exceptions import AuthenticationError


class TestAuthentication:
    """Test authentication against a real device."""

    def test_successful_authentication(self, config: Dict[str, Any]) -> None:
        """Test that authentication succeeds with valid credentials."""
        client = WDNasClient(
            host=config["host"],
            username=config["username"],
            password=config["password"],
            verify_ssl=False, # We don't have a valid SSL cert on the device
            # so we need to disable SSL verification
        )

        # Authenticate should not raise exceptions
        assert client.authenticate() is True
        assert client._authenticated is True

    def test_failed_authentication(self, config: Dict[str, Any]) -> None:
        """Test that authentication fails with invalid credentials."""
        client = WDNasClient(
            host=config["host"],
            username=config["username"],
            password="wrong_password",
            verify_ssl=False,
        )

        # Should raise AuthenticationError
        with pytest.raises(AuthenticationError):
            client.authenticate()
