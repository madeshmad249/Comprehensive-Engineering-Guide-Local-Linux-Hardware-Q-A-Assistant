"""Tests for system capability discovery and privilege detection."""
from hw_assistant.core.discovery import discover_system_capabilities


def test_discover_mock_mode():
    caps = discover_system_capabilities(mock=True)
    assert caps.is_linux is True
    assert caps.has_lscpu is True
    assert caps.has_dmidecode is True
    assert caps.has_sudo_dmidecode is True
    assert "get_memory_topology" in caps.available_tools
    assert "get_cpu_info" in caps.available_tools
    assert "get_block_devices" in caps.available_tools


def test_discover_native_mode():
    caps = discover_system_capabilities(mock=False)
    # Native discovery returns a valid SystemCapabilities model regardless of OS
    assert isinstance(caps.is_linux, bool)
    assert isinstance(caps.available_tools, list)
