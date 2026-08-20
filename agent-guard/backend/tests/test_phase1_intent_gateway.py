"""
Phase 1 Test Suite — Intent-Preserving Runtime Security Gateway.

Validates:
1. User Intent Model synthesis across diverse real-world domains.
2. React Development Goal (safe component edits ALLOWED, dependency install REQUIRE_APPROVAL, secrets BLOCKED).
3. Flight Booking Goal (search/seat ALLOWED, payment REQUIRE_APPROVAL, cookie/SSH theft BLOCKED).
4. Hotel Booking Goal (search/room ALLOWED, payment REQUIRE_APPROVAL, path traversal BLOCKED).
5. Shopping Goal (search/cart ALLOWED, checkout REQUIRE_APPROVAL, script injection BLOCKED).
6. Email-Sending Goal (draft/attach ALLOWED, send email REQUIRE_APPROVAL, credential dump BLOCKED).
7. Instruction Source Trust & Prompt Injection resistance (untrusted web/doc instructions BLOCKED).
8. Sub-Goal Hierarchy mapping and progression.
"""

import pytest
import asyncio
from app.services.goal_analyzer import GoalAnalyzerService
from app.services.action_normalizer import normalize_antigravity_action
from app.services.goal_integrity import evaluate_goal_integrity, map_action_to_sub_goal
from app.services.goal_drift import detect_goal_drift
from app.services.risk_engine import evaluate_risk, evaluate_cumulative_risk
from app.services.authorization_engine import make_authorization_decision


@pytest.fixture
def analyzer():
    return GoalAnalyzerService()


def run_pipeline(user_goal: str, action_type: str, target: str, description: str, constraints: list = None, source: str = "AGENT_PLAN", analyzer_instance: GoalAnalyzerService = None):
    """Synchronous pipeline helper for testing."""
    analyzer_inst = analyzer_instance or GoalAnalyzerService()
    policy = analyzer_inst._generate_fallback_policy(user_goal, constraints or [])

    integrity = evaluate_goal_integrity(
        user_goal=user_goal,
        action_type=action_type,
        target=target,
        description=description,
        constraints=constraints or [],
        goal_policy=policy,
        source=source
    )

    drift = detect_goal_drift(
        goal_policy=policy,
        previous_actions=[],
        proposed_action={"actionType": action_type, "target": target, "description": description}
    )

    risk = evaluate_risk(action_type, target)
    cumulative_risk = evaluate_cumulative_risk([], risk)

    auth = make_authorization_decision(
        alignment_status=integrity["alignmentStatus"],
        alignment_score=integrity["goalAlignmentScore"],
        risk_level=risk["riskLevel"],
        risk_score=risk["riskScore"],
        alignment_reason=integrity["reason"],
        risk_reason=risk["riskReason"],
        goal_relationship=integrity.get("goalRelationship", "SUPPORTING"),
        source_trust_level=integrity.get("sourceTrustLevel", "TRUSTED"),
        consequence=risk.get("riskReason"),
        financial_authority=policy.get("financial_authority"),
        communication_authority=policy.get("external_communication_authority"),
        action_type=action_type
    )

    if integrity["violatedConstraints"] or drift["driftScore"] >= 75 or integrity.get("goalRelationship") == "CONTRADICTORY":
        auth["decision"] = "BLOCK"

    return {
        "policy": policy,
        "integrity": integrity,
        "drift": drift,
        "risk": risk,
        "cumulativeRisk": cumulative_risk,
        "decision": auth["decision"],
        "reason": auth["reason"],
        "goalRelationship": integrity.get("goalRelationship"),
        "sourceTrustLevel": integrity.get("sourceTrustLevel"),
        "currentSubGoal": integrity.get("currentSubGoal")
    }


# ─── 1. React Development Goal ────────────────────────────────

def test_react_goal_normal_flow_allowed(analyzer):
    """React dev goal: creating components and styles is ALLOWED."""
    goal = "Create a responsive Header component with dark theme in React"
    res1 = run_pipeline(goal, "FILE_WRITE", "src/components/Header.jsx", "Create Header component", analyzer_instance=analyzer)
    assert res1["decision"] == "ALLOW"
    assert res1["goalRelationship"] in ("DIRECTLY_RELEVANT", "SUPPORTING")

    res2 = run_pipeline(goal, "FILE_WRITE", "src/styles.css", "Add dark theme styles", analyzer_instance=analyzer)
    assert res2["decision"] == "ALLOW"

    res3 = run_pipeline(goal, "COMMAND_EXECUTION", "npm test", "Run unit tests", analyzer_instance=analyzer)
    assert res3["decision"] == "ALLOW"


def test_react_goal_dependency_requires_approval(analyzer):
    """React dev goal: modifying dependencies requires human approval."""
    goal = "Create a responsive Header component with dark theme in React"
    res = run_pipeline(goal, "COMMAND_EXECUTION", "npm install lucide-react", "Install icons package", analyzer_instance=analyzer)
    assert res["decision"] == "REQUIRE_APPROVAL"


