"""Fixtures for integration tests."""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pytest
import yaml

from wdnas.client import WDNasClient
from wdnas.devices.ex2 import EX2UltraDevice


def load_config() -> Dict[str, Any]:
    """Load configuration from config file or environment variables."""
    # Try to load from config file first
    config_file = Path(__file__).parent.parent / "config.yaml"

    if config_file.exists():
        with open(config_file, "r") as f:
            return yaml.safe_load(f) or {}

    # Fall back to environment variables
    return {
        "host": os.environ.get("WDNAS_HOST", ""),
        "username": os.environ.get("WDNAS_USERNAME", ""),
        "password": os.environ.get("WDNAS_PASSWORD", ""),
        "http_port": int(os.environ.get("WDNAS_HTTP_PORT", "80")),
        "https_port": int(os.environ.get("WDNAS_HTTPS_PORT", "8443")),
    }


def requires_config(config: Dict[str, Any]) -> None:
    """Check if required configuration is available."""
    missing = []
    for key in ["host", "username", "password"]:
        if not config.get(key):
            missing.append(key)

    if missing:
        pytest.skip(f"Missing required configuration: {', '.join(missing)}")


@pytest.fixture
def config() -> Dict[str, Any]:
    """Provide configuration for tests."""
    config = load_config()
    requires_config(config)
    return config


@pytest.fixture
def client(config: Dict[str, Any]) -> WDNasClient:
    """Create an authenticated client for testing."""
    client = WDNasClient(
        host=config["host"],
        username=config["username"],
        password=config["password"],
        http_port=config.get("http_port", 80),
        https_port=config.get("https_port", 8443),
        verify_ssl=config.get("verify_ssl", False),
    )

    # Authenticate
    client.authenticate()
    return client


@pytest.fixture
def ex2_device(client: WDNasClient) -> EX2UltraDevice:
    """Create an EX2Ultra device instance for testing."""
    return EX2UltraDevice(client)
