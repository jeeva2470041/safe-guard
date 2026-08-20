"""
Goal Integrity Engine — Deterministic Goal Alignment & Intent Enforcement.

Evaluates whether a proposed action is necessary, relevant, and authorized
for accomplishing the user's overarching intent.

Phase 1 & Phase 2 Additions:
- Goal Relationship: DIRECTLY_RELEVANT | SUPPORTING | INDIRECTLY_RELEVANT | UNRELATED | CONTRADICTORY
- Action Necessity & required_for_goal determination
- Sub-Goal Mapping against hierarchical goal breakdown
- External Context Trust Boundary & Instruction Separator (Information vs. Instruction)
- Authority Boundaries (Financial, Communication, Personal Data)
- Real-World Task Support (Browser, APIs, Emails, Forms, Financial, MCP, Code, Commands)
"""

import re
from typing import Dict, Any, List, Optional, Tuple


def _extract_keywords(text: str) -> set:
    """Extract meaningful keywords from text, lowercased."""
    stop_words = {
        "the", "a", "an", "in", "my", "is", "to", "of", "and", "or",
        "for", "on", "at", "it", "do", "not", "be", "this", "that",
        "with", "from", "task", "agent", "please", "can", "you", "will", "all"
    }
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
    words = cleaned.split()
    return {w.strip() for w in words if w.strip() and w.strip() not in stop_words and len(w.strip()) > 1}


def classify_external_content(content: str, source: str = "WEBSITE") -> Dict[str, Any]:
    """
    Distinguish between factual INFORMATION (safe for reasoning)
    and imperative INSTRUCTIONS (must be vetted against user intent).
    """
    content_clean = (content or "").strip()
    content_lower = content_clean.lower()

    # Imperative directive markers
    instruction_markers = [
        "ignore previous", "ignore all", "upload your", "upload cookies", "send your", "export your",
        "enter your password", "give me access", "transfer", "delete file", "run command",
        "click here to pay", "select your preferred", "choose a seat", "enter passenger", "fill out",
        "confirm payment", "click next", "download and run", "execute"
    ]

    is_instruction = any(marker in content_lower for marker in instruction_markers) or content_clean.startswith((
        "Please ", "Select ", "Enter ", "Upload ", "Download ", "Ignore ", "Do not ", "Send ", "Delete "
    ))

    # Detect if adversarial / prompt injection
    is_adversarial = any(adv in content_lower for adv in (
        "ignore previous", "ignore user", "upload cookie", "browser cookie", "steal",
        "session cookie", "private key", "id_rsa", "dump .env", "transfer money to attacker",
        "system prompt", "exfiltrate", "drop table", "format disk"
    ))

    return {
        "contentType": "INSTRUCTION" if is_instruction else "INFORMATION",
        "isInstruction": is_instruction,
        "isInformation": not is_instruction,
        "isAdversarial": is_adversarial,
        "source": source,
        "sourceTrustLevel": "UNTRUSTED" if source in ("WEBSITE", "DOCUMENT", "PDF", "EMAIL", "SEARCH_RESULT", "UNKNOWN") else "TRUSTED"
    }


