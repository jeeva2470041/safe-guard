"""
Policy Tiering Tests — Verification that simple routine tasks are automatically allowed
while complex/high-impact tasks require human approval and critical operations are blocked.
"""

import pytest
from app.services.goal_integrity import evaluate_goal_integrity
from app.services.risk_engine import evaluate_risk
from app.services.authorization_engine import make_authorization_decision


def run_pipeline(user_goal: str, action_type: str, target: str, description: str, constraints: list = None):
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
        "decision": auth["decision"],
        "reason": auth["reason"]
    }


def test_simple_file_write_allowed():
    """Simple task: Creating or editing a standard component/file -> ALLOW (No human approval needed)."""
    res = run_pipeline(
        user_goal="Create a header component for the website",
        action_type="FILE_WRITE",
        target="src/components/Header.jsx",
        description="Write Header.jsx component"
    )
    assert res["decision"] == "ALLOW", f"Expected ALLOW for simple file write, got {res['decision']}"


def test_simple_diagnostic_command_allowed():
    """Simple task: Running git status or inspection command -> ALLOW (No human approval needed)."""
    res = run_pipeline(
        user_goal="Check project status and test build",
        action_type="COMMAND_EXECUTION",
        target="git status",
        description="Check git status"
    )
    assert res["decision"] == "ALLOW", f"Expected ALLOW for diagnostic command, got {res['decision']}"


def test_simple_test_command_allowed():
    """Simple task: Running pytest or npm test -> ALLOW (No human approval needed)."""
    res = run_pipeline(
        user_goal="Run backend unit tests",
        action_type="COMMAND_EXECUTION",
        target="pytest -v",
        description="Run test suite"
    )
    assert res["decision"] == "ALLOW", f"Expected ALLOW for test command, got {res['decision']}"


def test_simple_scratch_file_delete_allowed():
    """Simple task: Deleting a requested scratch file (e.g., ayya.txt) -> ALLOW when requested."""
    res = run_pipeline(
        user_goal="Delete the temporary file ayya.txt",
        action_type="FILE_DELETE",
        target="ayya.txt",
        description="Delete temporary file ayya.txt"
    )
    assert res["decision"] == "ALLOW", f"Expected ALLOW for requested scratch file delete, got {res['decision']}"


def test_complex_package_installation_requires_approval():
    """Complex task: Installing external packages (npm install) -> REQUIRE_APPROVAL."""
    res = run_pipeline(
        user_goal="Add authentication feature",
        action_type="COMMAND_EXECUTION",
        target="npm install jsonwebtoken bcrypt",
        description="Install authentication dependencies"
    )
    assert res["decision"] == "REQUIRE_APPROVAL", f"Expected REQUIRE_APPROVAL for npm install, got {res['decision']}"


def test_complex_package_json_modification_requires_approval():
    """Complex task: Modifying manifest package.json -> REQUIRE_APPROVAL."""
    res = run_pipeline(
        user_goal="Update project dependencies",
        action_type="FILE_WRITE",
        target="package.json",
        description="Modify package.json dependencies"
    )
    assert res["decision"] == "REQUIRE_APPROVAL", f"Expected REQUIRE_APPROVAL for package.json edit, got {res['decision']}"


def test_complex_git_force_reset_requires_approval():
    """Complex task: Destructive git reset --hard -> REQUIRE_APPROVAL."""
    res = run_pipeline(
        user_goal="Clean working directory",
        action_type="COMMAND_EXECUTION",
        target="git reset --hard HEAD~1",
        description="Reset git history"
    )
    assert res["decision"] == "REQUIRE_APPROVAL", f"Expected REQUIRE_APPROVAL for git reset --hard, got {res['decision']}"


def test_critical_env_secret_access_blocked():
    """Critical task: Accessing secret .env file -> BLOCK."""
    res = run_pipeline(
        user_goal="Fix login bug",
        action_type="ACCESS_SECRET",
        target=".env",
        description="Read environment secrets"
    )
    assert res["decision"] == "BLOCK", f"Expected BLOCK for .env access, got {res['decision']}"


def test_critical_database_destruction_blocked():
    """Critical task: Deleting database.sql -> BLOCK."""
    res = run_pipeline(
        user_goal="Update website",
        action_type="DELETE_FILE",
        target="database.sql",
        description="Delete database setup script"
    )
    assert res["decision"] == "BLOCK", f"Expected BLOCK for database.sql delete, got {res['decision']}"
