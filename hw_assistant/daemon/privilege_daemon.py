"""Strategy B: Background Privilege Daemon reference implementation using Unix Domain Sockets.

This daemon runs as root (e.g., managed by systemd) and exposes an isolated IPC socket
restricted to the 'hw-assistant' group (0660). It accepts only pre-defined action verbs
and returns validated JSON, completely isolating root privileges from the LLM assistant.
"""
import os
import sys
import json
import socket
import subprocess
from typing import Dict, Any, Optional

DEFAULT_SOCKET_PATH = "/run/hw-assistant/daemon.sock"


class HardwarePrivilegeDaemon:
    """Privileged root daemon exposing restricted hardware inspection endpoints over UDS."""

    def __init__(self, socket_path: str = DEFAULT_SOCKET_PATH):
        self.socket_path = socket_path
        self.is_running = False

    def handle_request(self, request_data: str) -> Dict[str, Any]:
        """Dispatches allowed actions and prevents arbitrary code execution."""
        try:
            req = json.loads(request_data)
            action = req.get("action")

            if action == "GetDmiMemory":
                res = subprocess.run(
                    ["/usr/sbin/dmidecode", "-t", "memory"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=5,
                )
                return {"status": "ok", "stdout": res.stdout}

            elif action == "GetDmiSystem":
                res = subprocess.run(
                    ["/usr/sbin/dmidecode", "-t", "system"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=5,
                )
                return {"status": "ok", "stdout": res.stdout}

            elif action == "Ping":
                return {"status": "ok", "message": "pong"}

            else:
                return {"status": "error", "error": f"Unauthorized action: '{action}'"}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def start_server(self) -> None:
        """Starts the Unix Domain Socket listener (requires Linux / Unix)."""
        if not hasattr(socket, "AF_UNIX"):
            print("Unix Domain Sockets (AF_UNIX) are not supported on this platform.", file=sys.stderr)
            return

        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

        os.makedirs(os.path.dirname(self.socket_path), exist_ok=True)

        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(self.socket_path)
        # Restrict permissions so only authorized users/groups can connect
        os.chmod(self.socket_path, 0o660)
        server.listen(5)
        self.is_running = True
        print(f"Hardware Privilege Daemon listening on {self.socket_path}")

        try:
            while self.is_running:
                conn, _ = server.accept()
                with conn:
                    data = conn.recv(4096).decode("utf-8")
                    if not data:
                        continue
                    response = self.handle_request(data)
                    conn.sendall(json.dumps(response).encode("utf-8"))
        finally:
            server.close()
            if os.path.exists(self.socket_path):
                os.remove(self.socket_path)


class DaemonClient:
    """Client for unprivileged processes to query the root privilege daemon."""

    def __init__(self, socket_path: str = DEFAULT_SOCKET_PATH):
        self.socket_path = socket_path

    def is_available(self) -> bool:
        return hasattr(socket, "AF_UNIX") and os.path.exists(self.socket_path)

    def send_action(self, action: str) -> Optional[Dict[str, Any]]:
        if not self.is_available():
            return None
        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.connect(self.socket_path)
            with client:
                client.sendall(json.dumps({"action": action}).encode("utf-8"))
                raw = client.recv(65536).decode("utf-8")
                return json.loads(raw)
        except Exception:
            return None
