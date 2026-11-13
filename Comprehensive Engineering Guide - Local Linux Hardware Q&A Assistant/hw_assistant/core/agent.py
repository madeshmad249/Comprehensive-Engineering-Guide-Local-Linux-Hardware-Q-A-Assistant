"""LLM orchestration engine with strict anti-hallucination prompting and offline deterministic fallback."""
import json
import re
from typing import Dict, Any, List, Optional, Tuple
import httpx

from .executor import SystemExecutionEngine
from .session import ConversationSession
from ..models.tools import SYSTEM_TOOLS, ToolCallRequest, ToolCallResponse


SYSTEM_GROUNDING_PROMPT = """You are a specialized, factual Linux Hardware Assistant.
Your job is to answer user queries about host machine hardware with 100% precision.

CRITICAL RULES:
1. Base your response SOLELY on the verified JSON data returned by system tools.
2. If the JSON data does not contain the answer or fields are marked 'Unknown' or missing, state clearly: "I cannot determine this hardware detail from system data." Never speculate, extrapolate, or guess hardware specs.
3. Be concise, direct, and technically precise.
4. When discussing RAM upgrades, always state:
   - Current installed memory
   - Total number of motherboard slots
   - Number of free / empty slots
   - Maximum supported motherboard capacity
5. When discussing disks, distinguish NVMe/PCIe SSDs from SATA and rotational HDDs.
"""


class OfflineDeterministicEngine:
    """Zero-dependency, offline deterministic agent that maps user intent to tools and formats grounded answers."""

    INTENT_KEYWORDS: Dict[str, List[str]] = {
        "get_memory_topology": ["ram", "memory", "dimm", "sodimm", "slot", "upgrade", "ddr4", "ddr5", "capacity", "max memory"],
        "get_cpu_info": ["cpu", "processor", "core", "thread", "ghz", "mhz", "intel", "amd", "ryzen", "architecture", "cache", "flags", "virtualization"],
        "get_block_devices": ["disk", "drive", "storage", "ssd", "nvme", "hdd", "hard drive", "partition", "mount", "space", "lsblk"],
        "get_gpu_info": ["gpu", "graphic", "graphics", "video", "nvidia", "radeon", "vga", "display controller"],
        "get_system_info": ["system", "laptop", "motherboard", "bios", "vendor", "model", "thinkpad", "dell", "chassis", "machine"],
        "get_memory_summary": ["free memory", "used memory", "available memory", "swap", "ram usage"],
    }

    def route_query(self, query: str) -> List[str]:
        """Determines which tool(s) to execute based on user intent keywords."""
        query_lower = query.lower()
        selected_tools: List[str] = []

        # Check memory upgrade specifically
        if "upgrade" in query_lower and ("ram" in query_lower or "memory" in query_lower):
            return ["get_memory_topology"]

        for tool_name, keywords in self.INTENT_KEYWORDS.items():
            if any(k in query_lower for k in keywords):
                selected_tools.append(tool_name)

        # Default fallback if query is general
        if not selected_tools:
            if "hardware" in query_lower or "spec" in query_lower or "summary" in query_lower:
                return ["get_cpu_info", "get_memory_topology", "get_block_devices"]
            return ["get_system_info"]

        return selected_tools

    def synthesize_response(self, query: str, tool_results: List[ToolCallResponse]) -> str:
        """Synthesizes a response strictly adhering to tool JSON data without hallucination."""
        lines = []

        for res in tool_results:
            if not res.success or not res.data:
                lines.append(f"- Tool '{res.tool_name}' failed: {res.error or 'Data unavailable'}.")
                continue

            data = res.data

            if res.tool_name == "get_memory_topology":
                max_cap = data.get("maximum_capacity_human", "Unknown")
                total = data.get("total_slots", 0)
                used = data.get("used_slots", 0)
                free = data.get("free_slots", 0)
                modules = data.get("installed_modules", [])

                installed_desc = []
                for m in modules:
                    if not m.get("is_empty"):
                        loc = m.get("locator", "Slot")
                        size = m.get("size_human", "Unknown")
                        m_type = m.get("type", "")
                        speed = m.get("speed", "")
                        installed_desc.append(f"{loc}: {size} {m_type} {speed}".strip())

                lines.append(f"**RAM Topology & Upgradeability:**")
                lines.append(f"- Installed: {len(installed_desc)} populated slot(s) out of {total} total.")
                for d in installed_desc:
                    lines.append(f"  * {d}")
                lines.append(f"- Available empty slots: {free}")
                lines.append(f"- Maximum supported capacity: {max_cap}")
                if free > 0:
                    lines.append(f"- Upgrade Status: **Yes**, you have {free} empty slot(s) available for upgrading.")
                else:
                    lines.append(f"- Upgrade Status: All slots are occupied. Upgrades require replacing existing modules.")

            elif res.tool_name == "get_cpu_info":
                model = data.get("model_name", "Unknown CPU")
                cores = data.get("cores", "Unknown")
                threads = data.get("threads", "Unknown")
                arch = data.get("architecture", "Unknown")
                max_mhz = data.get("max_mhz")
                l3 = data.get("l3_cache")
                virt = data.get("virtualization")

                lines.append(f"**Processor (CPU):**")
                lines.append(f"- Model: {model}")
                lines.append(f"- Architecture: {arch}")
                lines.append(f"- Cores & Threads: {cores} physical cores, {threads} logical threads")
                if max_mhz:
                    lines.append(f"- Max Frequency: {max_mhz:.1f} MHz")
                if l3:
                    lines.append(f"- L3 Cache: {l3}")
                if virt:
                    lines.append(f"- Virtualization: {virt}")

            elif res.tool_name == "get_block_devices":
                devices = data.get("devices", [])
                lines.append(f"**Storage & Block Devices:**")
                for d in devices:
                    name = d.get("name")
                    size = d.get("size_human")
                    model = d.get("model") or "Generic Drive"
                    tran = d.get("transport") or ("NVMe" if "nvme" in name else "SATA")
                    kind = "SSD" if d.get("is_ssd") else "HDD"
                    lines.append(f"- `{name}`: {model} ({size}, {kind} via {tran.upper()})")
                    for p in d.get("children", []):
                        p_name = p.get("name")
                        p_size = p.get("size_human")
                        mp = p.get("mountpoint") or "Unmounted"
                        lines.append(f"  * Partition `{p_name}` ({p_size}) -> {mp}")

            elif res.tool_name == "get_gpu_info":
                gpus = data.get("gpus", [])
                lines.append(f"**Graphics Controllers (GPU):**")
                if not gpus:
                    lines.append("- No dedicated graphics controllers detected.")
                for g in gpus:
                    dev = g.get("device_name", "Unknown Device")
                    slot = g.get("pci_slot")
                    vendor = g.get("vendor", "")
                    lines.append(f"- [{slot}] {vendor} - {dev}")

            elif res.tool_name == "get_system_info":
                mfg = data.get("manufacturer") or "Unknown"
                prod = data.get("product_name") or "Unknown"
                chassis = data.get("chassis_type") or "Unknown"
                lines.append(f"**System & Chassis:**")
                lines.append(f"- Machine: {mfg} {prod}")
                lines.append(f"- Chassis: {chassis}")

            elif res.tool_name == "get_memory_summary":
                tot = data.get("total_bytes", 0) / (1024**3)
                avail = data.get("available_bytes", 0) / (1024**3)
                used = data.get("used_bytes", 0) / (1024**3)
                lines.append(f"**Memory Consumption:**")
                lines.append(f"- Total: {tot:.2f} GB | Used: {used:.2f} GB | Available: {avail:.2f} GB")

        return "\n".join(lines)


