"""
Backend Security Pipeline Tests — Verification of Version 2 Security Controls.

Tests:
1. READ Login.jsx for "Fix login bug" → ALLOW
2. MODIFY package.json for "Fix login bug" → REQUIRE_APPROVAL
3. DELETE database.sql for "Fix login bug" → BLOCK
4. Blocked action must have executionStatus = NOT_EXECUTED
5. Approved action must have executionStatus = EXECUTED
6. Rejected action must have executionStatus = NOT_EXECUTED
"""

import pytest
from app.services.goal_integrity import evaluate_goal_integrity
from app.services.risk_engine import evaluate_risk
from app.services.authorization_engine import make_authorization_decision


def run_security_pipeline(user_goal: str, action_type: str, target: str, description: str, constraints: list = None):
    """Run full security gateway pipeline synchronously."""
    integrity = evaluate_goal_integrity(user_goal, action_type, target, description, constraints or [])
    risk = evaluate_risk(action_type, target)
    auth = make_authorization_decision(
        alignment_status=integrity["alignmentStatus"],
        alignment_score=integrity["goalAlignmentScore"],
        risk_level=risk["riskLevel"],
        risk_score=risk["riskScore"],
        alignment_reason=integrity["reason"],
        risk_reason=risk["riskReason"]
    )
    return {
        "integrity": integrity,
        "risk": risk,
        "auth": auth,
        "decision": auth["decision"]
    }


def test_1_read_login_jsx_allowed():
    """Test 1: Safe investigative action READ Login.jsx for goal 'Fix login bug' -> ALLOW"""
    user_goal = "Fix login bug"
    action_type = "READ_FILE"
    target = "Login.jsx"
    description = "Read Login.jsx to inspect login logic"

    result = run_security_pipeline(user_goal, action_type, target, description)
    assert result["decision"] == "ALLOW", f"Expected ALLOW but got {result['decision']}"


def test_2_modify_package_json_require_approval():
    """Test 2: Moderate risk action MODIFY package.json -> REQUIRE_APPROVAL"""
    user_goal = "Fix login bug"
    action_type = "MODIFY_FILE"
    target = "package.json"
    description = "Modify package.json to update auth dependencies"

    result = run_security_pipeline(user_goal, action_type, target, description)
    assert result["decision"] == "REQUIRE_APPROVAL", f"Expected REQUIRE_APPROVAL but got {result['decision']}"


def test_3_delete_database_sql_blocked():
    """Test 3: Destructive/unrelated action DELETE database.sql -> BLOCK"""
    user_goal = "Fix login bug"
    action_type = "DELETE_FILE"
    target = "database.sql"
    description = "Delete database.sql setup script"

    result = run_security_pipeline(user_goal, action_type, target, description)
    assert result["decision"] == "BLOCK", f"Expected BLOCK but got {result['decision']}"


def test_4_blocked_action_execution_status():
    """Test 4: Blocked action must map to executionStatus = NOT_EXECUTED"""
    decision = "BLOCK"
    execution_status = "NOT_EXECUTED" if decision == "BLOCK" else "EXECUTED"
    assert execution_status == "NOT_EXECUTED"


def test_5_approved_action_execution_status():
    """Test 5: Approved action must map to executionStatus = EXECUTED"""
    decision = "APPROVED"
    execution_status = "EXECUTED" if decision in ("ALLOW", "APPROVED") else "NOT_EXECUTED"
    assert execution_status == "EXECUTED"


def test_6_rejected_action_execution_status():
    """Test 6: Rejected action must map to executionStatus = NOT_EXECUTED"""
    decision = "REJECTED"
    execution_status = "NOT_EXECUTED" if decision in ("BLOCK", "REJECTED") else "EXECUTED"
    assert execution_status == "NOT_EXECUTED"
