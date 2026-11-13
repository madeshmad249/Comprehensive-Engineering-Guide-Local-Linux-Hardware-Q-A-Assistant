"""Tests for raw CLI output parsing and Pydantic model normalization."""
import json
import pytest
from hw_assistant.fixtures.mock_data import (
    MOCK_DMIDECODE_MEMORY,
    MOCK_LSCPU,
    MOCK_LSBLK_JSON,
    MOCK_FREE_BYTES,
    MOCK_PROC_MEMINFO,
    MOCK_LSPCI,
    MOCK_DMIDECODE_SYSTEM,
    MOCK_SYS_DMI_ID,
    MOCK_OS_RELEASE,
)
from hw_assistant.parsers.memory import parse_dmidecode_memory, parse_free_bytes, parse_proc_meminfo
from hw_assistant.parsers.cpu import parse_lscpu, parse_proc_cpuinfo
from hw_assistant.parsers.disk import parse_lsblk_json
from hw_assistant.parsers.pci import parse_lspci
from hw_assistant.parsers.system import parse_dmidecode_system, parse_sysfs_dmi, parse_os_release


def test_parse_dmidecode_memory():
    topo = parse_dmidecode_memory(MOCK_DMIDECODE_MEMORY, include_empty=True)
    assert topo.total_slots == 2
    assert topo.used_slots == 1
    assert topo.free_slots == 1
    assert topo.maximum_capacity_human == "64 GB"
    assert topo.maximum_capacity_bytes == 64 * 1024 * 1024 * 1024
    assert topo.is_upgradeable is True
    assert len(topo.installed_modules) == 2

    # Populated slot
    s0 = topo.installed_modules[0]
    assert s0.locator == "ChannelA-DIMM0"
    assert s0.size_human == "16 GB"
    assert s0.size_bytes == 16 * 1024 * 1024 * 1024
    assert s0.type == "DDR4"
    assert s0.speed == "3200 MT/s"
    assert s0.manufacturer == "Micron Technology"
    assert s0.is_empty is False

    # Empty slot
    s1 = topo.installed_modules[1]
    assert s1.locator == "ChannelB-DIMM0"
    assert s1.is_empty is True
    assert s1.size_human == "No Module Installed"

    # Filter empty slots
    topo_filtered = parse_dmidecode_memory(MOCK_DMIDECODE_MEMORY, include_empty=False)
    assert len(topo_filtered.installed_modules) == 1
    assert topo_filtered.installed_modules[0].locator == "ChannelA-DIMM0"


def test_parse_lscpu():
    cpu = parse_lscpu(MOCK_LSCPU)
    assert "AMD Ryzen 7 PRO 5850U" in cpu.model_name
    assert cpu.architecture == "x86_64"
    assert cpu.cores == 16
    assert cpu.threads == 16
    assert cpu.max_mhz == 4400.0
    assert cpu.min_mhz == 1400.0
    assert cpu.l3_cache == "16 MiB (1 instance)"
    assert cpu.virtualization == "AMD-V"
    assert "avx2" in cpu.flags


def test_parse_proc_cpuinfo():
    mock_cpuinfo = """processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model_name	: Intel(R) Core(TM) i7-1370P
cpu MHz		: 2200.000
cache size	: 24576 KB
flags		: fpu vme de pse tsc msr pae mce cx8 vmx
"""
    cpu = parse_proc_cpuinfo(mock_cpuinfo)
    assert "Intel(R) Core(TM) i7-1370P" in cpu.model_name
    assert cpu.cores >= 1
    assert cpu.max_mhz == 2200.0
    assert cpu.l3_cache == "24576 KB"
    assert cpu.virtualization == "VT-x/AMD-V"


def test_parse_lsblk_json():
    disks = parse_lsblk_json(MOCK_LSBLK_JSON)
    assert len(disks) == 1
    d0 = disks[0]
    assert d0.name == "nvme0n1"
    assert d0.transport == "nvme"
    assert d0.is_rotational is False
    assert d0.is_ssd is True
    assert "SAMSUNG" in (d0.model or "")
    assert len(d0.children) == 3
    assert d0.children[0].mountpoint == "/boot/efi"
    assert d0.children[2].mountpoint == "/"


def test_parse_free_bytes():
    mem = parse_free_bytes(MOCK_FREE_BYTES)
    assert mem.total_bytes == 16155930624
    assert mem.used_bytes == 4210450432
    assert mem.available_bytes == 11417001984
    assert mem.swap_total_bytes == 8589934592


def test_parse_proc_meminfo():
    mem = parse_proc_meminfo(MOCK_PROC_MEMINFO)
    assert mem.total_bytes == 15777276 * 1024
    assert mem.free_bytes == 5981024 * 1024
    assert mem.available_bytes == 11149416 * 1024
    assert mem.swap_total_bytes == 8388608 * 1024


def test_parse_lspci():
    gpus = parse_lspci(MOCK_LSPCI)
    assert len(gpus) == 1
    gpu = gpus[0]
    assert gpu.pci_slot == "04:00.0"
    assert "VGA compatible controller" in gpu.device_class
    assert "Cezanne" in gpu.device_name
    assert gpu.is_vga is True


def test_parse_dmidecode_system():
    sys_info = parse_dmidecode_system(MOCK_DMIDECODE_SYSTEM)
    assert sys_info.manufacturer == "LENOVO"
    assert sys_info.product_name == "20W0005HUS"
    assert "ThinkPad T14" in (sys_info.product_version or "")


def test_parse_sysfs_dmi():
    sys_info = parse_sysfs_dmi(MOCK_SYS_DMI_ID)
    assert sys_info.manufacturer == "LENOVO"
    assert sys_info.product_name == "20W0005HUS"
    assert sys_info.chassis_type == "Notebook"
    assert sys_info.bios_version == "N34ET52W (1.52 )"


def test_parse_os_release():
    os_info = parse_os_release(MOCK_OS_RELEASE)
    assert os_info["NAME"] == "Ubuntu"
    assert os_info["VERSION_ID"] == "24.04"
