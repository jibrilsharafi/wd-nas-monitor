"""Pytest fixtures for WD NAS Monitor tests."""

from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import pytest
import requests

# Base directory for fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def xml_fixtures_dir() -> Path:
    """Return the path to the XML fixtures directory."""
    dir_path = FIXTURES_DIR / "xml"
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


@pytest.fixture
def json_fixtures_dir() -> Path:
    """Return the path to the JSON fixtures directory."""
    dir_path = FIXTURES_DIR / "json"
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


@pytest.fixture
def load_xml_fixture() -> Callable[[str], ET.Element]:
    """Fixture to load XML fixture data."""

    def _load_xml(filename: str) -> ET.Element:
        path = FIXTURES_DIR / "xml" / filename
        if not path.exists():
            pytest.skip(f"Fixture file not found: {path}")
        return ET.parse(path).getroot()

    return _load_xml


@pytest.fixture
def load_json_fixture() -> Callable[[str], Dict[str, Any]]:
    """Fixture to load JSON fixture data."""

    def _load_json(filename: str) -> Dict[str, Any]:
        path = FIXTURES_DIR / "json" / filename
        if not path.exists():
            pytest.skip(f"Fixture file not found: {path}")
        with open(path, "r") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise TypeError(f"Expected JSON object, got {type(data).__name__}")
            return data

    return _load_json


@pytest.fixture
def load_fixture_text() -> Callable[[str, str], str]:
    """Fixture to load raw text fixture data."""

    def _load(subdir: str, filename: str) -> str:
        path = FIXTURES_DIR / subdir / filename
        if not path.exists():
            pytest.skip(f"Fixture file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    return _load


# Mock response data
@pytest.fixture
def mock_system_info_response() -> str:
    """Mock system info XML response."""
    return """
    <system>
        <name>MyNAS</name>
        <model>WD My Cloud EX2 Ultra</model>
        <firmware_version>2.31.204</firmware_version>
        <serial>WD1234567890</serial>
        <cpu_usage>25</cpu_usage>
        <memory>
            <total>512000000</total>
            <used>256000000</used>
        </memory>
        <uptime>1 days, 12:34:56</uptime>
        <temperature>42</temperature>
    </system>
    """


@pytest.fixture
def mock_home_info_response() -> str:
    """Mock home info XML response with disk information."""
    return """
    <home_info>
        <volume id="vol_1">
            <capacity>1000000000000</capacity>
            <used>500000000000</used>
            <free>500000000000</free>
            <usage>50</usage>
        </volume>
        <disks>
            <disk id="sda">
                <name>Disk 1</name>
                <vendor>WDC</vendor>
                <model>WD10EFRX-68FYTN0</model>
                <sn>WD-XYZ123456789</sn>
                <size>1000000000000</size>
                <temp>40</temp>
                <healthy>1</healthy>
                <smart>
                    <result>PASS</result>
                </smart>
            </disk>
            <disk id="sdb">
                <name>Disk 2</name>
                <vendor>WDC</vendor>
                <model>WD10EFRX-68FYTN0</model>
                <sn>WD-XYZ987654321</sn>
                <size>1000000000000</size>
                <temp>42</temp>
                <healthy>1</healthy>
                <smart>
                    <result>PASS</result>
                </smart>
            </disk>
        </disks>
    </home_info>
    """


@pytest.fixture
def mock_firmware_response() -> str:
    """Mock firmware XML response."""
    return """
    <firmware>
        <version>2.31.204</version>
        <build>20200615</build>
        <release_notes>https://example.com/release_notes</release_notes>
    </firmware>
    """


@pytest.fixture
def mock_smart_response() -> Dict[str, Any]:
    """Mock SMART JSON response."""
    return {
        "page": "1",
        "total": 2,
        "rows": [
            {"id": "1", "cell": ["1", "5", "Reallocated Sectors Count", "0", "140", "140", "OK"]},
            {"id": "2", "cell": ["2", "197", "Current Pending Sectors", "0", "0", "0", "OK"]},
        ],
    }


# Mock response class
class MockResponse:
    """Mock requests.Response object."""

    def __init__(
        self,
        status_code: int,
        text: str = "",
        json_data: Optional[Dict[str, Any]] = None,
        cookies: Optional[Dict[str, str]] = None,
    ):
        self.status_code = status_code
        self.text = text
        self._json = json_data
        self.cookies = cookies or {}

    def json(self) -> Dict[str, Any]:
        if self._json is None:
            return {}
        return self._json

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"Mock HTTP Error: {self.status_code}")


# Mock session class
class MockSession:
    """Mock requests.Session for testing."""

    def __init__(self) -> None:
        self.responses: Dict[Tuple[str, str], MockResponse] = {}
        self.requests: List[Tuple[str, str, Dict[str, Any]]] = []
        self.headers: Dict[str, str] = {}

    def add_response(self, url: str, method: str, response: MockResponse) -> None:
        self.responses[(url, method.upper())] = response

    def request(self, method: str, url: str, **kwargs: Any) -> MockResponse:
        self.requests.append((method.upper(), url, kwargs))
        key = (url, method.upper())
        if key in self.responses:
            return self.responses[key]
        return MockResponse(404, text="Not Found")

    def get(self, url: str, **kwargs: Any) -> MockResponse:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> MockResponse:
        return self.request("POST", url, **kwargs)


@pytest.fixture
def mock_session(monkeypatch: pytest.MonkeyPatch) -> MockSession:
    """Mock requests.Session for testing."""
    mock = MockSession()
    monkeypatch.setattr(requests, "Session", lambda: mock)
    return mock
