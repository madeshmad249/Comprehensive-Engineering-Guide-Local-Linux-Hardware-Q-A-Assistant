"""Tests for agent routing, session context caching, and anti-hallucination synthesis."""
from hw_assistant.core.executor import SystemExecutionEngine
from hw_assistant.core.session import ConversationSession
from hw_assistant.core.agent import HardwareAssistantAgent, OfflineDeterministicEngine


def test_offline_deterministic_intent_routing():
    engine = OfflineDeterministicEngine()
    
    # RAM upgrade intent
    tools = engine.route_query("Can I upgrade my RAM, and by how much?")
    assert tools == ["get_memory_topology"]

    # CPU intent
    tools = engine.route_query("What processor and core count do I have?")
    assert "get_cpu_info" in tools

    # Storage intent
    tools = engine.route_query("Do I have an NVMe SSD or hard drive?")
    assert "get_block_devices" in tools

    # GPU intent
    tools = engine.route_query("What graphics card is installed?")
    assert "get_gpu_info" in tools


def test_agent_process_query_mock():
    executor = SystemExecutionEngine(mock_mode=True)
    session = ConversationSession()
    agent = HardwareAssistantAgent(executor=executor, session=session)

    response = agent.process_query("Can I upgrade my RAM, and by how much?")
    # Check grounded factual assertions
    assert "64 GB" in response
    assert "16 GB" in response
    assert "empty slot" in response.lower()
    assert "ChannelA-DIMM0" in response or "DDR4" in response
    assert len(session.messages) == 2  # 1 user + 1 assistant


def test_agent_context_caching():
    executor = SystemExecutionEngine(mock_mode=True)
    session = ConversationSession()
    agent = HardwareAssistantAgent(executor=executor, session=session)

    # First query populates cache
    agent.process_query("Tell me about my RAM")
    assert "get_memory_topology" in session.cached_hardware_facts

    # Second query should use cache
    agent.process_query("What was the maximum memory again?")
    assert len(session.messages) == 4
