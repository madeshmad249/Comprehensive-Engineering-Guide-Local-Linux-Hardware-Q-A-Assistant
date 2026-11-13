"""Parser for host system metadata, motherboard/BIOS details, and OS release."""
import re
from typing import Dict, Optional
from ..models.hardware import SystemInfo


CHASSIS_TYPES = {
    "1": "Other",
    "2": "Unknown",
    "3": "Desktop",
    "8": "Portable",
    "9": "Laptop",
    "10": "Notebook",
    "11": "Hand Held",
    "14": "Sub Notebook",
    "30": "Tablet",
    "31": "Convertible",
    "32": "Detachable",
}


def parse_dmidecode_system(stdout: str) -> SystemInfo:
    """Parses `dmidecode -t system` into a SystemInfo model."""
    # Find System Information block (Handle 0x..., DMI type 1)
    target_block = stdout
    if "System Information" in stdout:
        blocks = re.split(r"(?:Handle\s+0x[0-9a-fA-F]+,\s+DMI\s+type\s+\d+)", stdout)
        for b in blocks:
            if "System Information" in b:
                target_block = b
                break

    props = {}
    for line in target_block.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            props[k.strip()] = v.strip()

    return SystemInfo(
        manufacturer=props.get("Manufacturer"),
        product_name=props.get("Product Name"),
        product_version=props.get("Version"),
        chassis_type=props.get("Family") or props.get("Chassis"),
        bios_version=None,
        bios_date=None,
        os_name=None,
        os_version=None,
        kernel_version=None,
    )


def parse_sysfs_dmi(dmi_dict: Dict[str, str]) -> SystemInfo:
    """Parses key-value data directly read from unprivileged /sys/class/dmi/id/*."""
    chassis_code = dmi_dict.get("chassis_type", "").strip()
    chassis_name = CHASSIS_TYPES.get(chassis_code, f"Type {chassis_code}" if chassis_code else "Notebook")

    return SystemInfo(
        manufacturer=dmi_dict.get("sys_vendor", "").strip() or None,
        product_name=dmi_dict.get("product_name", "").strip() or None,
        product_version=dmi_dict.get("product_version", "").strip() or None,
        chassis_type=chassis_name,
        bios_version=dmi_dict.get("bios_version", "").strip() or None,
        bios_date=dmi_dict.get("bios_date", "").strip() or None,
        os_name=None,
        os_version=None,
        kernel_version=None,
    )


def parse_os_release(stdout: str) -> Dict[str, str]:
    """Parses /etc/os-release key-value pairs."""
    info = {}
    for line in stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            v = v.strip("\"'")
            info[k.strip()] = v
    return info
