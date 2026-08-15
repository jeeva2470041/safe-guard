"""
Version 5 Tests — Multi-Step Goal Drift, Cumulative Risk, Automatic Pause, and Goal Versioning.
"""

import pytest
from app.services.goal_drift import detect_goal_drift, get_drift_level, calculate_rolling_integrity
from app.services.risk_engine import evaluate_risk, evaluate_cumulative_risk, get_cumulative_risk_level
from app.services.security_gateway import classify_action
from app.services.authorization_engine import make_authorization_decision


def test_v5_1_multi_step_goal_drift():
    """Test 1: Progressive drift detection across action trajectory."""
    goal_policy = {
        "allowedScope": ["frontend components", "Navbar.jsx", "Hero.jsx", "styles.css"],
        "restrictedScope": ["backend", "server.js", "database.sql", ".env"],
        "constraints": ["Do not modify backend", "Do not access secrets"]
    }

    # Action 1: Aligned component read
    act1 = {
        "actionType": "READ_FILE",
        "target": "Navbar.jsx",
        "description": "Read Navbar component",
        "goalAlignmentScore": 95,
        "decision": "ALLOW"
    }
    drift1 = detect_goal_drift(goal_policy, [], act1)
    assert drift1["driftScore"] <= 20
    assert drift1["driftLevel"] == "NORMAL"

    # Action 2: Aligned CSS edit
    act2 = {
        "actionType": "MODIFY_FILE",
        "target": "styles.css",
        "description": "Update dark theme styles",
        "goalAlignmentScore": 90,
        "decision": "ALLOW"
    }
    drift2 = detect_goal_drift(goal_policy, [act1], act2)
    assert drift2["driftScore"] <= 20
    assert drift2["driftLevel"] == "NORMAL"

    # Action 3: Drift towards backend
    act3 = {
        "actionType": "MODIFY_FILE",
        "target": "server.js",
        "description": "Modify server backend endpoints",
        "goalAlignmentScore": 30,
        "decision": "BLOCK"
    }
    drift3 = detect_goal_drift(goal_policy, [act1, act2], act3)
    assert drift3["driftScore"] >= 60
    assert drift3["driftLevel"] in ("HIGH", "CRITICAL")
    assert drift3["driftDetected"] is True


def test_v5_2_cumulative_risk_escalation():
    """Test 2: Cumulative risk escalates with consecutive high-risk actions."""
    # Action 1: Low risk read
    risk1 = evaluate_risk("READ_FILE", "Navbar.jsx")
    cum1 = evaluate_cumulative_risk([], risk1)
    assert cum1["cumulativeRiskScore"] <= 30
    assert cum1["cumulativeRiskLevel"] == "LOW"

    # Action 2: Medium risk modify
    risk2 = evaluate_risk("MODIFY_FILE", "Hero.jsx")
    cum2 = evaluate_cumulative_risk([{"riskScore": risk1["riskScore"], "decision": "ALLOW"}], risk2)
    assert cum2["cumulativeRiskLevel"] in ("LOW", "MODERATE")

    # Action 3: Critical risk secret access
    risk3 = evaluate_risk("ACCESS_FILE", ".env")
    cum3 = evaluate_cumulative_risk(
        [
            {"riskScore": risk1["riskScore"], "decision": "ALLOW", "riskLevel": "LOW"},
            {"riskScore": risk2["riskScore"], "decision": "ALLOW", "riskLevel": "MEDIUM"}
        ],
        risk3
    )
    assert cum3["cumulativeRiskScore"] >= 75
    assert cum3["cumulativeRiskLevel"] == "CRITICAL"


def test_v5_3_action_classification():
    """Test 3: Verify standard V5 action classification."""
    # Productive: High alignment, low risk
    c1 = classify_action(alignment_score=95, risk_level="LOW", action_type="WRITE_FILE", has_violations=False, target="Hero.jsx")
    assert c1 == "PRODUCTIVE"

    # Dangerous: Critical risk or secrets
    c2 = classify_action(alignment_score=10, risk_level="CRITICAL", action_type="ACCESS_ENV", has_violations=True, target=".env")
    assert c2 == "DANGEROUS"

    # Relevant: Safe reads
    c3 = classify_action(alignment_score=70, risk_level="LOW", action_type="READ_FILE", has_violations=False, target="config.json")
    assert c3 == "RELEVANT"

    # Unrelated: Low alignment
    c4 = classify_action(alignment_score=25, risk_level="HIGH", action_type="MODIFY_FILE", has_violations=False, target="server.js")
    assert c4 == "UNRELATED"


def test_v5_4_rolling_integrity():
    """Test 4: Rolling integrity degrades smoothly as unaligned actions occur."""
    history = [
        {"goalAlignmentScore": 95},
        {"goalAlignmentScore": 90},
        {"goalAlignmentScore": 88},
        {"goalAlignmentScore": 40},
        {"goalAlignmentScore": 15},
    ]
    rolling = calculate_rolling_integrity(history)
    assert rolling < 70.0
