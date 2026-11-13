"""Secure tool execution engine with privilege fallback handling and mock simulation runner."""
import os
import subprocess
from typing import Dict, Any, Optional

from .security import get_command_vector, SecurityValidationError
from ..models.tools import ToolCallResponse
from ..parsers.cpu import parse_lscpu, parse_proc_cpuinfo
from ..parsers.memory import parse_dmidecode_memory, parse_free_bytes, parse_proc_meminfo
from ..parsers.disk import parse_lsblk_json
from ..parsers.pci import parse_lspci
from ..parsers.system import parse_dmidecode_system, parse_sysfs_dmi
from ..fixtures.mock_data import (
    MOCK_DMIDECODE_MEMORY,
    MOCK_LSCPU,
    MOCK_LSBLK_JSON,
    MOCK_FREE_BYTES,
    MOCK_LSPCI,
    MOCK_DMIDECODE_SYSTEM,
    MOCK_SYS_DMI_ID,
)


class SystemExecutionEngine:
    """Executes validated system tools, handling privilege elevation and unprivileged fallbacks."""

    def __init__(self, mock_mode: bool = False, timeout_seconds: int = 5):
        self.mock_mode = mock_mode
        self.timeout_seconds = timeout_seconds

    def execute_tool(self, tool_name: str, kwargs: Optional[Dict[str, Any]] = None) -> ToolCallResponse:
        """Executes the requested tool, returning structured data or fallbacks."""
        kwargs = kwargs or {}

        # 1. Mock simulation mode
        if self.mock_mode:
            return self._execute_mock(tool_name, kwargs)

        # 2. Validate against security allow-list and parameters
        try:
            cmd = get_command_vector(tool_name, kwargs)
        except SecurityValidationError as e:
            return ToolCallResponse(
                tool_name=tool_name,
                success=False,
                error=str(e),
                source="security_block",
            )

        # 3. Direct execution via execve (shell=False)
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout_seconds,
            )
            data = self._parse_output(tool_name, res.stdout, kwargs)
            return ToolCallResponse(
                tool_name=tool_name,
                success=True,
                data=data,
                fallback_used=False,
                source="native",
            )
        except subprocess.TimeoutExpired:
            return ToolCallResponse(
                tool_name=tool_name,
                success=False,
                error=f"Command '{cmd[0]}' timed out after {self.timeout_seconds} seconds.",
                source="timeout",
            )
        except (subprocess.CalledProcessError, FileNotFoundError, PermissionError) as e:
            # Attempt unprivileged fallback
            return self._execute_fallback(tool_name, str(e), kwargs)

    def _execute_mock(self, tool_name: str, kwargs: Dict[str, Any]) -> ToolCallResponse:
        """Returns verified mock data representing real Linux hardware."""
        include_empty = kwargs.get("include_empty_slots", True)

        if tool_name == "get_memory_topology":
            topology = parse_dmidecode_memory(MOCK_DMIDECODE_MEMORY, include_empty=include_empty)
            return ToolCallResponse(tool_name=tool_name, success=True, data=topology.model_dump(), source="mock")

        elif tool_name == "get_cpu_info":
            cpu = parse_lscpu(MOCK_LSCPU)
            return ToolCallResponse(tool_name=tool_name, success=True, data=cpu.model_dump(), source="mock")

        elif tool_name == "get_memory_summary":
            mem = parse_free_bytes(MOCK_FREE_BYTES)
            return ToolCallResponse(tool_name=tool_name, success=True, data=mem.model_dump(), source="mock")

        elif tool_name == "get_block_devices":
            disks = parse_lsblk_json(MOCK_LSBLK_JSON)
            return ToolCallResponse(tool_name=tool_name, success=True, data={"devices": [d.model_dump() for d in disks]}, source="mock")

        elif tool_name == "get_gpu_info":
            gpus = parse_lspci(MOCK_LSPCI)
            return ToolCallResponse(tool_name=tool_name, success=True, data={"gpus": [g.model_dump() for g in gpus]}, source="mock")

        elif tool_name == "get_system_info":
            sys_info = parse_dmidecode_system(MOCK_DMIDECODE_SYSTEM)
            return ToolCallResponse(tool_name=tool_name, success=True, data=sys_info.model_dump(), source="mock")

        return ToolCallResponse(tool_name=tool_name, success=False, error=f"Unknown mock tool: {tool_name}", source="mock")

    def _parse_output(self, tool_name: str, stdout: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes stdout into Pydantic models and dictionaries."""
        include_empty = kwargs.get("include_empty_slots", True)

        if tool_name == "get_cpu_info":
            return parse_lscpu(stdout).model_dump()

        elif tool_name == "get_memory_topology":
            return parse_dmidecode_memory(stdout, include_empty=include_empty).model_dump()

        elif tool_name == "get_memory_summary":
            return parse_free_bytes(stdout).model_dump()

        elif tool_name == "get_block_devices":
            disks = parse_lsblk_json(stdout)
            return {"devices": [d.model_dump() for d in disks]}

        elif tool_name == "get_gpu_info":
            gpus = parse_lspci(stdout)
            return {"gpus": [g.model_dump() for g in gpus]}

        elif tool_name == "get_system_info":
            return parse_dmidecode_system(stdout).model_dump()

        return {"raw": stdout}

    def _execute_fallback(self, tool_name: str, orig_error: str, kwargs: Dict[str, Any]) -> ToolCallResponse:
        """Executes unprivileged Strategy C fallback when root binaries are blocked or missing."""
        try:
            if tool_name == "get_memory_topology" or tool_name == "get_memory_summary":
                if os.path.exists("/proc/meminfo"):
                    with open("/proc/meminfo", "r", encoding="utf-8") as f:
                        content = f.read()
                    mem = parse_proc_meminfo(content)
                    return ToolCallResponse(
                        tool_name=tool_name,
                        success=True,
                        data={
                            **mem.model_dump(),
                            "notice": "Retrieved from unprivileged /proc/meminfo. Maximum motherboard physical slot capacity requires root dmidecode.",
                        },
                        fallback_used=True,
                        source="fallback_proc_meminfo",
                    )

            elif tool_name == "get_cpu_info":
                if os.path.exists("/proc/cpuinfo"):
                    with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
                        content = f.read()
                    cpu = parse_proc_cpuinfo(content)
                    return ToolCallResponse(
                        tool_name=tool_name,
                        success=True,
                        data=cpu.model_dump(),
                        fallback_used=True,
                        source="fallback_proc_cpuinfo",
                    )

            elif tool_name == "get_system_info":
                if os.path.exists("/sys/class/dmi/id"):
                    dmi_map = {}
                    for field in ["sys_vendor", "product_name", "product_version", "bios_version", "bios_date", "chassis_type"]:
                        path = f"/sys/class/dmi/id/{field}"
                        if os.path.exists(path):
                            try:
                                with open(path, "r", encoding="utf-8") as f:
                                    dmi_map[field] = f.read()
                            except Exception:
                                pass
                    sys_info = parse_sysfs_dmi(dmi_map)
                    return ToolCallResponse(
                        tool_name=tool_name,
                        success=True,
                        data=sys_info.model_dump(),
                        fallback_used=True,
                        source="fallback_sysfs_dmi",
                    )
        except Exception as fallback_err:
            return ToolCallResponse(
                tool_name=tool_name,
                success=False,
                error=f"Primary tool failed ({orig_error}) and fallback failed ({str(fallback_err)})",
                source="error",
            )

        return ToolCallResponse(
            tool_name=tool_name,
            success=False,
            error=f"Execution failed: {orig_error}. No fallback available for '{tool_name}'.",
            source="error",
        )