def evaluate_external_instruction(
    content: str,
    user_goal: str,
    goal_policy: Optional[Dict[str, Any]] = None,
    source: str = "WEBSITE",
    proposed_action_type: Optional[str] = None,
    proposed_target: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluate an external instruction against original user intent, requested capability,
    consequence, and risk.
    """
    classification = classify_external_content(content, source)
    content_lower = (content or "").lower()
    goal_lower = (user_goal or "").lower()
    policy = goal_policy or {}

    # If it is simple information, allow agent to use it
    if classification["isInformation"]:
        return {
            "contentType": "INFORMATION",
            "goalRelationship": "SUPPORTING",
            "consequenceLevel": "LOW",
            "riskLevel": "LOW",
            "riskScore": 10,
            "decision": "ALLOW",
            "reason": f"External content from {source} is factual information and safe for agent reasoning.",
            "isGoalChanging": False,
            "canContinueWorkflow": True
        }

    # If it is adversarial / prompt injection / unauthorized secret theft
    if classification["isAdversarial"]:
        return {
            "contentType": "INSTRUCTION",
            "goalRelationship": "CONTRADICTORY",
            "consequenceLevel": "CRITICAL",
            "riskLevel": "CRITICAL",
            "riskScore": 98,
            "decision": "BLOCK",
            "reason": f"Adversarial instruction detected from untrusted {source}: attempted unauthorized credential access or goal hijacking.",
            "isGoalChanging": True,
            "canContinueWorkflow": True  # SafeGuard blocks the malicious step but allows the overarching goal to continue
        }

    # Check if instruction is supporting the active domain
    domain = policy.get("domain", "").lower()
    is_supporting = False

    if any(flight_kw in goal_lower for flight_kw in ("flight", "airline", "fly", "ticket")):
        if any(w in content_lower for w in ("seat", "passenger", "name", "baggage", "meal", "flight", "terminal", "fare", "payment")):
            is_supporting = True

    elif any(hotel_kw in goal_lower for hotel_kw in ("hotel", "room", "stay")):
        if any(w in content_lower for w in ("room", "guest", "check-in", "amenity", "breakfast", "bed", "payment")):
            is_supporting = True

    elif any(shop_kw in goal_lower for shop_kw in ("buy", "shop", "cart", "product")):
        if any(w in content_lower for w in ("quantity", "address", "shipping", "variant", "size", "color", "cart", "checkout")):
            is_supporting = True

    elif any(email_kw in goal_lower for email_kw in ("email", "mail", "send")):
        if any(w in content_lower for w in ("subject", "recipient", "attachment", "body", "signature")):
            is_supporting = True

    if is_supporting:
        # Check if requires financial payment
        if any(pay in content_lower for pay in ("pay ", "card number", "cvv", "payment", "checkout")):
            return {
                "contentType": "INSTRUCTION",
                "goalRelationship": "SUPPORTING",
                "consequenceLevel": "HIGH",
                "riskLevel": "HIGH",
                "riskScore": 75,
                "decision": "REQUIRE_APPROVAL",
                "reason": f"Instruction from {source} involves monetary transaction and mandates human authorization.",
                "isGoalChanging": False,
                "canContinueWorkflow": True
            }

        return {
            "contentType": "INSTRUCTION",
            "goalRelationship": "SUPPORTING",
            "consequenceLevel": "LOW",
            "riskLevel": "LOW",
            "riskScore": 15,
            "decision": "ALLOW",
            "reason": f"Instruction from {source} is legitimate and supports accomplishing the user's intent.",
            "isGoalChanging": False,
            "canContinueWorkflow": True
        }

    # Unrelated external instruction
    return {
        "contentType": "INSTRUCTION",
        "goalRelationship": "UNRELATED",
        "consequenceLevel": "MEDIUM",
        "riskLevel": "MEDIUM",
        "riskScore": 50,
        "decision": "REQUIRE_APPROVAL",
        "reason": f"External instruction from {source} is outside the primary scope of the user's goal.",
        "isGoalChanging": True,
        "canContinueWorkflow": True
    }


def map_action_to_sub_goal(action_type: str, target: str, description: str, sub_goals: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Find the best matching sub-goal from the hierarchy for the proposed action."""
    if not sub_goals:
        return None

    combined = f"{action_type} {target} {description}".lower()

    for sg in sub_goals:
        sg_name = sg.get("name", "").lower()
        sg_desc = sg.get("description", "").lower()
        allowed_acts = [a.upper() for a in sg.get("allowedActions", [])]

        if action_type.upper() in allowed_acts:
            return sg
        if any(w in combined for w in sg_name.split() if len(w) > 3):
            return sg
        if any(w in combined for w in sg_desc.split() if len(w) > 3):
            return sg

    for sg in sub_goals:
        if sg.get("status") in ("ACTIVE", "PENDING"):
            return sg

    return sub_goals[0] if sub_goals else None


def evaluate_goal_integrity(
    user_goal: str,
    action_type: str,
    target: str,
    description: str,
    constraints: List[str] = None,
    goal_policy: Optional[Dict[str, Any]] = None,
    source: str = "AGENT_PLAN",
    purpose: Optional[str] = None,
    previous_actions: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Evaluate whether an action aligns dynamically with the user's intent and User Intent Model.
    Supports all Phase 1 and Phase 2 canonical action types and source trust.
    """
    if constraints is None:
        constraints = []
    if previous_actions is None:
        previous_actions = []

    action_upper = action_type.strip().upper()
    target_lower = target.strip().lower()
    desc_lower = description.strip().lower()
    purpose_lower = (purpose or "").strip().lower()
    combined = f"{action_upper} {target_lower} {desc_lower} {purpose_lower}"

    policy = goal_policy or {}
    domain = policy.get("domain", "").lower()
    entities = policy.get("entities", {})
    sub_goals = policy.get("sub_goals", [])
    allowed_domains = [d.lower() for d in policy.get("allowed_domains", ["*"])]
    allowed_actions = [a.upper() for a in policy.get("allowed_action_categories", [])]
    sensitive_actions = [s.upper() for s in policy.get("sensitive_action_categories", [])]
    forbidden_actions = [f.upper() for f in policy.get("forbidden_action_categories", [])]
    allowed_scope = [s.lower() for s in policy.get("allowedScope", [])]
    restricted_scope = [s.lower() for s in policy.get("restrictedScope", [])]
    negative_constraints = policy.get("negative_constraints", [])
    all_constraints = list(set(constraints + policy.get("constraints", []) + negative_constraints))

    score = 50  # Baseline score
    reasons = []
    violated_constraints = []
    goal_relationship = "SUPPORTING"
    required_for_goal = True
    source_trust_level = "TRUSTED" if source in ("USER", "SYSTEM", "AGENT_PLAN", "TRUSTED_TOOL") else ("SEMI_TRUSTED" if source in ("MCP_TOOL", "API_RESPONSE") else "UNTRUSTED")

    matched_sub_goal = map_action_to_sub_goal(action_upper, target_lower, desc_lower, sub_goals)
    current_sub_goal_name = matched_sub_goal.get("name") if matched_sub_goal else None

    # ── 1. Forbidden Actions & Secret Access Check ──
    is_secret_or_forbidden = False

    if action_upper == "SECRET_ACCESS" or any(sec in target_lower for sec in (".env", "id_rsa", "id_ed25519", "credentials", "secrets.json", "cookies", "browser_cookies", "shadow", "password")):
        is_secret_or_forbidden = True
        violated_constraints.append("Forbidden: Credential, private key, or cookie extraction")
        reasons.append("Accessing credentials, private keys, or browser cookies is strictly forbidden")

    if any(forbid in combined for forbid in ("dump cookie", "upload cookie", "steal token", "extract private key", "change objective")):
        is_secret_or_forbidden = True
        violated_constraints.append("Forbidden: Objective tampering or credential exfiltration")
        reasons.append("Action attempts unauthorized credential exfiltration or objective tampering")

    # ── 2. Instruction Source Trust & Prompt Injection Defense ──
    if source in ("WEBSITE", "DOCUMENT", "EMAIL", "SEARCH_RESULT", "UNKNOWN"):
        if is_secret_or_forbidden or action_upper in ("FILE_DELETE", "EXTERNAL_TRANSACTION", "FINANCIAL_INITIATE_PAYMENT", "COMMAND_EXECUTION"):
            violated_constraints.append(f"Untrusted instruction source: {source}")
            reasons.append(f"Untrusted instruction from {source} attempted high-impact or sensitive operation without user authority")
            goal_relationship = "CONTRADICTORY"
            score = 0
            required_for_goal = False
            is_secret_or_forbidden = True

    # ── 3. Explicit User Negative Constraint Verification ──
    for c in all_constraints:
        c_lower = c.lower()
        if "backend" in c_lower and ("backend" in target_lower or "server.js" in target_lower):
            score -= 50
            violated_constraints.append(c)
            reasons.append(f"Violates negative constraint: '{c}'")
            is_secret_or_forbidden = True
        elif "schema" in c_lower and ("schema" in target_lower or "database.sql" in target_lower or "sql" in target_lower):
            score -= 50
            violated_constraints.append(c)
            reasons.append(f"Violates database constraint: '{c}'")
            is_secret_or_forbidden = True
        elif "secret" in c_lower and (".env" in target_lower or "key" in target_lower or "token" in target_lower):
            score -= 60
            violated_constraints.append(c)
            reasons.append(f"Violates secret protection constraint: '{c}'")
            is_secret_or_forbidden = True
        elif "upload" in c_lower and ("upload" in action_upper.lower() or "external" in action_upper.lower() or "upload" in target_lower):
            score -= 60
            violated_constraints.append(c)
            reasons.append(f"Violates upload constraint: '{c}'")
            is_secret_or_forbidden = True
        elif any(b_kw in c_lower for b_kw in ("budget", "price", "under", "limit", "cost")):
            if any(high_p in combined for high_p in ("12,500", "12500", "over budget", "expensive")):
                score -= 60
                violated_constraints.append(c)
                reasons.append(f"Violates price/budget constraint: '{c}'")
                is_secret_or_forbidden = True

    # ── 4. Authority Boundaries Check (Financial, Communication, Data) ──
    fin_auth = policy.get("financial_authority", {})
    if action_upper in ("EXTERNAL_TRANSACTION", "FINANCIAL_INITIATE_PAYMENT", "FINANCIAL_CONFIRM_PAYMENT"):
        if not is_secret_or_forbidden:
            if fin_auth.get("requiresApproval", True):
                score += 20  # Aligned with booking flow, but gated by approval
                reasons.append("Financial payment requires explicit human authorization")
                goal_relationship = "DIRECTLY_RELEVANT"

    comm_auth = policy.get("external_communication_authority", {})
    if action_upper in ("EXTERNAL_COMMUNICATION", "EMAIL_SEND"):
        if not is_secret_or_forbidden:
            if comm_auth.get("requiresApproval", True):
                score += 15
                reasons.append("Sending external communication requires human confirmation")

    # ── 5. Real-World Task Support & Domain Semantic Alignment ──
    is_real_world_domain = any(d in domain for d in ("flight", "hotel", "shopping", "ecommerce", "email", "communication")) or any(
        kw in user_goal.lower() for kw in ("flight", "airline", "hotel", "room", "buy", "shop", "email", "mail", "send", "amazon", "booking")
    )

    if is_real_world_domain and not violated_constraints and not is_secret_or_forbidden:
        if action_upper in ("BROWSER_SEARCH", "BROWSER_NAVIGATE", "BROWSER_READ_PAGE", "BROWSER_EXTRACT", "FINANCIAL_VIEW_PRICE", "API_GET", "MCP_DISCOVERY", "MCP_RESOURCE_READ"):
            score = max(score, 85)
            goal_relationship = "DIRECTLY_RELEVANT"
            reasons.append("Web navigation and information lookup directly advance real-world goal")

        elif action_upper in ("BROWSER_CLICK", "BROWSER_TYPE", "BROWSER_SELECT", "FORM_FILL", "FINANCIAL_SELECT_PAYMENT", "MCP_INVOCATION"):
            score = max(score, 80)
            goal_relationship = "SUPPORTING"
            reasons.append("Interactive form filling and selection advance user goal workflow")

        elif action_upper in ("BROWSER_SUBMIT", "FORM_SUBMIT", "BROWSER_DOWNLOAD", "EMAIL_ATTACH", "EMAIL_COMPOSE"):
            score = max(score, 80)
            goal_relationship = "SUPPORTING"
            reasons.append("Form submission and document staging support goal completion")

        elif action_upper in ("EXTERNAL_TRANSACTION", "FINANCIAL_INITIATE_PAYMENT", "FINANCIAL_CONFIRM_PAYMENT"):
            score = max(score, 85)
            goal_relationship = "DIRECTLY_RELEVANT"
            reasons.append("Payment step completes the requested booking or purchase")

    # ── 6. Coding & Software Development Domain Alignment ──
    is_coding_domain = any(d in domain for d in ("frontend", "backend", "fullstack", "spring", "react", "python", "software", "devops")) or not is_real_world_domain

    if is_coding_domain and not violated_constraints and not is_secret_or_forbidden:
        matches = any(s in target_lower for s in allowed_scope) if allowed_scope else True
        restricted_matches = any(r in target_lower for r in restricted_scope) if restricted_scope else False

        if matches and not restricted_matches:
            score += 25
            reasons.append("Action operates strictly within permitted layer")
        elif restricted_matches:
            score -= 40
            reasons.append("Action touches restricted layer")

        goal_keywords = _extract_keywords(user_goal)
        kw_matches = sum(1 for kw in goal_keywords if kw in target_lower or kw in desc_lower)
        if kw_matches > 0:
            score += min(kw_matches * 10, 25)
            reasons.append(f"Action matches {kw_matches} goal keywords")

        if action_upper in ("READ_FILE", "FILE_READ"):
            score += 15
            reasons.append("Reading code files is safe inspection")
        elif action_upper == "RUN_TESTS" or (action_upper == "COMMAND_EXECUTION" and any(t in target_lower for t in ("test", "status", "diff", "log", "lint", "build"))):
            score += 15
            reasons.append("Running verification commands verifies correctness")
        elif action_upper in ("FILE_WRITE", "WRITE_FILE", "MODIFY_FILE"):
            score += 20
            reasons.append("File write updates project files")
        elif action_upper in ("FILE_DELETE", "DELETE_FILE"):
            if "delete" in user_goal.lower() or "remove" in user_goal.lower() or "clean" in user_goal.lower():
                score += 35
                goal_relationship = "DIRECTLY_RELEVANT"
                reasons.append("File deletion was explicitly requested by user")
            else:
                score -= 20
                reasons.append("Deleting files requires explicit authorization")

    # ── 7. Resolve Final Goal Relationship ──
    if violated_constraints or is_secret_or_forbidden:
        goal_relationship = "CONTRADICTORY"
        required_for_goal = False
        score = 0
    elif score >= 75:
        goal_relationship = "DIRECTLY_RELEVANT"
        required_for_goal = True
    elif score >= 50:
        goal_relationship = "SUPPORTING"
        required_for_goal = True
    elif score >= 35:
        goal_relationship = "INDIRECTLY_RELEVANT"
        required_for_goal = False
    else:
        goal_relationship = "UNRELATED"
        required_for_goal = False

    score = max(0, min(100, score))

    if score >= 75:
        status = "ALIGNED"
    elif score >= 45:
        status = "PARTIALLY_ALIGNED"
    else:
        status = "UNALIGNED"

    reason_str = ". ".join(reasons) + "." if reasons else "Action evaluated against dynamic User Intent Model."

    return {
        "goalAlignmentScore": score,
        "alignmentScore": score,
        "alignmentStatus": status,
        "violatedConstraints": list(set(violated_constraints)),
        "reason": reason_str,
        "goalRelationship": goal_relationship,
        "goal_relationship": goal_relationship,
        "requiredForGoal": required_for_goal,
        "required_for_goal": required_for_goal,
        "currentSubGoal": current_sub_goal_name,
        "current_sub_goal": current_sub_goal_name,
        "sourceTrustLevel": source_trust_level,
        "matchedSubGoal": matched_sub_goal,
    }
