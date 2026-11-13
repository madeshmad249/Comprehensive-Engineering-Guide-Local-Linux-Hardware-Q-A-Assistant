"""Tool schemas and parameter specifications for LLM function calling."""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    name: str = Field(..., description="Tool identifier matching internal allow-list")
    description: str = Field(..., description="Function description instructing LLM when to invoke")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema of parameters")


class ToolCallRequest(BaseModel):
    tool_name: str = Field(..., description="Target tool identifier")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Validated argument map")


class ToolCallResponse(BaseModel):
    tool_name: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    fallback_used: bool = False
    source: str = "native"  # "native", "fallback", or "mock"


# Catalog of available LLM tools
SYSTEM_TOOLS: List[ToolDefinition] = [
    ToolDefinition(
        name="get_memory_topology",
        description="Retrieves physical RAM details including installed capacity, total slots, available empty slots, speed, and maximum supported motherboard capacity from DMI/SMBIOS.",
        parameters={
            "type": "object",
            "properties": {
                "include_empty_slots": {
                    "type": "boolean",
                    "description": "Set to true to return details on unused memory slots."
                }
            },
            "required": []
        }
    ),
    ToolDefinition(
        name="get_memory_summary",
        description="Retrieves system memory consumption, total RAM, free RAM, available memory, and swap space via /proc/meminfo or free.",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
    ToolDefinition(
        name="get_cpu_info",
        description="Retrieves processor model, core count, thread count, architecture, max frequencies, cache sizes, and virtualization capabilities.",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
    ToolDefinition(
        name="get_block_devices",
        description="Retrieves storage drives, partition tables, disk sizes, mountpoints, drive models, and detects whether drives are SSD/NVMe or rotational HDDs.",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
    ToolDefinition(
        name="get_gpu_info",
        description="Retrieves installed graphic controllers, PCI video cards, AMD/NVIDIA/Intel GPUs, and display devices.",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
    ToolDefinition(
        name="get_system_info",
        description="Retrieves laptop/desktop make and model, chassis type, BIOS firmware version, release date, and Linux OS distribution.",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    )
]
