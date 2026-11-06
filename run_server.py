"""
Kuber Data Core (कुबेर) — Intelligent Server Launcher
Automatically checks for active instance on port 8002, reuses running daemon,
binds to next available free port if occupied, and launches default browser.
"""

import sys
import socket
import webbrowser
import time
import urllib.request
import json
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import uvicorn


def is_kuber_running(port: int = 8002) -> bool:
    """Checks if Kuber Data Core is already running and responsive."""
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/health", headers={"User-Agent": "KuberLauncher"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
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
    if is_kuber_running(8002):
        url = "http://127.0.0.1:8002"
        print("=" * 72)
        print("   KUBER DATA CORE -- ENTERPRISE FINANCIAL INTELLIGENCE WORKSTATION")
        print(f"   [INFO] Kuber Data Core is ALREADY active and healthy on {url}")
        print("   Opening workstation interface in your default browser...")
        print("=" * 72)
        webbrowser.open(url)
        print("\nPress Ctrl+C to close this launcher window (server stays active in background).")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            return

    port = find_free_port(8002)
    url = f"http://127.0.0.1:{port}"

    print("=" * 72)
    print("   KUBER DATA CORE -- ENTERPRISE FINANCIAL INTELLIGENCE WORKSTATION")
    print(f"   Active Service URL: {url}")
    print("   SEC EDGAR & FIBO Knowledge Graph Engine Online")
    print("=" * 72)

    def open_browser():
        time.sleep(1.2)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run("backend.main:app", host="127.0.0.1", port=port, reload=False)


if __name__ == "__main__":
    main()
