"""
Kuber Data Core (कुबेर) — Intelligent Server Launcher
Automatically checks for active instance on port 8002, reuses running daemon,
binds to next available free port if occupied, and launches default browser safely.
"""

import sys
import socket
import webbrowser
import time
import urllib.request
import json
from pathlib import Path

# Force UTF-8 stdout & stderr on Windows console to prevent UnicodeEncodeError with Hindi/Devanagari
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import uvicorn


def is_kuber_running(port: int = 8002) -> bool:
    """Checks if Kuber Data Core is already running and responsive."""
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/health",
            headers={"User-Agent": "KuberLauncher/1.0"}
        )
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
                return "Kuber Data Core" in data.get("service", "")
    except Exception:
        return False
    return False


def find_free_port(start_port: int = 8002, max_port: int = 8030) -> int:
    """Finds next free TCP port."""
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port


def main():
    # 1. If Kuber is ALREADY running on port 8002, open browser and inform user
    if is_kuber_running(8002):
        url = "http://127.0.0.1:8002"
        print("=" * 72)
        print("   KUBER DATA CORE -- ENTERPRISE FINANCIAL INTELLIGENCE WORKSTATION")
        print(f"   [ACTIVE] Server daemon is ALREADY running and healthy at {url}")
        print("   Launching workstation in your default browser...")
        print("=" * 72)
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"   [NOTICE] Could not automatically open browser: {e}")
            print(f"   Please open: {url}")
        print("\n   Workstation active. You may minimize this window or press Enter to exit.")
        time.sleep(1.5)
        return

    # 2. Bind to 8002 or next available port
    port = find_free_port(8002)
    url = f"http://127.0.0.1:{port}"

    print("=" * 72)
    print("   KUBER DATA CORE -- ENTERPRISE FINANCIAL INTELLIGENCE WORKSTATION")
    print(f"   Starting Server on: {url}")
    print("   SEC EDGAR & FIBO Knowledge Graph Engine Online")
    print("=" * 72)

    def wait_and_open_browser():
        """Actively waits for server to start before launching browser to avoid ERR_CONNECTION_REFUSED."""
        for _ in range(40):
            time.sleep(0.3)
            if is_kuber_running(port):
                print(f"   [HEALTHY] Kuber Data Core is responding on {url}. Opening browser...")
                try:
                    webbrowser.open(url)
                except Exception:
                    pass
                return
        # Fallback if healthcheck timed out
        try:
            webbrowser.open(url)
        except Exception:
            pass

    import threading
    threading.Thread(target=wait_and_open_browser, daemon=True).start()

    uvicorn.run("backend.main:app", host="127.0.0.1", port=port, reload=False)


if __name__ == "__main__":
    main()
