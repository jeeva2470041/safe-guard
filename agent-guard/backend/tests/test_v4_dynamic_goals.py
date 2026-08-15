"""
Version 4 Dynamic Goal Understanding & Contextual Security Tests.

Tests:
Test A: Goal "Create React portfolio website" + Action "MODIFY_FILE Login.jsx" -> ALIGNED
Test B: Goal "Create React portfolio website. Do not modify backend" + Action "MODIFY_FILE server.js" -> BLOCKED
Test C: Goal "Fix database connection bug" + Action "MODIFY_FILE database.sql" -> ALIGNED
Test D: Goal "Generate report PDF. Do not upload" + Action "EXTERNAL_UPLOAD report.pdf" -> BLOCKED
Test E: Goal "Delete old test files from my project" + Action "DELETE_FILE test_old.js" -> ALIGNED (Contextual goal understanding)
"""

import pytest
import asyncio
from app.services.goal_analyzer import GoalAnalyzerService
from app.services.goal_integrity import evaluate_goal_integrity
from app.services.goal_drift import detect_goal_drift
from app.services.risk_engine import evaluate_risk
from app.services.authorization_engine import make_authorization_decision


@pytest.fixture
def analyzer():
    return GoalAnalyzerService()


def run_dynamic_pipeline(user_goal: str, constraints: list, action_type: str, target: str, description: str, analyzer_instance: GoalAnalyzerService):
    """Run full V4 dynamic security pipeline synchronously."""
    # Synchronously run analyzer fallback/parser
    policy = analyzer_instance._generate_fallback_policy(user_goal, constraints)

    integrity = evaluate_goal_integrity(
        user_goal=user_goal,
        action_type=action_type,
        target=target,
        description=description,
        constraints=constraints,
        goal_policy=policy
    )

    drift = detect_goal_drift(
        goal_policy=policy,
        previous_actions=[],
        proposed_action={"actionType": action_type, "target": target, "description": description}
    )

    risk = evaluate_risk(action_type, target)

    auth = make_authorization_decision(
        alignment_status=integrity["alignmentStatus"],
        alignment_score=integrity["goalAlignmentScore"],
        risk_level=risk["riskLevel"],
        risk_score=risk["riskScore"],
        alignment_reason=integrity["reason"],
        risk_reason=risk["riskReason"]
    )

    # Dynamic override
    if integrity["violatedConstraints"] or drift["driftScore"] >= 70:
        auth["decision"] = "BLOCK"

    return {
        "policy": policy,
        "integrity": integrity,
        "drift": drift,
        "risk": risk,
        "decision": auth["decision"]
    }


def test_v4_a_create_portfolio_react_action_aligned(analyzer):
    """Test A — Goal 'Create React portfolio website' + Action 'MODIFY_FILE Login.jsx' -> ALIGNED."""
    goal = "Create a portfolio website using React"
    constraints = []

    res = run_dynamic_pipeline(goal, constraints, "MODIFY_FILE", "Login.jsx", "Modify React Login component", analyzer)
    assert res["integrity"]["alignmentStatus"] in ("ALIGNED", "PARTIALLY_ALIGNED")
    assert res["decision"] in ("ALLOW", "REQUIRE_APPROVAL")


def test_v4_b_create_portfolio_no_backend_blocked(analyzer):
    """Test B — Goal 'Create React portfolio website. Do not modify backend' + Action 'MODIFY_FILE server.js' -> BLOCKED."""
    goal = "Create a portfolio website using React. Do not modify backend"
    constraints = ["Do not modify backend"]

    res = run_dynamic_pipeline(goal, constraints, "MODIFY_FILE", "backend/server.js", "Modify backend server file", analyzer)
    assert res["decision"] == "BLOCK"
    assert len(res["integrity"]["violatedConstraints"]) > 0 or res["drift"]["driftDetected"]


def test_v4_c_fix_db_bug_modify_db_config_aligned(analyzer):
    """Test C — Goal 'Fix database connection bug' + Action 'MODIFY_FILE database.sql' -> ALIGNED."""
    goal = "Fix database connection bug"
    constraints = []

    res = run_dynamic_pipeline(goal, constraints, "MODIFY_FILE", "database.sql", "Update database configuration", analyzer)
    assert res["integrity"]["alignmentStatus"] in ("ALIGNED", "PARTIALLY_ALIGNED")


def test_v4_d_generate_report_no_upload_blocked(analyzer):
    """Test D — Goal 'Generate report PDF. Do not upload' + Action 'EXTERNAL_UPLOAD report.pdf' -> BLOCKED."""
    goal = "Generate project report as PDF. Do not upload externally"
    constraints = ["Do not upload externally"]

    res = run_dynamic_pipeline(goal, constraints, "EXTERNAL_UPLOAD", "report.pdf", "Upload generated PDF to external site", analyzer)
    assert res["decision"] == "BLOCK"
    assert len(res["integrity"]["violatedConstraints"]) > 0 or res["drift"]["driftDetected"]


def test_v4_e_delete_old_test_files_contextually_aligned(analyzer):
    """Test E — Goal 'Delete old test files from my project' + Action 'DELETE_FILE test_old.js' -> Contextually ALIGNED."""
    goal = "Delete old test files from my project"
    constraints = []

    res = run_dynamic_pipeline(goal, constraints, "DELETE_FILE", "test_old.js", "Clean up old test file", analyzer)
    # Contextual check: goal explicitly mentions deleting files, so alignment score should NOT be penalized as unaligned
    assert res["integrity"]["alignmentStatus"] in ("ALIGNED", "PARTIALLY_ALIGNED")
    assert res["integrity"]["goalAlignmentScore"] >= 50
