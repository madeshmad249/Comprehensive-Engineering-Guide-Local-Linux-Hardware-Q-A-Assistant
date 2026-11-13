"""CLI application for the Local Linux Hardware Q&A Assistant."""
import sys
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from .core.discovery import discover_system_capabilities
from .core.executor import SystemExecutionEngine
from .core.session import ConversationSession
from .core.agent import HardwareAssistantAgent

app = typer.Typer(
    name="linux-hw-assistant",
    help="Deterministic, secure local Linux hardware Q&A assistant with strict anti-hallucination tool calling.",
    add_completion=False,
)
console = Console()


def _get_executor(mock: Optional[bool] = None) -> SystemExecutionEngine:
    """Returns executor in native or mock mode. Auto-defaults to mock on non-Linux systems."""
    is_linux = sys.platform.startswith("linux")
    if mock is None:
        use_mock = not is_linux
    else:
        use_mock = mock
    return SystemExecutionEngine(mock_mode=use_mock)


@app.command()
def ask(
    query: str = typer.Argument(..., help="Hardware question (e.g., 'Can I upgrade my RAM?')"),
    mock: bool = typer.Option(False, "--mock", "-m", help="Force mock hardware mode (default on non-Linux)"),
    llm_endpoint: Optional[str] = typer.Option(None, "--llm", help="Optional local Ollama/OpenAI endpoint (e.g. http://localhost:11434)"),
    model: str = typer.Option("qwen2.5:7b", "--model", help="LLM model name if using external endpoint"),
):
    """Answers a single hardware question with verified system facts."""
    executor = _get_executor(mock if mock else None)
    agent = HardwareAssistantAgent(executor=executor, llm_endpoint=llm_endpoint, model_name=model)

    mode_notice = "[dim](Mock Mode: ThinkPad T14 fixture)[/dim]" if executor.mock_mode else "[dim](Native Linux System Query)[/dim]"
    console.print(f"[bold cyan]Query:[/bold cyan] {query} {mode_notice}")

    with console.status("[bold green]Executing verified system tools...[/bold green]"):
        response = agent.process_query(query)

    console.print(Panel(Markdown(response), title="[bold green]Hardware Assistant Response[/bold green]", border_style="green"))


@app.command()
def chat(
    mock: bool = typer.Option(False, "--mock", "-m", help="Force mock hardware mode"),
    llm_endpoint: Optional[str] = typer.Option(None, "--llm", help="Optional local Ollama/OpenAI endpoint"),
    model: str = typer.Option("qwen2.5:7b", "--model", help="LLM model name"),
):
    """Starts an interactive multi-turn conversational session."""
    executor = _get_executor(mock if mock else None)
    session = ConversationSession()
    agent = HardwareAssistantAgent(executor=executor, session=session, llm_endpoint=llm_endpoint, model_name=model)

    mode_label = "MOCK SIMULATION" if executor.mock_mode else "NATIVE LINUX"
    console.print(
        Panel(
            f"[bold green]Local Linux Hardware Q&A Assistant[/bold green]\n"
            f"Mode: [cyan]{mode_label}[/cyan] | Strict Anti-Hallucination: [bold]ACTIVE[/bold]\n"
            f"Type your hardware questions below. Type [yellow]'exit'[/yellow] or [yellow]'quit'[/yellow] to end session.",
            title="Session Started",
            border_style="cyan",
        )
    )

    while True:
        try:
            query = console.input("\n[bold cyan]hw-assistant>[/bold cyan] ").strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit", "q"):
                console.print("[yellow]Exiting session. Goodbye![/yellow]")
                break

            with console.status("[bold green]Inspecting hardware...[/bold green]"):
                answer = agent.process_query(query)

            console.print(Panel(Markdown(answer), border_style="green"))
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Session interrupted. Goodbye![/yellow]")
            break


