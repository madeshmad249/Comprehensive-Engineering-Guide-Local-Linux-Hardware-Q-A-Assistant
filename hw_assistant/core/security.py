"""Security enforcement engine: allow-lists, argument sanitization, and subshell prevention."""
import re
from typing import Dict, List, Tuple, Any


class SecurityValidationError(Exception):
    """Raised when an unauthorized command, tool, or injection attempt is detected."""
    pass


# Strict immutable mapping of approved tools to binary argument vectors
ALLOW_LISTED_TOOLS: Dict[str, Tuple[str, ...]] = {
    "get_cpu_info": ("lscpu",),
    "get_block_devices": ("lsblk", "-J", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,MODEL,ROTA,TRAN"),
    "get_memory_summary": ("free", "-b"),
    "get_memory_topology": ("sudo", "-n", "/usr/sbin/dmidecode", "-t", "memory"),
    "get_gpu_info": ("lspci", "-vmm"),
    "get_system_info": ("sudo", "-n", "/usr/sbin/dmidecode", "-t", "system"),
}

# Unprivileged fallback commands when root / dmidecode is unavailable
FALLBACK_COMMANDS: Dict[str, Tuple[str, ...]] = {
    "proc_meminfo": ("/bin/cat", "/proc/meminfo"),
    "proc_cpuinfo": ("/bin/cat", "/proc/cpuinfo"),
    "os_release": ("/bin/cat", "/etc/os-release"),
}

# Dangerous shell metacharacters and tokens to reject in all parameters
DANGEROUS_PATTERNS = [
    re.compile(r"[;&|`$><]"),           # Shell chaining and redirection
    re.compile(r"\$\(.*\)"),            # Command substitution
    re.compile(r"`.*`"),                # Backtick substitution
    re.compile(r"\.\./"),               # Path traversal
    re.compile(r"^--?[a-zA-Z0-9_-]+"),  # Flag injection attempts
]


def validate_tool_name(tool_name: str) -> None:
    """Ensures tool is present in the static allow-list."""
    if tool_name not in ALLOW_LISTED_TOOLS:
        raise SecurityValidationError(
            f"Blocked unauthorized tool call: '{tool_name}'. Tool is not in Allow-List."
        )


def sanitize_argument_value(key: str, value: Any) -> None:
    """Validates that tool arguments contain no malicious injection vectors."""
    if isinstance(value, bool):
        return  # Booleans are safe

    if isinstance(value, (int, float)):
        return  # Numbers are safe

    if isinstance(value, str):
        # Check against dangerous injection patterns
        for pattern in DANGEROUS_PATTERNS:
            if pattern.search(value):
                raise SecurityValidationError(
                    f"Malicious parameter detected in argument '{key}': '{value}'. Execution rejected."
                )
    else:
        raise SecurityValidationError(
            f"Unsupported parameter type for '{key}': {type(value).__name__}."
        )


def get_command_vector(tool_name: str, kwargs: Dict[str, Any]) -> List[str]:
    """Validates inputs and returns the immutable command array for execve."""
    validate_tool_name(tool_name)

    for k, v in kwargs.items():
        sanitize_argument_value(k, v)

    # Return a copy of the fixed command vector
    return list(ALLOW_LISTED_TOOLS[tool_name])