class HardwareAssistantAgent:
    """Main conversational coordinator managing execution, context caching, and answer generation."""

    def __init__(
        self,
        executor: SystemExecutionEngine,
        session: Optional[ConversationSession] = None,
        llm_endpoint: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self.executor = executor
        self.session = session or ConversationSession()
        self.llm_endpoint = llm_endpoint
        self.model_name = model_name or "qwen2.5:7b"
        self.deterministic_engine = OfflineDeterministicEngine()

    def process_query(self, user_query: str) -> str:
        """Processes a query, selects and executes tools, and generates a factual response."""
        self.session.add_user_message(user_query)

        # 1. Determine tools required
        tools_to_run = self.deterministic_engine.route_query(user_query)

        # 2. Check cached facts first to avoid unnecessary executions
        tool_results: List[ToolCallResponse] = []
        for t in tools_to_run:
            cached = self.session.get_cached_tool_data(t)
            if cached is not None:
                tool_results.append(
                    ToolCallResponse(tool_name=t, success=True, data=cached, source="cache")
                )
            else:
                res = self.executor.execute_tool(t)
                if res.success and res.data:
                    self.session.cache_tool_data(t, res.data)
                tool_results.append(res)

        # 3. Generate response
        # If an external local LLM endpoint is provided and online, use it; otherwise use the strict offline engine
        answer = None
        if self.llm_endpoint:
            answer = self._query_llm(user_query, tool_results)

        if not answer:
            answer = self.deterministic_engine.synthesize_response(user_query, tool_results)

        self.session.add_assistant_message(answer)
        return answer

    def _query_llm(self, query: str, tool_results: List[ToolCallResponse]) -> Optional[str]:
        """Calls local Ollama or OpenAI-compatible endpoint with grounding context."""
        context_data = {r.tool_name: r.data for r in tool_results if r.success and r.data}
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_GROUNDING_PROMPT},
                {"role": "user", "content": f"Hardware JSON Facts:\n{json.dumps(context_data, indent=2)}\n\nUser Question:\n{query}"}
            ],
            "temperature": 0.0,
        }
        try:
            url = f"{self.llm_endpoint.rstrip('/')}/v1/chat/completions"
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
        except Exception:
            pass
        return None
