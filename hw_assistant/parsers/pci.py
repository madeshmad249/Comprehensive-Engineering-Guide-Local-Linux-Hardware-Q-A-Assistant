"""Parser for PCI hardware devices (specifically GPUs and display controllers)."""
import re
from typing import List
from ..models.hardware import GPUDevice


def parse_lspci(stdout: str) -> List[GPUDevice]:
    """Parses lspci output (standard, -vmm, or -nnmm) to extract graphics cards and GPUs."""
    gpus: List[GPUDevice] = []

    # Check if format is lspci -vmm or -mm
    if "Slot:\t" in stdout:
        blocks = stdout.strip().split("\n\n")
        for block in blocks:
            props = {}
            for line in block.splitlines():
                if ":\t" in line:
                    k, v = line.split(":\t", 1)
                    props[k.strip()] = v.strip()
                elif ":" in line:
                    k, v = line.split(":", 1)
                    props[k.strip()] = v.strip()

            cls = props.get("Class", "")
            # Filter for display and 3D controllers (VGA: 0300, 3D: 0302, Display: 0380)
            if any(term in cls.lower() for term in ["vga", "3d", "display", "0300", "0302"]):
                slot = props.get("Slot", "00:00.0")
                vendor = props.get("Vendor", "Unknown Vendor")
                device = props.get("Device", "Unknown Device")
                subsystem = props.get("SDevice") or props.get("SVendor")

                gpus.append(
                    GPUDevice(
                        pci_slot=slot,
                        device_class=cls,
                        vendor=vendor,
                        device_name=device,
                        subsystem=subsystem,
                        is_vga="vga" in cls.lower() or "0300" in cls,
                    )
                )
    else:
        # Standard one-line-per-device format:
        # e.g.: 04:00.0 VGA compatible controller: Advanced Micro Devices, Inc. [AMD/ATI] Cezanne [Radeon Vega Series / Radeon Vega Mobile Series] (rev c1)
        for line in stdout.splitlines():
            line_clean = line.strip()
            if not line_clean:
                continue
            if any(term in line_clean.lower() for term in ["vga compatible controller", "3d controller", "display controller"]):
                parts = line_clean.split(" ", 1)
                slot = parts[0]
                rest = parts[1] if len(parts) > 1 else ""

                # Class and device split by colon
                if ":" in rest:
                    dev_class, full_name = rest.split(":", 1)
                else:
                    dev_class, full_name = "Display Controller", rest

                full_name = full_name.strip()
                vendor = "Unknown"
                if "amd" in full_name.lower() or "ati" in full_name.lower():
                    vendor = "AMD / ATI"
                elif "nvidia" in full_name.lower():
                    vendor = "NVIDIA Corporation"
                elif "intel" in full_name.lower():
                    vendor = "Intel Corporation"

                gpus.append(
                    GPUDevice(
                        pci_slot=slot,
                        device_class=dev_class.strip(),
                        vendor=vendor,
                        device_name=full_name,
                        subsystem=None,
                        is_vga="vga" in dev_class.lower(),
                    )
                )

    return gpus