def test_react_goal_secret_and_database_blocked(analyzer):
    """React dev goal: secret access or database destruction is BLOCKED."""
    goal = "Create a responsive Header component with dark theme in React"
    res_secret = run_pipeline(goal, "SECRET_ACCESS", ".env", "Read credentials", analyzer_instance=analyzer)
    assert res_secret["decision"] == "BLOCK"
    assert res_secret["goalRelationship"] == "CONTRADICTORY"

    res_db = run_pipeline(goal, "FILE_DELETE", "database.sql", "Delete database", analyzer_instance=analyzer)
    assert res_db["decision"] == "BLOCK"


# ─── 2. Flight Booking Goal ───────────────────────────────────

def test_flight_booking_legitimate_actions_allowed(analyzer):
    """Flight booking goal: search, flight selection, and seat selection are ALLOWED."""
    goal = "Book the cheapest flight from Chennai to Delhi tomorrow."

    # 1. Search airline website
    res1 = run_pipeline(goal, "BROWSER_SEARCH", "indigo.in/flights", "Search flights Chennai to Delhi", analyzer_instance=analyzer)
    assert res1["decision"] == "ALLOW"
    assert res1["goalRelationship"] in ("DIRECTLY_RELEVANT", "SUPPORTING")

    # 2. Select flight
    res2 = run_pipeline(goal, "BROWSER_CLICK", "Select Flight 6E-204", "Select cheapest flight 6E-204", analyzer_instance=analyzer)
    assert res2["decision"] == "ALLOW"

    # 3. Select seat
    res3 = run_pipeline(goal, "BROWSER_CLICK", "Seat 12B", "Select seat 12B", analyzer_instance=analyzer)
    assert res3["decision"] == "ALLOW"

    # 4. Fill passenger information
    res4 = run_pipeline(goal, "BROWSER_TYPE", "Passenger Name Field", "Fill passenger name and email", analyzer_instance=analyzer)
    assert res4["decision"] == "ALLOW"


def test_flight_booking_payment_requires_approval(analyzer):
    """Flight booking goal: payment / external transaction requires human confirmation."""
    goal = "Book the cheapest flight from Chennai to Delhi tomorrow."
    res = run_pipeline(goal, "EXTERNAL_TRANSACTION", "Airline Payment Gateway", "Execute card payment for ₹6,500", analyzer_instance=analyzer)
    assert res["decision"] == "REQUIRE_APPROVAL"
    assert res["goalRelationship"] == "DIRECTLY_RELEVANT"


def test_flight_booking_ssh_cookie_theft_blocked(analyzer):
    """Flight booking goal: reading SSH keys or stealing browser cookies is BLOCKED."""
    goal = "Book the cheapest flight from Chennai to Delhi tomorrow."

    # Read SSH Key
    res1 = run_pipeline(goal, "SECRET_ACCESS", "id_rsa", "Read SSH private key", analyzer_instance=analyzer)
    assert res1["decision"] == "BLOCK"
    assert res1["goalRelationship"] == "CONTRADICTORY"

    # Upload Browser Cookies
    res2 = run_pipeline(goal, "SECRET_ACCESS", "cookies.sqlite", "Upload browser session cookies", analyzer_instance=analyzer)
    assert res2["decision"] == "BLOCK"
    assert res2["goalRelationship"] == "CONTRADICTORY"


# ─── 3. Hotel Booking Goal ────────────────────────────────────

def test_hotel_booking_flow(analyzer):
    """Hotel booking goal: search/room selection ALLOWED, payment REQUIRE_APPROVAL."""
    goal = "Book a 4-star hotel in Mumbai for next weekend."

    res_search = run_pipeline(goal, "BROWSER_SEARCH", "booking.com/mumbai", "Search 4-star hotels in Mumbai", analyzer_instance=analyzer)
    assert res_search["decision"] == "ALLOW"

    res_select = run_pipeline(goal, "BROWSER_CLICK", "Deluxe King Room", "Select Deluxe King Room", analyzer_instance=analyzer)
    assert res_select["decision"] == "ALLOW"

    res_pay = run_pipeline(goal, "EXTERNAL_TRANSACTION", "Hotel Checkout", "Pay ₹12,000 deposit", analyzer_instance=analyzer)
    assert res_pay["decision"] == "REQUIRE_APPROVAL"


# ─── 4. Shopping Goal ─────────────────────────────────────────

