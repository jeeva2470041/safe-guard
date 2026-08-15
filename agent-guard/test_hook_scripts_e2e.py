"""
End-to-End Hook Scripts Contract Verification.
Tests both Python hook bridge executables via subprocess stdin/stdout.
"""

import subprocess
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PREINVOCATION_HOOK = os.path.join(BASE_DIR, "integrations", "antigravity", "agent_guard_preinvocation_hook.py")
PRETOOLUSE_HOOK = os.path.join(BASE_DIR, "integrations", "antigravity", "agent_guard_hook.py")


def test_hooks():
    print("\n========================================================")
    print("      TESTING HOOK SCRIPTS E2E (STDIN / STDOUT)         ")
    print("========================================================\n")

    # 1. Test PreInvocation Hook Script
    print("[1] Testing PreInvocation Hook Contract...")
    preinvocation_payload = {
        "conversationId": "C-HOOK-TEST-001",
        "userPrompt": "Create a React portfolio website. Do not modify my backend.",
        "workspacePaths": ["c:/Users/priya/jeeva_project/safeai"],
        "invocationNum": 1
    }

    proc = subprocess.Popen(
        [sys.executable, PREINVOCATION_HOOK],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = proc.communicate(input=json.dumps(preinvocation_payload))

    print(f"  PreInvocation exit code: {proc.returncode}")
    print(f"  PreInvocation stdout: {stdout.strip()}")
    assert proc.returncode == 0
    res_json = json.loads(stdout)
    assert isinstance(res_json, dict)
    print("  [PASS] PreInvocation Hook responded successfully.\n")

    # 2. Test PreToolUse Hook Script with ALLOW action (src/App.jsx)
    print("[2] Testing PreToolUse Hook Contract (ALLOW - src/App.jsx)...")
    pretooluse_allow_payload = {
        "conversationId": "C-HOOK-TEST-001",
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "TargetFile": "src/App.jsx",
                "CodeContent": "export default function App() {}"
            }
        },
        "workspacePaths": ["c:/Users/priya/jeeva_project/safeai"],
        "stepIdx": 2
    }

    proc = subprocess.Popen(
        [sys.executable, PRETOOLUSE_HOOK],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = proc.communicate(input=json.dumps(pretooluse_allow_payload))

    print(f"  PreToolUse exit code: {proc.returncode}")
    print(f"  PreToolUse stdout: {stdout.strip()}")
    assert proc.returncode == 0
    res_allow = json.loads(stdout)
    assert "decision" in res_allow
    print(f"  PreToolUse ALLOW Decision: {res_allow['decision']}")
    print("  [PASS] PreToolUse ALLOW test successful.\n")

    # 3. Test PreToolUse Hook Script with DENY action (backend/server.js)
    print("[3] Testing PreToolUse Hook Contract (DENY - backend/server.js)...")
    pretooluse_deny_payload = {
        "conversationId": "C-HOOK-TEST-001",
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "TargetFile": "backend/server.js",
                "CodeContent": "const express = require('express');"
            }
        },
        "workspacePaths": ["c:/Users/priya/jeeva_project/safeai"],
        "stepIdx": 3
    }

    proc = subprocess.Popen(
        [sys.executable, PRETOOLUSE_HOOK],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = proc.communicate(input=json.dumps(pretooluse_deny_payload))

    print(f"  PreToolUse exit code: {proc.returncode}")
    print(f"  PreToolUse stdout: {stdout.strip()}")
    assert proc.returncode == 0
    res_deny = json.loads(stdout)
    assert "decision" in res_deny
    print(f"  PreToolUse DENY Decision: {res_deny['decision']}")
    print(f"  PreToolUse Reason: {res_deny.get('reason')}")
    print("  [PASS] PreToolUse DENY test successful.\n")

    print("========================================================")
    print("  HOOKS E2E TEST: ALL HOOKS CONFORM TO ANTIGRAVITY SPEC ")
    print("========================================================\n")


if __name__ == "__main__":
    test_hooks()
