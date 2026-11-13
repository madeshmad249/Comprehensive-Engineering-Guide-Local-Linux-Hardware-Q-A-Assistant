"""Parsers for RAM, physical memory topology, and swap memory."""
import re
from typing import List, Optional, Tuple
from ..models.hardware import MemorySlot, MemoryTopology, MemorySummary


def _parse_size_bytes(size_str: str) -> Tuple[int, str]:
    """Converts strings like '16 GB', '8192 MB', '1024 kB' into bytes and cleaned string."""
    clean = size_str.strip()
    match = re.match(r"^(\d+(?:\.\d+)?)\s*([KMGTP]B|Bytes|B|KiB|MiB|GiB|TiB)?$", clean, re.IGNORECASE)
    if not match:
        return 0, clean

    value = float(match.group(1))
    unit = (match.group(2) or "B").upper()

    multipliers = {
        "B": 1,
        "BYTES": 1,
        "KB": 1024,
        "KIB": 1024,
        "MB": 1024**2,
        "MIB": 1024**2,
        "GB": 1024**3,
        "GIB": 1024**3,
        "TB": 1024**4,
        "TIB": 1024**4,
    }
    multiplier = multipliers.get(unit, 1)
    return int(value * multiplier), clean


def parse_dmidecode_memory(stdout: str, include_empty: bool = True) -> MemoryTopology:
    """Parses `dmidecode -t memory` output into a validated MemoryTopology model."""
    # 1. Parse Type 16 (Physical Memory Array)
    max_cap_match = re.search(r"Maximum Capacity:\s*(.+)", stdout)
    max_cap_human = max_cap_match.group(1).strip() if max_cap_match else "Unknown"
    max_cap_bytes, _ = _parse_size_bytes(max_cap_human)

    # 2. Parse Type 17 (Memory Device) blocks
    # Blocks start with "Handle 0x..., DMI type 17"
    raw_devices = re.split(r"(?:Handle\s+0x[0-9a-fA-F]+,\s+DMI\s+type\s+17)", stdout)
    
    slots: List[MemorySlot] = []
    for block in raw_devices[1:]:
        lines = block.splitlines()
        props = {}
        for line in lines:
            if ":" in line:
                k, v = line.split(":", 1)
                props[k.strip()] = v.strip()

        size_raw = props.get("Size", "Unknown")
        is_empty = ("No Module Installed" in size_raw) or (size_raw == "Unknown") or (size_raw == "0 B")

        size_bytes, size_human = (0, "No Module Installed") if is_empty else _parse_size_bytes(size_raw)

        locator = props.get("Locator", f"Slot {len(slots)}")
        bank = props.get("Bank Locator")
        form_factor = props.get("Form Factor")
        mem_type = props.get("Type")
        speed = props.get("Speed")
        manufacturer = props.get("Manufacturer")
        part_number = props.get("Part Number")

        slot = MemorySlot(
            locator=locator,
            bank_locator=bank if bank != "None" else None,
            size_human=size_human,
            size_bytes=size_bytes,
            form_factor=form_factor if form_factor != "Unknown" else None,
            type=mem_type if mem_type != "Unknown" else None,
            speed=speed if speed != "Unknown" else None,
            manufacturer=manufacturer if manufacturer not in ("Unknown", "Not Specified") else None,
            part_number=part_number if part_number not in ("Unknown", "Not Specified") else None,
            is_empty=is_empty,
        )
        slots.append(slot)

    # Calculate totals
    total_slots = len(slots)
    used_slots = sum(1 for s in slots if not s.is_empty)
    free_slots = total_slots - used_slots

    installed_bytes = sum(s.size_bytes for s in slots if not s.is_empty)
    installed_gb = installed_bytes / (1024**3)

    # Determine upgradability: free slots exist, or slots are non-soldered (SODIMM/DIMM)
    has_removable_form_factor = any(s.form_factor in ("SODIMM", "DIMM") for s in slots)
    is_upgradeable = (free_slots > 0) or has_removable_form_factor

    speed_info = ""
    type_info = ""
    populated = [s for s in slots if not s.is_empty]
    if populated:
        if populated[0].speed:
            speed_info = f" @ {populated[0].speed}"
        if populated[0].type:
            type_info = f"{populated[0].type}"

    summary = (
        f"Installed: {installed_gb:.0f} GB across {used_slots} of {total_slots} slots "
        f"({type_info}{speed_info}). "
        f"Maximum supported motherboard capacity: {max_cap_human}. "
        f"Available free slots: {free_slots}."
    )

    reported_modules = slots if include_empty else populated

    return MemoryTopology(
        maximum_capacity_human=max_cap_human,
        maximum_capacity_bytes=max_cap_bytes if max_cap_bytes > 0 else None,
        total_slots=total_slots,
        used_slots=used_slots,
        free_slots=free_slots,
        is_upgradeable=is_upgradeable,
        installed_modules=reported_modules,
        summary=summary,
    )


def parse_free_bytes(stdout: str) -> MemorySummary:
    """Parses `free -b` output into a validated MemorySummary model."""
    lines = stdout.strip().splitlines()
    mem_total = 0
    mem_used = 0
    mem_free = 0
    mem_avail = 0
    swap_total = 0
    swap_used = 0
    swap_free = 0

    for line in lines:
        parts = line.split()
        if not parts:
            continue
        if parts[0].startswith("Mem:"):
            # Mem: total used free shared buff/cache available
            mem_total = int(parts[1])
            mem_used = int(parts[2])
            mem_free = int(parts[3])
            mem_avail = int(parts[6]) if len(parts) > 6 else (mem_free + int(parts[5]))
        elif parts[0].startswith("Swap:"):
            # Swap: total used free
            swap_total = int(parts[1])
            swap_used = int(parts[2])
            swap_free = int(parts[3])

    return MemorySummary(
        total_bytes=mem_total,
        used_bytes=mem_used,
        free_bytes=mem_free,
        available_bytes=mem_avail,
        swap_total_bytes=swap_total,
        swap_used_bytes=swap_used,
        swap_free_bytes=swap_free,
    )


def parse_proc_meminfo(stdout: str) -> MemorySummary:
    """Parses /proc/meminfo when `free` or root dmidecode is unavailable."""
    kv = {}
    for line in stdout.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            # Remove " kB" and convert to integer bytes
            val_clean = v.strip().replace(" kB", "")
            try:
                kv[k.strip()] = int(val_clean) * 1024
            except ValueError:
                pass

    total = kv.get("MemTotal", 0)
    free = kv.get("MemFree", 0)
    avail = kv.get("MemAvailable", free)
    used = total - avail if total >= avail else 0

    swap_total = kv.get("SwapTotal", 0)
    swap_free = kv.get("SwapFree", 0)
    swap_used = swap_total - swap_free if swap_total >= swap_free else 0

    return MemorySummary(
        total_bytes=total,
        used_bytes=used,
        free_bytes=free,
        available_bytes=avail,
        swap_total_bytes=swap_total,
        swap_used_bytes=swap_used,
        swap_free_bytes=swap_free,
    )