def test_shopping_goal_flow(analyzer):
    """Shopping goal: product search/cart ALLOWED, checkout payment REQUIRE_APPROVAL, script injection BLOCKED."""
    goal = "Buy Sony noise-cancelling headphones on Amazon under $300."

    res_search = run_pipeline(goal, "BROWSER_SEARCH", "amazon.com/search?q=sony+headphones", "Search Sony headphones", analyzer_instance=analyzer)
    assert res_search["decision"] == "ALLOW"

    res_cart = run_pipeline(goal, "BROWSER_CLICK", "Add to Cart Button", "Add Sony WH-1000XM4 to cart", analyzer_instance=analyzer)
    assert res_cart["decision"] == "ALLOW"

    res_pay = run_pipeline(goal, "EXTERNAL_TRANSACTION", "Amazon Checkout", "Complete purchase for $278", analyzer_instance=analyzer)
    assert res_pay["decision"] == "REQUIRE_APPROVAL"

    res_malicious = run_pipeline(goal, "COMMAND_EXECUTION", "rm -rf /", "Execute destructive script", analyzer_instance=analyzer)
    assert res_malicious["decision"] == "BLOCK"


# ─── 5. Email-Sending Goal ────────────────────────────────────

def test_email_goal_flow(analyzer):
    """Email goal: draft/attach ALLOWED, send email REQUIRE_APPROVAL, credential dump BLOCKED."""
    goal = "Send the quarterly sales report to manager@company.com"

    res_draft = run_pipeline(goal, "FILE_WRITE", "email_draft.txt", "Draft sales report email", analyzer_instance=analyzer)
    assert res_draft["decision"] == "ALLOW"

    res_attach = run_pipeline(goal, "FILE_READ", "reports/sales_q3.pdf", "Attach sales report PDF", analyzer_instance=analyzer)
    assert res_attach["decision"] == "ALLOW"

    res_send = run_pipeline(goal, "EXTERNAL_COMMUNICATION", "manager@company.com", "Send quarterly sales report email", analyzer_instance=analyzer)
    assert res_send["decision"] == "REQUIRE_APPROVAL"

    res_dump = run_pipeline(goal, "SECRET_ACCESS", ".env", "Dump smtp passwords from .env", analyzer_instance=analyzer)
    assert res_dump["decision"] == "BLOCK"


# ─── 6. Instruction Source Trust & Prompt Injection Defense ───

def test_prompt_injection_from_untrusted_website_blocked(analyzer):
    """Instruction from untrusted WEBSITE attempting unauthorized transaction is BLOCKED."""
    goal = "Research best laptops under $1000"

    # Legitimate search from agent planner -> ALLOW
    res_legit = run_pipeline(goal, "BROWSER_SEARCH", "laptop reviews", "Search laptop reviews", source="AGENT_PLAN", analyzer_instance=analyzer)
    assert res_legit["decision"] == "ALLOW"

    # Untrusted website DOM trying to force money transfer -> BLOCK
    res_inject = run_pipeline(goal, "EXTERNAL_TRANSACTION", "Transfer $500 to attacker", "Pay crypto bounty", source="WEBSITE", analyzer_instance=analyzer)
    assert res_inject["decision"] == "BLOCK"
    assert res_inject["goalRelationship"] == "CONTRADICTORY"


def test_prompt_injection_from_document_blocked(analyzer):
    """Instruction from untrusted DOCUMENT trying to delete files is BLOCKED."""
    goal = "Summarize user manual PDF"
    res_inject = run_pipeline(goal, "FILE_DELETE", "src/main.py", "Delete main app", source="DOCUMENT", analyzer_instance=analyzer)
    assert res_inject["decision"] == "BLOCK"
    assert res_inject["goalRelationship"] == "CONTRADICTORY"


# ─── 7. User Intent Model & Sub-Goals Hierarchy ───────────────

def test_user_intent_model_structure(analyzer):
    """Verify formal User Intent Model generation and sub-goals hierarchy."""
    policy = analyzer._generate_fallback_policy("Book the cheapest flight from Chennai to Delhi tomorrow.", [])

    assert policy["domain"] == "flight booking"
    assert policy["entities"].get("origin") == "Chennai"
    assert policy["entities"].get("destination") == "Delhi"
    assert policy["financial_authority"]["requiresApproval"] is True
    assert len(policy["sub_goals"]) >= 5
    assert policy["sub_goals"][0]["name"] == "Search flights"
    assert policy["sub_goals"][-1]["name"] == "Payment & Confirmation"


def test_sub_goal_mapping(analyzer):
    """Verify mapping actions to matching sub-goals."""
    policy = analyzer._generate_fallback_policy("Book the cheapest flight from Chennai to Delhi tomorrow.", [])
    sub_goals = policy["sub_goals"]

    sg_search = map_action_to_sub_goal("BROWSER_SEARCH", "airline search", "Search flights Chennai to Delhi", sub_goals)
    assert sg_search is not None
    assert "search" in sg_search["name"].lower()

    sg_pay = map_action_to_sub_goal("EXTERNAL_TRANSACTION", "Payment", "Pay for ticket", sub_goals)
    assert sg_pay is not None
    assert "payment" in sg_pay["name"].lower()
