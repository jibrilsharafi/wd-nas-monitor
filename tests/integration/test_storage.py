"""Integration tests for storage information retrieval."""


from wdnas.devices.ex2 import EX2UltraDevice


class TestStorageInfo:
    """Test storage information retrieval."""

    def test_get_storage_usage(self, ex2_device: EX2UltraDevice) -> None:
        """Test retrieving storage usage information."""
        storage = ex2_device.get_storage_usage()
        
        # Verify storage information format
        assert isinstance(storage, dict)
        assert "total_gb" in storage
        assert "used_gb" in storage
        assert "free_gb" in storage
        assert "usage_percent" in storage
        
        # Verify logical relationships
        assert storage["total_gb"] > 0
        assert storage["used_gb"] >= 0
        assert storage["free_gb"] >= 0
        assert 0 <= storage["usage_percent"] <= 100
        
        # Total should equal used + free (with small floating-point tolerance)
        expected_total = storage["used_gb"] + storage["free_gb"]
        assert abs(storage["total_gb"] - expected_total) < 0.1
