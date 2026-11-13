"""Fixtures package for hardware simulation."""
from .mock_data import (
    MOCK_DMIDECODE_MEMORY,
    MOCK_DMIDECODE_SYSTEM,
    MOCK_LSCPU,
    MOCK_LSBLK_JSON,
    MOCK_FREE_BYTES,
    MOCK_PROC_MEMINFO,
    MOCK_LSPCI,
    MOCK_SYS_DMI_ID,
    MOCK_OS_RELEASE,
)

__all__ = [
    "MOCK_DMIDECODE_MEMORY",
    "MOCK_DMIDECODE_SYSTEM",
    "MOCK_LSCPU",
    "MOCK_LSBLK_JSON",
    "MOCK_FREE_BYTES",
    "MOCK_PROC_MEMINFO",
    "MOCK_LSPCI",
    "MOCK_SYS_DMI_ID",
    "MOCK_OS_RELEASE",
]
