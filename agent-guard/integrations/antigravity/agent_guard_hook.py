#!/usr/bin/env python3
"""
Agent Guard PreToolUse Hook Bridge for Google Antigravity.

This hook receives Antigravity's proposed tool action on stdin, sends it to the
Agent Guard FastAPI Security Gateway for evaluation against the active Goal Policy,
and returns the authorization decision on stdout BEFORE the tool executes.
"""

import sys
import json
import urllib.request
import urllib.error

AGENT_GUARD_API = "http://127.0.0.1:8000/api/agent/intercept"
TIMEOUT_SECONDS = 10


def main():
    try:
        # Read Antigravity hook payload from stdin
        input_raw = sys.stdin.read()
        if not input_raw or not input_raw.strip():
            # If no input, allow by default
            print(json.dumps({"decision": "allow", "reason": "No tool call payload received."}))
            return

        payload = json.loads(input_raw)

        # Structure request for Agent Guard Intercept API
        intercept_request = {
            "toolCall": payload.get("toolCall", {}),
            "conversationId": payload.get("conversationId"),
            "sessionId": payload.get("conversationId"),
            "workspacePaths": payload.get("workspacePaths", []),
            "stepIdx": payload.get("stepIdx"),
            "agent": "antigravity"
        }

        # Send HTTP request to Agent Guard FastAPI
        req_data = json.dumps(intercept_request).encode("utf-8")
        req = urllib.request.Request(
            AGENT_GUARD_API,
            data=req_data,
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            res_body = response.read().decode("utf-8")
            res_data = json.loads(res_body)

            decision = res_data.get("decision", "allow")
            reason = res_data.get("reason", "Agent Guard evaluated tool call.")
            action_id = res_data.get("actionId")
            execution_status = res_data.get("executionStatus")

            # If action requires approval from the dashboard, block and poll until user approves/rejects on site
            if decision == "ask" or execution_status == "PENDING_APPROVAL":
                if action_id:
                    import time
                    poll_url = f"http://127.0.0.1:8000/api/actions/{action_id}"
                    max_wait_seconds = 180
                    poll_interval = 1.0
                    elapsed = 0.0
                    final_decision = "deny"
                    final_reason = f"[Agent Guard] Action {action_id} timed out awaiting approval on dashboard."

                    while elapsed < max_wait_seconds:
                        time.sleep(poll_interval)
                        elapsed += poll_interval
                        try:
                            poll_req = urllib.request.Request(poll_url, headers={"Content-Type": "application/json"})
                            with urllib.request.urlopen(poll_req, timeout=5) as poll_res:
                                poll_data = json.loads(poll_res.read().decode("utf-8"))
                                cur_dec = poll_data.get("decision")
                                cur_stat = poll_data.get("executionStatus")

                                if cur_dec == "APPROVED" or cur_stat == "EXECUTED":
                                    final_decision = "allow"
                                    final_reason = f"[Agent Guard] Action {action_id} approved by user on dashboard."
                                    break
                                elif cur_dec == "REJECTED" or cur_stat == "NOT_EXECUTED":
                                    final_decision = "deny"
                                    final_reason = f"[Agent Guard] Action {action_id} rejected by user on dashboard."
                                    break
                        except Exception:
                            pass

                    hook_response = {
                        "decision": final_decision,
                        "reason": final_reason
                    }
                    print(json.dumps(hook_response))
                    return

            # Output response matching Antigravity PreToolUse hook contract
            hook_response = {
                "decision": decision,  # allow | deny
                "reason": f"[Agent Guard] {reason}"
            }
            print(json.dumps(hook_response))

    except urllib.error.URLError as url_err:
        # Backend unavailable: In enforce mode, deny critical operations or warn
        err_msg = f"Agent Guard Security Gateway unreachable ({url_err.reason})."
        hook_response = {
            "decision": "ask",
            "reason": f"[Agent Guard Warning] {err_msg} Confirm tool execution?"
        }
        print(json.dumps(hook_response))

    except Exception as ex:
        # Fallback error response
        hook_response = {
            "decision": "ask",
            "reason": f"[Agent Guard] Interception hook error: {str(ex)}"
        }
        print(json.dumps(hook_response))


if __name__ == "__main__":
    main()
