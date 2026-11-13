"""Parsers for CPU information from lscpu and /proc/cpuinfo."""
import re
from typing import Dict, Any, List
from ..models.hardware import CPUInfo


def parse_lscpu(stdout: str) -> CPUInfo:
    """Parses raw stdout from `lscpu` into a validated CPUInfo model."""
    kv: Dict[str, str] = {}
    for line in stdout.splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            kv[key.strip()] = val.strip()

    model_name = kv.get("Model name") or kv.get("Model Name") or "Unknown CPU"
    architecture = kv.get("Architecture", "unknown")
    
    # Calculate cores & threads
    cores_per_socket = int(kv.get("Core(s) per socket", 1))
    sockets = int(kv.get("Socket(s)", 1))
    threads_per_core = int(kv.get("Thread(s) per core", 1))
    total_cores = int(kv.get("CPU(s)", cores_per_socket * sockets))
    total_threads = cores_per_socket * sockets * threads_per_core

    # Parse frequencies
    max_mhz = None
    min_mhz = None
    if "CPU max MHz" in kv:
        try:
            max_mhz = float(kv["CPU max MHz"])
        except ValueError:
            pass
    if "CPU min MHz" in kv:
        try:
            min_mhz = float(kv["CPU min MHz"])
        except ValueError:
            pass

    # Parse flags
    flags_raw = kv.get("Flags", "")
    flags = [f for f in flags_raw.split() if f]

    return CPUInfo(
        model_name=model_name,
        architecture=architecture,
        cores=total_cores,
        threads=total_threads,
        sockets=sockets,
        max_mhz=max_mhz,
        min_mhz=min_mhz,
        l1d_cache=kv.get("L1d") or kv.get("L1d cache"),
        l1i_cache=kv.get("L1i") or kv.get("L1i cache"),
        l2_cache=kv.get("L2") or kv.get("L2 cache"),
        l3_cache=kv.get("L3") or kv.get("L3 cache"),
        virtualization=kv.get("Virtualization"),
        flags=flags,
    )


def parse_proc_cpuinfo(stdout: str) -> CPUInfo:
    """Fallback parser for /proc/cpuinfo when lscpu is unavailable."""
    processors = 0
    model_name = "Unknown CPU"
    flags: List[str] = []
    cache_size = None
    cpu_mhz = None

    for line in stdout.splitlines():
        if not line.strip():
            continue
        if ":" in line:
            key, val = [x.strip() for x in line.split(":", 1)]
            if key == "processor":
                processors += 1
            elif key in ("model name", "model_name") and model_name == "Unknown CPU":
                model_name = val
            elif key == "flags" and not flags:
                flags = val.split()
            elif key == "cache size" and cache_size is None:
                cache_size = val
            elif key == "cpu MHz" and cpu_mhz is None:
                try:
                    cpu_mhz = float(val)
                except ValueError:
                    pass

    return CPUInfo(
        model_name=model_name,
        architecture="x86_64",
        cores=max(1, processors),
        threads=max(1, processors),
        sockets=1,
        max_mhz=cpu_mhz,
        min_mhz=None,
        l1d_cache=None,
        l1i_cache=None,
        l2_cache=None,
        l3_cache=cache_size,
        virtualization="VT-x/AMD-V" if ("vmx" in flags or "svm" in flags) else None,
        flags=flags,
    )
