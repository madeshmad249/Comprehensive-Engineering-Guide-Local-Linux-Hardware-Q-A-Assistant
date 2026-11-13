"""Pydantic data models for normalized Linux hardware specifications."""
from typing import List, Optional
from pydantic import BaseModel, Field


class CPUInfo(BaseModel):
    model_name: str = Field(..., description="CPU model brand and naming")
    architecture: str = Field(..., description="Instruction set architecture, e.g. x86_64, aarch64")
    cores: int = Field(..., description="Total physical CPU cores")
    threads: int = Field(..., description="Total execution threads")
    sockets: int = Field(default=1, description="CPU physical socket count")
    max_mhz: Optional[float] = Field(default=None, description="Maximum CPU frequency in MHz")
    min_mhz: Optional[float] = Field(default=None, description="Minimum CPU frequency in MHz")
    l1d_cache: Optional[str] = Field(default=None, description="L1 Data cache size")
    l1i_cache: Optional[str] = Field(default=None, description="L1 Instruction cache size")
    l2_cache: Optional[str] = Field(default=None, description="L2 cache size")
    l3_cache: Optional[str] = Field(default=None, description="L3 cache size")
    virtualization: Optional[str] = Field(default=None, description="Hardware virtualization technology (VT-x / AMD-V)")
    flags: List[str] = Field(default_factory=list, description="Supported CPU instruction flags")


class MemorySlot(BaseModel):
    locator: str = Field(..., description="Slot locator, e.g. ChannelA-DIMM0 or DIMM 0")
    bank_locator: Optional[str] = Field(default=None, description="Bank location")
    size_human: str = Field(..., description="Readable size, e.g. '16 GB' or 'No Module Installed'")
    size_bytes: int = Field(default=0, description="Capacity in bytes")
    form_factor: Optional[str] = Field(default=None, description="SODIMM, DIMM, etc.")
    type: Optional[str] = Field(default=None, description="DDR4, DDR5, LPDDR5, etc.")
    speed: Optional[str] = Field(default=None, description="Memory speed, e.g. 3200 MT/s")
    manufacturer: Optional[str] = Field(default=None, description="Module manufacturer")
    part_number: Optional[str] = Field(default=None, description="Manufacturer part number")
    is_empty: bool = Field(default=False, description="True if no physical module is inserted")


class MemoryTopology(BaseModel):
    maximum_capacity_human: str = Field(..., description="Maximum physical RAM supported by motherboard/BIOS")
    maximum_capacity_bytes: Optional[int] = Field(default=None, description="Maximum RAM in bytes")
    total_slots: int = Field(..., description="Total physical memory sockets on board")
    used_slots: int = Field(..., description="Number of populated slots")
    free_slots: int = Field(..., description="Number of vacant slots available for upgrade")
    is_upgradeable: bool = Field(..., description="True if free slots exist or modules are swappable SODIMMs")
    installed_modules: List[MemorySlot] = Field(default_factory=list, description="Details for each physical slot")
    summary: str = Field(..., description="Human-readable upgrade and topology summary")


class MemorySummary(BaseModel):
    total_bytes: int = Field(..., description="Total system memory in bytes")
    used_bytes: int = Field(..., description="Active/used memory in bytes")
    free_bytes: int = Field(..., description="Unused memory in bytes")
    available_bytes: int = Field(..., description="Memory available for starting applications without swapping")
    swap_total_bytes: int = Field(default=0, description="Total swap space in bytes")
    swap_used_bytes: int = Field(default=0, description="Used swap space in bytes")
    swap_free_bytes: int = Field(default=0, description="Free swap space in bytes")


class BlockPartition(BaseModel):
    name: str = Field(..., description="Device node name, e.g. nvme0n1p1")
    size_human: str = Field(..., description="Formatted size string")
    size_bytes: int = Field(..., description="Partition size in bytes")
    type: str = Field(..., description="Device type, e.g. part")
    mountpoint: Optional[str] = Field(default=None, description="Mount location, e.g. / or /home")


class BlockDevice(BaseModel):
    name: str = Field(..., description="Device name, e.g. nvme0n1 or sda")
    size_human: str = Field(..., description="Human-readable size string")
    size_bytes: int = Field(..., description="Total disk size in bytes")
    type: str = Field(..., description="Block type: disk, loop, rom")
    model: Optional[str] = Field(default=None, description="Disk drive model name")
    is_rotational: bool = Field(default=False, description="True if HDD, False if SSD/NVMe")
    transport: Optional[str] = Field(default=None, description="Bus transport: nvme, sata, usb")
    is_ssd: bool = Field(default=True, description="True if solid state drive")
    children: List[BlockPartition] = Field(default_factory=list, description="Child partitions")


class GPUDevice(BaseModel):
    pci_slot: str = Field(..., description="PCI address, e.g. 04:00.0")
    device_class: str = Field(..., description="PCI class name")
    vendor: str = Field(..., description="Vendor name, e.g. AMD, Intel, NVIDIA")
    device_name: str = Field(..., description="Model string")
    subsystem: Optional[str] = Field(default=None, description="Subsystem manufacturer/device")
    is_vga: bool = Field(default=True, description="True if primary VGA display controller")


class SystemInfo(BaseModel):
    manufacturer: Optional[str] = Field(default=None, description="System manufacturer, e.g. LENOVO, Dell")
    product_name: Optional[str] = Field(default=None, description="Product model, e.g. ThinkPad T14 Gen 2")
    product_version: Optional[str] = Field(default=None, description="Hardware release version")
    chassis_type: Optional[str] = Field(default=None, description="Form factor: Notebook, Desktop, Laptop")
    bios_version: Optional[str] = Field(default=None, description="BIOS firmware version")
    bios_date: Optional[str] = Field(default=None, description="BIOS release date")
    os_name: Optional[str] = Field(default=None, description="Linux distribution name")
    os_version: Optional[str] = Field(default=None, description="Distribution version")
    kernel_version: Optional[str] = Field(default=None, description="Linux kernel release")
