"""Tests for execution engine, mock simulation, and privilege fallback handling."""
from hw_assistant.core.executor import SystemExecutionEngine
from hw_assistant.core.security import SecurityValidationError


def test_mock_execution_all_tools():
    engine = SystemExecutionEngine(mock_mode=True)
    tools = [
        "get_memory_topology",
        "get_cpu_info",
        "get_memory_summary",
        "get_block_devices",
        "get_gpu_info",
        "get_system_info",
    ]
    for tool in tools:
        res = engine.execute_tool(tool)
        assert res.success is True
        assert res.data is not None
        assert res.source == "mock"


def test_mock_memory_topology_options():
    engine = SystemExecutionEngine(mock_mode=True)
    res_all = engine.execute_tool("get_memory_topology", {"include_empty_slots": True})
    assert len(res_all.data["installed_modules"]) == 2

    res_populated = engine.execute_tool("get_memory_topology", {"include_empty_slots": False})
    assert len(res_populated.data["installed_modules"]) == 1


def test_security_violation_caught_by_executor():
    engine = SystemExecutionEngine(mock_mode=False)
    # Injecting invalid tool
    res = engine.execute_tool("malicious_tool")
    assert res.success is False
    assert res.source == "security_block"
    assert "Blocked unauthorized tool call" in res.error

    # Injecting command separator in argument
    res2 = engine.execute_tool("get_cpu_info", {"device": "sda; rm -rf /"})
    assert res2.success is False
    assert res2.source == "security_block"
    assert "Malicious parameter detected" in res2.error