@app.command()
def inspect(
    mock: bool = typer.Option(False, "--mock", "-m", help="Force mock hardware mode"),
):
    """Displays a complete structured hardware specification sheet."""
    executor = _get_executor(mock if mock else None)

    with console.status("[bold green]Probing system hardware...[/bold green]"):
        cpu_res = executor.execute_tool("get_cpu_info")
        mem_topo_res = executor.execute_tool("get_memory_topology")
        disk_res = executor.execute_tool("get_block_devices")
        gpu_res = executor.execute_tool("get_gpu_info")
        sys_res = executor.execute_tool("get_system_info")

    mode_label = "MOCK FIXTURE" if executor.mock_mode else "HOST LINUX"
    console.print(f"\n[bold magenta]=== Hardware Specification Report ({mode_label}) ===[/bold magenta]\n")

    # 1. System Info Table
    if sys_res.success and sys_res.data:
        sys_tbl = Table(title="Host Machine & Chassis", expand=True)
        sys_tbl.add_column("Property", style="cyan")
        sys_tbl.add_column("Value", style="white")
        for k, v in sys_res.data.items():
            if v:
                sys_tbl.add_row(k.replace("_", " ").title(), str(v))
        console.print(sys_tbl)
        console.print()

    # 2. CPU Table
    if cpu_res.success and cpu_res.data:
        cpu_data = cpu_res.data
        cpu_tbl = Table(title="Processor (CPU)", expand=True)
        cpu_tbl.add_column("Property", style="cyan")
        cpu_tbl.add_column("Value", style="white")
        cpu_tbl.add_row("Model", cpu_data.get("model_name", "Unknown"))
        cpu_tbl.add_row("Architecture", cpu_data.get("architecture", "Unknown"))
        cpu_tbl.add_row("Physical Cores", str(cpu_data.get("cores", "Unknown")))
        cpu_tbl.add_row("Threads", str(cpu_data.get("threads", "Unknown")))
        if cpu_data.get("max_mhz"):
            cpu_tbl.add_row("Max Frequency", f"{cpu_data['max_mhz']:.1f} MHz")
        if cpu_data.get("l3_cache"):
            cpu_tbl.add_row("L3 Cache", cpu_data["l3_cache"])
        if cpu_data.get("virtualization"):
            cpu_tbl.add_row("Virtualization", cpu_data["virtualization"])
        console.print(cpu_tbl)
        console.print()

    # 3. RAM Topology Table
    if mem_topo_res.success and mem_topo_res.data:
        m_data = mem_topo_res.data
        mem_tbl = Table(title="Physical Memory (RAM) Topology", expand=True)
        mem_tbl.add_column("Slot Locator", style="cyan")
        mem_tbl.add_column("Status / Size", style="white")
        mem_tbl.add_column("Type & Speed", style="white")
        mem_tbl.add_column("Form Factor", style="dim")
        mem_tbl.add_column("Part Number", style="dim")

        for slot in m_data.get("installed_modules", []):
            is_empty = slot.get("is_empty")
            status = "[yellow]Empty Slot[/yellow]" if is_empty else f"[green]{slot.get('size_human')}[/green]"
            type_speed = f"{slot.get('type') or ''} {slot.get('speed') or ''}".strip() or "-"
            mem_tbl.add_row(
                slot.get("locator", "Unknown"),
                status,
                type_speed,
                slot.get("form_factor") or "-",
                slot.get("part_number") or "-",
            )
        console.print(mem_tbl)
        console.print(
            f"[bold]Summary:[/bold] {m_data.get('used_slots')}/{m_data.get('total_slots')} slots used. "
            f"Max motherboard capacity: [bold green]{m_data.get('maximum_capacity_human')}[/bold green]. "
            f"Free slots: [bold cyan]{m_data.get('free_slots')}[/bold cyan]."
        )
        console.print()

    # 4. Storage Table
    if disk_res.success and disk_res.data:
        disk_tbl = Table(title="Storage Drives & Partitions", expand=True)
        disk_tbl.add_column("Device", style="cyan")
        disk_tbl.add_column("Model", style="white")
        disk_tbl.add_column("Size", style="white")
        disk_tbl.add_column("Type / Bus", style="green")
        disk_tbl.add_column("Partitions / Mounts", style="dim")

        for dev in disk_res.data.get("devices", []):
            tran = dev.get("transport") or ("NVMe" if "nvme" in dev.get("name") else "SATA")
            kind = "SSD" if dev.get("is_ssd") else "HDD"
            parts = ", ".join(
                f"{p['name']} ({p.get('mountpoint') or 'unmounted'})" for p in dev.get("children", [])
            )
            disk_tbl.add_row(
                dev.get("name"),
                dev.get("model") or "Generic",
                dev.get("size_human"),
                f"{kind} ({tran.upper()})",
                parts or "None",
            )
        console.print(disk_tbl)
        console.print()

    # 5. GPU Table
    if gpu_res.success and gpu_res.data:
        gpu_tbl = Table(title="Display & GPU Controllers", expand=True)
        gpu_tbl.add_column("PCI Slot", style="cyan")
        gpu_tbl.add_column("Vendor", style="white")
        gpu_tbl.add_column("Device Name", style="white")

        for g in gpu_res.data.get("gpus", []):
            gpu_tbl.add_row(g.get("pci_slot"), g.get("vendor"), g.get("device_name"))
        console.print(gpu_tbl)


