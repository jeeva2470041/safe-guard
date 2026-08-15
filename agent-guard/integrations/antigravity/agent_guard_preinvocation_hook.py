#!/usr/bin/env python3
"""
Agent Guard PreInvocation Hook Bridge for Google Antigravity.

This hook runs BEFORE the model is called. It extracts the user's natural language
prompt from the Antigravity transcript, sends it to Agent Guard to automatically
synthesize a dynamic Goal Policy, creates/updates the goal version, and associates
the conversationId with the goal in MongoDB.
"""

import sys
import os
import json
import re
import urllib.request
import urllib.error

AGENT_GUARD_SESSION_API = "http://127.0.0.1:8000/api/agent/session/start"
TIMEOUT_SECONDS = 10


def extract_prompt_from_transcript(transcript_path: str) -> str:
    """Extract the latest user prompt reliably in ~1ms from transcript.jsonl."""
    if not transcript_path or not os.path.exists(transcript_path):
        return ""

    try:
        with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in reversed(f.readlines()):
                line = line.strip()
                if not line:
                    continue
                try:
                    step = json.loads(line)
                    if step.get("type") == "USER_INPUT" and step.get("content"):
                        content = step.get("content", "")
                        match = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", content, re.DOTALL)
                        if match:
                            return match.group(1).strip()
                        return content.strip()
                except Exception:
                    continue
    except Exception:
        pass

    return ""


def main():
    try:
        input_raw = sys.stdin.read()
        if not input_raw or not input_raw.strip():
            print(json.dumps({}))
            return

        payload = json.loads(input_raw)

        conversation_id = payload.get("conversationId", "default-session")
        transcript_path = payload.get("transcriptPath", "")
        workspace_paths = payload.get("workspacePaths", [])
        invocation_num = payload.get("invocationNum", 1)

        # Extract prompt from transcript
        user_prompt = extract_prompt_from_transcript(transcript_path)

        if not user_prompt:
            # Fallback if transcript hasn't been flushed yet
            user_prompt = payload.get("userPrompt") or payload.get("prompt") or ""

        if not user_prompt:
            # Nothing to register yet
            print(json.dumps({}))
            return

        # Register session & auto-create Goal Policy
        start_payload = {
            "conversationId": conversation_id,
            "sessionId": conversation_id,
            "userPrompt": user_prompt,
            "workspacePaths": workspace_paths,
            "invocationNum": invocation_num,
            "agent": "antigravity"
        }

        req_data = json.dumps(start_payload).encode("utf-8")
        req = urllib.request.Request(
            AGENT_GUARD_SESSION_API,
            data=req_data,
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            res_body = response.read().decode("utf-8")
            res_data = json.loads(res_body)

        # PreInvocation contract expects empty object or injectSteps
        print(json.dumps({}))

    except Exception:
        # PreInvocation must never break Antigravity execution if backend is offline
        print(json.dumps({}))


if __name__ == "__main__":
    main()
