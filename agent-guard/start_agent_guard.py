#!/usr/bin/env python3
"""
Agent Guard Single Launcher.

Starts:
1. MongoDB connectivity verification
2. FastAPI Security Gateway Backend (http://localhost:8000)
3. React Vite Dashboard Frontend (http://localhost:5173)

Usage:
    python start_agent_guard.py
"""

import sys
import os
import subprocess
import time
import socket
import urllib.request
import signal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")


try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a local TCP port is already open."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0


def check_mongo():
    """Verify MongoDB is running."""
    print(" [1/3] Checking MongoDB connection (127.0.0.1:27017)...")
    if not is_port_in_use(27017):
        print("  WARNING: MongoDB is not responding on 127.0.0.1:27017.")
        print("           Please ensure mongod is started (or running in Docker).")
    else:
        print("  [OK] MongoDB is connected and active.")


def start_services():
    processes = []

    print("\n========================================================")
    print("              AGENT GUARD RUNTIME LAUNCHER              ")
    print("========================================================")

    check_mongo()

    # 1. Start Backend
    print("\n [2/3] Starting FastAPI Backend on http://localhost:8000 ...")
    if is_port_in_use(8000):
        print("  [OK] Port 8000 is already in use (FastAPI is likely running).")
    else:
        backend_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
            cwd=BACKEND_DIR
        )
        processes.append(backend_proc)
        print("  [OK] FastAPI Backend process launched.")

    # 2. Start Frontend
    print("\n [3/3] Starting React Dashboard Frontend on http://localhost:5173 ...")
    if is_port_in_use(5173):
        print("  [OK] Port 5173 is already in use (Frontend is likely running).")
    else:
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        frontend_proc = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=FRONTEND_DIR
        )
        processes.append(frontend_proc)
        print("  [OK] Vite Frontend process launched.")

    print("\n========================================================")
    print("             AGENT GUARD IS READY FOR USE               ")
    print("========================================================")
    print("  * Backend API:      http://localhost:8000")
    print("  * Live Dashboard:   http://localhost:5173")
    print("  * Antigravity Hook: Enabled in .agents/hooks.json")
    print("--------------------------------------------------------")
    print("  HOW TO USE:")
    print("  1. Open Antigravity and enter any natural language task.")
    print("  2. Agent Guard will automatically capture the goal,")
    print("     generate the security policy, and monitor all actions.")
    print("  3. View live security decisions on the Dashboard.")
    print("========================================================\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down Agent Guard processes...")
        for proc in processes:
            proc.terminate()
        sys.exit(0)


if __name__ == "__main__":
    start_services()