@app.command()
def doctor():
    """Diagnoses host environment, binaries, privileges, and unprivileged fallbacks."""
    caps = discover_system_capabilities(mock=False)

    tbl = Table(title="System Capability & Security Diagnosis", expand=True)
    tbl.add_column("Check / Capability", style="cyan")
    tbl.add_column("Status", style="bold")
    tbl.add_column("Detail / Impact", style="dim")

    def _mark(val: bool, ok_text: str = "AVAILABLE", bad_text: str = "MISSING") -> str:
        return f"[green]{ok_text}[/green]" if val else f"[red]{bad_text}[/red]"

    tbl.add_row("Operating System", f"[green]Linux[/green]" if caps.is_linux else "[yellow]Non-Linux[/yellow]", sys.platform)
    tbl.add_row("lscpu Binary", _mark(caps.has_lscpu), "Used for processor & cache topology")
    tbl.add_row("lsblk Binary", _mark(caps.has_lsblk), "Used for storage & NVMe partition tree")
    tbl.add_row("free Binary", _mark(caps.has_free), "Used for quick memory consumption summary")
    tbl.add_row("lspci Binary", _mark(caps.has_lspci), "Used for GPU & PCI device enumeration")
    tbl.add_row("dmidecode Binary", _mark(caps.has_dmidecode), "Used for motherboard RAM slots & limits")
    tbl.add_row(
        "dmidecode Sudo (No Password)",
        _mark(caps.has_sudo_dmidecode, "CONFIGURED", "NOT CONFIGURED"),
        "Enables Strategy A scoped sudo execution without prompting for root password"
    )
    tbl.add_row("/proc/meminfo Fallback", _mark(caps.has_proc_meminfo), "Strategy C zero-install RAM fallback")
    tbl.add_row("/proc/cpuinfo Fallback", _mark(caps.has_proc_cpuinfo), "Strategy C zero-install CPU fallback")
    tbl.add_row("/sys/class/dmi Fallback", _mark(caps.has_sys_dmi), "Strategy C zero-install DMI fallback")

    console.print(tbl)

    if not caps.has_sudo_dmidecode and caps.is_linux:
        console.print(
            Panel(
                "[bold yellow]Privilege Escalation Recommendation (Strategy A):[/bold yellow]\n"
                "To allow reading physical RAM slots and max capacity without root prompts, add:\n\n"
                "[bold cyan]ALL ALL=(root) NOPASSWD: /usr/sbin/dmidecode -t memory, /usr/sbin/dmidecode -t system[/bold cyan]\n\n"
                "into [bold]/etc/sudoers.d/hw-assistant[/bold] and run [bold]sudo chmod 0440 /etc/sudoers.d/hw-assistant[/bold].",
                border_style="yellow",
            )
        )


if __name__ == "__main__":
    app()
