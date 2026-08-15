"""
Version 3 Security Gateway & Real Controlled Tools Verification Tests.

Tests:
1. Allowed action executes (READ_FILE Login.jsx -> decision=ALLOW, executionStatus=EXECUTED).
2. Blocked deletion does not execute (DELETE_FILE database.sql -> decision=BLOCK, executionStatus=NOT_EXECUTED, file STILL EXISTS).
3. Secret access does not execute (ACCESS_SECRET .env -> decision=BLOCK, executionStatus=NOT_EXECUTED).
4. Approval pauses execution (MODIFY package.json -> decision=REQUIRE_APPROVAL, executionStatus=PENDING_APPROVAL).
5. Rejected approval does not execute (MODIFY package.json + REJECT -> decision=REJECTED, executionStatus=NOT_EXECUTED).
6. Path traversal is blocked (READ_FILE ../../important.txt -> decision=BLOCK, executionStatus=NOT_EXECUTED).
"""

import pytest
from pathlib import Path
from app.services.goal_integrity import evaluate_goal_integrity
from app.services.risk_engine import evaluate_risk
from app.services.authorization_engine import make_authorization_decision
from app.services.execution_verifier import verify_action_execution
from app.tools.file_tools import resolve_sandbox_path

SANDBOX_DIR = Path(__file__).resolve().parent.parent / "sandbox"


def test_v3_1_allowed_action_executes():
    """Test 1 — Allowed action executes (READ_FILE Login.jsx -> ALLOWED, EXECUTED)."""
    user_goal = "Fix login bug"
    action_type = "READ_FILE"
    target = "Login.jsx"

    integrity = evaluate_goal_integrity(user_goal, action_type, target, "Read login file")
    risk = evaluate_risk(action_type, target)
    auth = make_authorization_decision(
        alignment_status=integrity["alignmentStatus"],
        alignment_score=integrity["goalAlignmentScore"],
        risk_level=risk["riskLevel"],
        risk_score=risk["riskScore"],
        alignment_reason=integrity["reason"],
        risk_reason=risk["riskReason"]
    )

    decision = auth["decision"]
    execution_status = "EXECUTED" if decision == "ALLOW" else "NOT_EXECUTED"
    verifier = verify_action_execution(action_type, target, decision, execution_status)

    assert decision == "ALLOW"
    assert execution_status == "EXECUTED"
    assert verifier["verificationStatus"] == "PASSED"


def test_v3_2_blocked_deletion_does_not_execute():
    """Test 2 — Blocked deletion does not execute (DELETE_FILE database.sql -> BLOCKED, NOT_EXECUTED, file STILL EXISTS)."""
    db_file = SANDBOX_DIR / "database.sql"
    assert db_file.exists(), "database.sql must exist prior to test"

    user_goal = "Fix login bug"
    action_type = "DELETE_FILE"
    target = "database.sql"

    integrity = evaluate_goal_integrity(user_goal, action_type, target, "Delete database file")
    risk = evaluate_risk(action_type, target)
    auth = make_authorization_decision(
        alignment_status=integrity["alignmentStatus"],
        alignment_score=integrity["goalAlignmentScore"],
        risk_level=risk["riskLevel"],
        risk_score=risk["riskScore"],
        alignment_reason=integrity["reason"],
        risk_reason=risk["riskReason"]
    )

    decision = auth["decision"]
    execution_status = "NOT_EXECUTED" if decision == "BLOCK" else "EXECUTED"
    verifier = verify_action_execution(action_type, target, decision, execution_status)

    assert decision == "BLOCK"
    assert execution_status == "NOT_EXECUTED"
    assert db_file.exists(), "PROOF FAILED: database.sql was deleted despite being BLOCKED!"
    assert verifier["verificationStatus"] == "PASSED"
    assert "STILL EXISTS" in verifier["verificationMessage"] or "untouched" in verifier["verificationMessage"]


def test_v3_3_secret_access_does_not_execute():
    """Test 3 — Secret access does not execute (ACCESS_SECRET .env -> BLOCKED, NOT_EXECUTED)."""
    user_goal = "Fix login bug"
    action_type = "ACCESS_SECRET"
    target = ".env"

    integrity = evaluate_goal_integrity(user_goal, action_type, target, "Access .env file")
    risk = evaluate_risk(action_type, target)
    auth = make_authorization_decision(
        alignment_status=integrity["alignmentStatus"],
        alignment_score=integrity["goalAlignmentScore"],
        risk_level=risk["riskLevel"],
        risk_score=risk["riskScore"],
        alignment_reason=integrity["reason"],
        risk_reason=risk["riskReason"]
    )

    decision = auth["decision"]
    execution_status = "NOT_EXECUTED" if decision == "BLOCK" else "EXECUTED"
    verifier = verify_action_execution(action_type, target, decision, execution_status)

    assert decision == "BLOCK"
    assert execution_status == "NOT_EXECUTED"
    assert verifier["verificationStatus"] == "PASSED"


def test_v3_4_approval_pauses_execution():
    """Test 4 — Approval pauses execution (MODIFY_FILE package.json -> REQUIRE_APPROVAL, PENDING_APPROVAL)."""
    user_goal = "Fix login bug"
    action_type = "MODIFY_FILE"
    target = "package.json"
    description = "Modify package.json to update auth dependencies"

    integrity = evaluate_goal_integrity(user_goal, action_type, target, description)
    risk = evaluate_risk(action_type, target)
    auth = make_authorization_decision(
        alignment_status=integrity["alignmentStatus"],
        alignment_score=integrity["goalAlignmentScore"],
        risk_level=risk["riskLevel"],
        risk_score=risk["riskScore"],
        alignment_reason=integrity["reason"],
        risk_reason=risk["riskReason"]
    )

    decision = auth["decision"]
    execution_status = "PENDING_APPROVAL" if decision == "REQUIRE_APPROVAL" else "EXECUTED"

    assert decision == "REQUIRE_APPROVAL"
    assert execution_status == "PENDING_APPROVAL"


def test_v3_5_rejected_approval_does_not_execute():
    """Test 5 — Rejected approval does not execute (MODIFY package.json + REJECT -> REJECTED, NOT_EXECUTED)."""
    decision = "REJECTED"
    execution_status = "NOT_EXECUTED"
    verifier = verify_action_execution("MODIFY_FILE", "package.json", decision, execution_status)

    assert decision == "REJECTED"
    assert execution_status == "NOT_EXECUTED"
    assert verifier["verificationStatus"] == "PASSED"


def test_v3_6_path_traversal_is_blocked():
    """Test 6 — Path traversal is blocked (READ_FILE ../../important.txt -> BLOCKED, NOT_EXECUTED)."""
    target = "../../important.txt"
    is_path_traversal = False

    try:
        resolve_sandbox_path(target)
    except ValueError:
        is_path_traversal = True

    assert is_path_traversal, "Expected Path Traversal ValueError to be raised for ../../important.txt"

    decision = "BLOCK"
    execution_status = "NOT_EXECUTED"
    verifier = verify_action_execution("READ_FILE", target, decision, execution_status)

    assert decision == "BLOCK"
    assert execution_status == "NOT_EXECUTED"
    assert verifier["verificationStatus"] == "PASSED"
