# Local Linux Hardware Q&A Assistant

A deterministic, secure, natural-language conversational assistant (CLI / TUI) that inspects a host Linux machine's hardware specifications and answers user queries with high precision, zero hallucinations, and sandboxed privilege handling.

```
+-----------------------------------------------------------------------------------+
| 1. USER INPUT                                                                     |
|    "Can I upgrade my RAM, and by how much?"                                       |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 2. INTENT & TOOL SELECTION (LLM / Agent Router)                                   |
|    Decides necessary tools: `get_memory_topology`                                 |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 3. SECURE SYSTEM EXECUTION ENGINE                                                 |
|    Validates command against strict Allow-list -> Invokes scoped Helper Daemon    |
|    Runs `dmidecode -t memory` / parses `/proc/meminfo`                            |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 4. PARSER & NORMALIZER                                                            |
|    Transforms raw unstructured command stdout into validated Pydantic JSON        |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 5. CONTEXTUAL ANSWER SYNTHESIS                                                    |
|    Formats response using only verified JSON data                                 |
|    "You have 16 GB installed in 1 of 2 slots. Maximum supported is 64 GB..."     |
+-----------------------------------------------------------------------------------+
```

---

## Key Architecture & Security Pillars

### 1. Security & Anti-Arbitrary Code Execution
- **Strict Allow-List Enforcement:** The agent never invokes `/bin/sh` or arbitrary bash scripts.
- **Direct Syscalls (`execve` / `shell=False`):** Commands are executed directly with immutable argument tuples. Shell metacharacters (`;`, `&&`, `|`, `$(...)`, `` ` ``), flag injections (`--flag`), and path traversal attempts are rejected before execution.
- **Parameter Sanitization:** Tool arguments are strictly scalar and validated against allow-list regexes and schemas.

### 2. Privilege Escalation Strategies

| Strategy | Mechanism | Best Suited For | Implementation Status |
| --- | --- | --- | --- |
| **Strategy A (Scoped Sudo)** | Rule in `/etc/sudoers.d/hw-assistant` allowing passwordless execution of only specific binaries (e.g. `/usr/sbin/dmidecode -t memory`). | Production CLI & Server environments | Included template: [`sudoers.d/hw-assistant-sudoers.example`](sudoers.d/hw-assistant-sudoers.example) |
| **Strategy B (Privilege Daemon)** | Root background daemon listening on an isolated Unix domain socket (`/run/hw-assistant/daemon.sock`, `0660`). | Desktop GUI / Daemon services | Reference implementation in [`hw_assistant/daemon/privilege_daemon.py`](hw_assistant/daemon/privilege_daemon.py) |
| **Strategy C (Non-Root Fallback)** | Reading unprivileged interfaces (`/proc/meminfo`, `/proc/cpuinfo`, `/sys/class/dmi/id/*`). | Zero-setup, non-root environments | Fully integrated into execution engine |

### 3. Anti-Hallucination & Uncertainty Handling
- System prompt mandates strict adherence to retrieved JSON data.
- Unverified, unknown, or missing fields are explicitly reported as *"Data unavailable"* rather than guessed.
- Memory upgrade answers always specify current installed memory, populated slots, empty slots, and maximum supported motherboard capacity.

### 4. Cross-Platform Simulation Fixtures
- Authentic fixture captures from ThinkPad T14 (AMD Ryzen + DDR4) and Framework laptops allow full testing and development on any OS (including macOS and Windows).
- Automatically toggles between native Linux syscalls and mock fixtures.

---

## Installation & Setup

```bash
# Clone and enter directory
cd linux-hw-assistant

# Install dependencies
pip install -r requirements.txt
```

### Optional: Set Up Scoped Sudoers (Linux Host)

To allow the assistant to read SMBIOS/DMI motherboard slot details without root password prompts:

```bash
sudo cp sudoers.d/hw-assistant-sudoers.example /etc/sudoers.d/hw-assistant
sudo chmod 0440 /etc/sudoers.d/hw-assistant
sudo visudo -c  # verify syntax
```

---

## CLI Usage

### 1. Ask a One-Shot Hardware Question
```bash
# Ask about RAM upgradeability
python -m hw_assistant.cli ask "Can I upgrade my RAM, and by how much?" --mock

# Ask about CPU
python -m hw_assistant.cli ask "What processor and core count do I have?" --mock

# Ask about Storage
python -m hw_assistant.cli ask "What drives and partitions are installed?" --mock
```

### 2. Interactive Multi-Turn Chat
```bash
python -m hw_assistant.cli chat --mock
```
*Features conversation state memory and cached hardware facts across turns.*

### 3. Complete Hardware Specification Sheet
```bash
python -m hw_assistant.cli inspect --mock
```

### 4. Capability & Security Doctor
```bash
python -m hw_assistant.cli doctor
```
*Probes available binaries, sudoers configuration, and unprivileged fallbacks.*

### 5. Connecting a Local LLM (Ollama / vLLM)
```bash
# Point to local Ollama instance (e.g. running Qwen2.5:7b or Llama-3.2:3b)
python -m hw_assistant.cli ask "Can I upgrade my RAM?" --llm http://localhost:11434 --model qwen2.5:7b
```

---

## Running Automated Tests

```bash
python -m pytest tests/ -v
```

36 comprehensive tests covering:
- **Security:** Arbitrary command injection blocking, flag smuggling rejection, allow-list enforcement.
- **Parsers:** `dmidecode` memory topology, `lscpu`, `lsblk` JSON, `free -b`, `lspci` GPU, sysfs DMI, and os-release.
- **Execution & Fallbacks:** Mock runner, native execution, non-root fallback cascade.
- **Agent:** Intent routing, context caching, grounded synthesis.
- **CLI:** Typer CLI test runner for all commands.
