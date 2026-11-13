"""Capability and binary discovery service to detect available Linux utilities and privilege level."""
import os
import shutil
import subprocess
import sys
from typing import Dict, Any, List
from pydantic import BaseModel, Field


class SystemCapabilities(BaseModel):
    is_linux: bool = Field(..., description="True if host operating system is Linux")
    has_lscpu: bool = Field(default=False)
    has_lsblk: bool = Field(default=False)
    has_free: bool = Field(default=False)
    has_lspci: bool = Field(default=False)
    has_dmidecode: bool = Field(default=False)
    has_sudo_dmidecode: bool = Field(default=False, description="True if dmidecode can run via sudo without password")
    has_proc_meminfo: bool = Field(default=False)
    has_proc_cpuinfo: bool = Field(default=False)
    has_sys_dmi: bool = Field(default=False)
    available_tools: List[str] = Field(default_factory=list)


def discover_system_capabilities(mock: bool = False) -> SystemCapabilities:
    """Probes the host OS for command binaries, filesystems, and sudo permissions."""
    if mock:
        return SystemCapabilities(
            is_linux=True,
            has_lscpu=True,
            has_lsblk=True,
            has_free=True,
            has_lspci=True,
            has_dmidecode=True,
            has_sudo_dmidecode=True,
            has_proc_meminfo=True,
            has_proc_cpuinfo=True,
            has_sys_dmi=True,
            available_tools=[
                "get_cpu_info",
                "get_memory_topology",
                "get_memory_summary",
                "get_block_devices",
                "get_gpu_info",
                "get_system_info",
            ],
        )

    is_linux = sys.platform.startswith("linux")
    has_lscpu = shutil.which("lscpu") is not None
    has_lsblk = shutil.which("lsblk") is not None
    has_free = shutil.which("free") is not None
    has_lspci = shutil.which("lspci") is not None
    has_dmidecode = shutil.which("dmidecode") is not None or os.path.exists("/usr/sbin/dmidecode")

    # Check non-root /proc and /sys files
    has_proc_meminfo = os.path.exists("/proc/meminfo")
    has_proc_cpuinfo = os.path.exists("/proc/cpuinfo")
    has_sys_dmi = os.path.exists("/sys/class/dmi/id")

    # Test sudo passwordless execution for dmidecode
    has_sudo_dmidecode = False
    if is_linux and has_dmidecode:
        try:
            # -n flag ensures sudo fails immediately instead of prompting for a password in terminal
            res = subprocess.run(
                ["sudo", "-n", "/usr/sbin/dmidecode", "-t", "memory"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            has_sudo_dmidecode = (res.returncode == 0)
        except Exception:
            has_sudo_dmidecode = False

    available_tools: List[str] = []
    if has_lscpu or has_proc_cpuinfo:
        available_tools.append("get_cpu_info")
    if has_lsblk:
        available_tools.append("get_block_devices")
    if has_free or has_proc_meminfo:
        available_tools.append("get_memory_summary")
    if has_sudo_dmidecode or has_proc_meminfo:
        available_tools.append("get_memory_topology")
    if has_lspci:
        available_tools.append("get_gpu_info")
    if has_sudo_dmidecode or has_sys_dmi:
        available_tools.append("get_system_info")

    return SystemCapabilities(
        is_linux=is_linux,
        has_lscpu=has_lscpu,
        has_lsblk=has_lsblk,
        has_free=has_free,
        has_lspci=has_lspci,
        has_dmidecode=has_dmidecode,
        has_sudo_dmidecode=has_sudo_dmidecode,
        has_proc_meminfo=has_proc_meminfo,
        has_proc_cpuinfo=has_proc_cpuinfo,
        has_sys_dmi=has_sys_dmi,
        available_tools=available_tools,
    )
