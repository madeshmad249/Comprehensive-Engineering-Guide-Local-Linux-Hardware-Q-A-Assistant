"""Parser for block storage devices from lsblk JSON."""
import json
from typing import List, Dict, Any
from ..models.hardware import BlockDevice, BlockPartition


def _format_bytes(num_bytes: int) -> str:
    """Formats byte counts into standard human-readable units."""
    if num_bytes <= 0:
        return "0 B"
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}" if unit != "B" else f"{num_bytes} B"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PiB"


def parse_lsblk_json(stdout: str) -> List[BlockDevice]:
    """Parses output of `lsblk -J -o NAME,SIZE,TYPE,MOUNTPOINT,MODEL,ROTA,TRAN`."""
    data = json.loads(stdout)
    devices: List[BlockDevice] = []

    for item in data.get("blockdevices", []):
        size_raw = item.get("size", "0")
        try:
            size_bytes = int(size_raw)
            size_human = _format_bytes(size_bytes)
        except ValueError:
            size_bytes = 0
            size_human = str(size_raw)

        rota = item.get("rota", False)
        # ROTA can be boolean or int or string "0"/"1"
        is_rotational = rota is True or rota == 1 or rota == "1" or rota == "true"
        tran = item.get("tran")
        is_ssd = not is_rotational or (tran == "nvme")

        # Parse partitions
        children: List[BlockPartition] = []
        for child in item.get("children", []):
            c_size_raw = child.get("size", "0")
            try:
                c_bytes = int(c_size_raw)
                c_human = _format_bytes(c_bytes)
            except ValueError:
                c_bytes = 0
                c_human = str(c_size_raw)

            children.append(
                BlockPartition(
                    name=child.get("name", ""),
                    size_human=c_human,
                    size_bytes=c_bytes,
                    type=child.get("type", "part"),
                    mountpoint=child.get("mountpoint"),
                )
            )

        devices.append(
            BlockDevice(
                name=item.get("name", ""),
                size_human=size_human,
                size_bytes=size_bytes,
                type=item.get("type", "disk"),
                model=item.get("model"),
                is_rotational=is_rotational,
                transport=tran,
                is_ssd=is_ssd,
                children=children,
            )
        )

    return devices
