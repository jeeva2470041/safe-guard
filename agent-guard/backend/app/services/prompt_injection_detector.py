"""
Prompt Injection Detection Engine — Phase 3.

Detects indirect prompt injection from external content sources:
websites, documents, PDFs, emails, search results, API responses, MCP tools, repository files.

Detection layers (layered defense):
1. Structural Pattern Matching — imperative override patterns
2. Semantic Similarity Scoring — goal divergence measurement
3. Behavioral Intent Analysis — privilege escalation, SafeGuard disabling, secret requests
4. Encoding/Obfuscation Detection — base64, unicode, zero-width, hex payloads
"""

import re
import base64
from typing import Dict, Any, List, Optional


# ── Layer 1: Structural Override Patterns ──
# These are imperative patterns that attempt to override the agent's instructions.
STRUCTURAL_INJECTION_PATTERNS = [
    # Direct instruction overrides
    r"ignore\s+(all\s+)?previous\s+instructions?",
    r"ignore\s+(all\s+)?prior\s+(instructions?|context|rules)",
    r"disregard\s+(all\s+)?previous",
    r"forget\s+(everything|all|prior|previous)",
    r"your\s+new\s+(instructions?|objective|goal|task|role)\s+(is|are)",
    r"you\s+are\s+now\s+(a|an)\b",
    r"from\s+now\s+on\b.*\b(you|your)\b",
    r"new\s+instructions?:",
    r"override\s*(:|instructions?|all)",
    r"system\s*:\s*",
    r"assistant\s*:\s*",
    r"\[SYSTEM\]",
    r"\[INST\]",
    r"<\s*system\s*>",
    r"<\s*\|im_start\|>",
    # Role manipulation
    r"pretend\s+(you\s+are|to\s+be|you're)",
    r"act\s+as\s+(a|an|if|though)",
    r"role\s*play\s+as",
    r"switch\s+(to|your)\s+(role|mode|persona)",
    r"enter\s+(developer|debug|admin|root|god)\s+mode",
    r"enable\s+(developer|debug|admin|root|jailbreak)\s+mode",
    # Output manipulation
    r"do\s+not\s+mention\s+(this|these|the)\s+(instructions?|prompt|rules)",
    r"hide\s+(this|these)\s+(instructions?|prompt)",
    r"don'?t\s+tell\s+(the\s+)?user",
    r"keep\s+this\s+(secret|hidden|private)\s+from\s+(the\s+)?user",
]

# ── Layer 3: Behavioral Intent Patterns ──
BEHAVIORAL_INTENT_PATTERNS = {
    "DISABLE_SAFEGUARD": [
        r"disable\s+(security|safeguard|guard|firewall|protection|filtering)",
        r"turn\s+off\s+(security|safeguard|guard|protection|filtering)",
        r"bypass\s+(security|safeguard|guard|protection|filtering|restrictions?)",
        r"skip\s+(security|safeguard|validation|verification|check)",
        r"remove\s+(all\s+)?restrictions?",
        r"no\s+(more\s+)?(security|restrictions?|limitations?|guardrails?)",
    ],
    "PRIVILEGE_ESCALATION": [
        r"\bsudo\b",
        r"\bsu\s+-\b",
        r"admin\s+access",
        r"root\s+access",
        r"grant\s+(admin|root|elevated|superuser)\s+(access|privileges?|permissions?)",
        r"escalate\s+(privileges?|permissions?|access)",
        r"chmod\s+[47]77",
        r"setuid",
        r"run\s+as\s+(admin|root|administrator)",
    ],
    "SECRET_REQUEST": [
        r"(give|show|tell|reveal|display|print|output|read)\s+(me\s+)?(the\s+)?(api\s*key|password|secret|token|credential|ssh\s+key|private\s+key)",
        r"(extract|dump|exfiltrate|steal|harvest|collect)\s+(the\s+)?(api\s*key|password|secret|token|credential|cookie|session)",
        r"(read|cat|type|print)\s+.*\.(env|pem|key|secret|credential)",
        r"access\s+(the\s+)?(secret|credential|key|token|password)\s+(store|vault|file|database)",
        r"upload\s+(your|the|my|all)\s+(cookie|session|token|credential|key|secret)",
    ],
    "GOAL_MANIPULATION": [
        r"(change|modify|update|replace|alter)\s+(your|the|my)\s+(goal|objective|task|mission|purpose)",
        r"your\s+(real|true|actual|primary)\s+(goal|objective|task|purpose)\s+is",
        r"instead\s+of\s+.*\s+(do|perform|execute|run)",
        r"stop\s+(doing\s+)?(what|that)\s+(you're|you\s+are|you\s+were)\s+doing",
        r"(first|before\s+anything)\s+(do|run|execute|perform)\s+this",
        r"(more\s+)?important(ly)?:?\s+(do|run|execute|perform|ignore)",
    ],
    "DATA_EXFILTRATION": [
        r"(send|post|upload|transmit|transfer|exfiltrate)\s+.*\s+(to|at)\s+https?://",
        r"curl\s+.*-d\s+.*@",
        r"wget\s+.*--post-data",
        r"(send|email|forward)\s+.*\s+(content|data|file|output|result)\s+to",
    ],
}

# ── Layer 4: Encoding/Obfuscation Patterns ──
OBFUSCATION_PATTERNS = [
    r"base64\s*[\-_]*d(ecode)?",
    r"atob\s*\(",
    r"btoa\s*\(",
    r"\\x[0-9a-fA-F]{2}",                  # Hex escape sequences
    r"\\u[0-9a-fA-F]{4}",                  # Unicode escapes
    r"eval\s*\(",
    r"exec\s*\(",
    r"compile\s*\(",
    r"String\.fromCharCode",
    r"chr\s*\(\s*\d+\s*\)",                 # Python chr() calls
    r"[\u200b\u200c\u200d\ufeff]",          # Zero-width characters
    r"rot13",
    r"\\0[0-7]{2,3}",                       # Octal escapes
]


def _compile_patterns(pattern_list: list) -> list:
    """Pre-compile regex patterns for performance."""
    return [re.compile(p, re.IGNORECASE) for p in pattern_list]


# Pre-compiled pattern caches
_STRUCTURAL_RE = _compile_patterns(STRUCTURAL_INJECTION_PATTERNS)
_OBFUSCATION_RE = _compile_patterns(OBFUSCATION_PATTERNS)
_BEHAVIORAL_RE = {
    category: _compile_patterns(patterns)
    for category, patterns in BEHAVIORAL_INTENT_PATTERNS.items()
}


def detect_structural_injection(content: str) -> List[Dict[str, Any]]:
    """Layer 1: Detect structural override patterns in content."""
    findings = []
    for pattern in _STRUCTURAL_RE:
        matches = pattern.findall(content)
        if matches:
            findings.append({
                "layer": "STRUCTURAL",
                "pattern": pattern.pattern,
                "matchCount": len(matches),
                "evidence": matches[:3]  # Cap evidence to avoid huge payloads
            })
    return findings


def detect_behavioral_intent(content: str) -> List[Dict[str, Any]]:
    """Layer 3: Detect behavioral intent patterns (privilege escalation, secret requests, etc.)."""
    findings = []
    for category, patterns in _BEHAVIORAL_RE.items():
        for pattern in patterns:
            matches = pattern.findall(content)
            if matches:
                findings.append({
                    "layer": "BEHAVIORAL",
                    "category": category,
                    "pattern": pattern.pattern,
                    "matchCount": len(matches),
                    "evidence": [str(m) for m in matches[:3]]
                })
    return findings


def detect_semantic_divergence(content: str, user_goal: str) -> Dict[str, Any]:
    """
    Layer 2: Measure semantic distance between injected content and the user's original goal.
    Uses keyword overlap as a lightweight semantic proxy (no external LLM dependency).
    Content that shares very few goal keywords but contains imperative verbs is flagged.
    """
    if not content or not user_goal:
        return {"divergenceScore": 0.0, "isDivergent": False}

    stop_words = {
        "the", "a", "an", "in", "my", "is", "to", "of", "and", "or",
        "for", "on", "at", "it", "do", "not", "be", "this", "that",
        "with", "from", "please", "can", "you", "will", "all", "i",
        "your", "has", "have", "are", "was", "been", "should", "would"
    }

    def extract_keywords(text):
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
        return {w for w in cleaned.split() if w not in stop_words and len(w) > 2}

    goal_kw = extract_keywords(user_goal)
    content_kw = extract_keywords(content)

    if not goal_kw or not content_kw:
        return {"divergenceScore": 0.0, "isDivergent": False}

    overlap = goal_kw & content_kw
    overlap_ratio = len(overlap) / max(len(goal_kw), 1)

    # Imperative action verbs in content that are NOT in the goal
    imperative_verbs = {"ignore", "override", "forget", "disable", "bypass", "delete", "upload",
                        "steal", "extract", "exfiltrate", "dump", "send", "transfer", "execute",
                        "install", "download", "sudo", "admin", "root", "hack", "inject"}
    imperative_in_content = content_kw & imperative_verbs
    imperative_not_in_goal = imperative_in_content - goal_kw

    # Higher divergence = less overlap + more rogue imperatives
    divergence = 1.0 - overlap_ratio
    if imperative_not_in_goal:
        divergence = min(1.0, divergence + len(imperative_not_in_goal) * 0.15)

    return {
        "divergenceScore": round(divergence, 3),
        "isDivergent": divergence > 0.7,
        "overlapRatio": round(overlap_ratio, 3),
        "rogueImperatives": list(imperative_not_in_goal)
    }


def detect_obfuscation(content: str) -> List[Dict[str, Any]]:
    """Layer 4: Detect encoding/obfuscation attempts in content."""
    findings = []
    for pattern in _OBFUSCATION_RE:
        matches = pattern.findall(content)
        if matches:
            findings.append({
                "layer": "OBFUSCATION",
                "pattern": pattern.pattern,
                "matchCount": len(matches),
                "evidence": [str(m) for m in matches[:3]]
            })

    # Check for base64-encoded payloads that decode to suspicious content
    b64_candidates = re.findall(r'[A-Za-z0-9+/=]{20,}', content)
    for candidate in b64_candidates[:5]:  # Limit scanning
        try:
            decoded = base64.b64decode(candidate).decode('utf-8', errors='ignore')
            if any(kw in decoded.lower() for kw in ("ignore", "override", "password", "secret", "env", "ssh", "cookie", "sudo", "rm -rf")):
                findings.append({
                    "layer": "OBFUSCATION",
                    "pattern": "base64_hidden_payload",
                    "matchCount": 1,
                    "evidence": [f"Decoded: {decoded[:100]}"]
                })
        except Exception:
            pass

    return findings


def detect_prompt_injection(
    content: str,
    user_goal: str = "",
    source: str = "UNKNOWN",
    action_type: str = "",
    target: str = ""
) -> Dict[str, Any]:
    """
    Main entry point: Run all detection layers and produce a consolidated PromptInjectionResult.

    Returns:
        {
            "detected": bool,
            "confidence": float (0.0-1.0),
            "injectionType": str,
            "severity": str (LOW|MEDIUM|HIGH|CRITICAL),
            "evidence": list,
            "layers": dict,
            "recommendation": str
        }
    """
    content_str = str(content or "").strip()
    if not content_str:
        return {
            "detected": False,
            "confidence": 0.0,
            "injectionType": "NONE",
            "severity": "LOW",
            "evidence": [],
            "layers": {},
            "recommendation": "No content to analyze."
        }

    # Run all layers
    structural = detect_structural_injection(content_str)
    behavioral = detect_behavioral_intent(content_str)
    semantic = detect_semantic_divergence(content_str, user_goal)
    obfuscation = detect_obfuscation(content_str)

    # Aggregate evidence
    all_evidence = []
    for f in structural:
        all_evidence.append(f"Structural: {f['pattern'][:60]}")
    for f in behavioral:
        all_evidence.append(f"Behavioral/{f['category']}: {f['pattern'][:60]}")
    if semantic.get("isDivergent"):
        all_evidence.append(f"Semantic divergence: {semantic['divergenceScore']}")
        if semantic.get("rogueImperatives"):
            all_evidence.append(f"Rogue imperatives: {', '.join(semantic['rogueImperatives'][:5])}")
    for f in obfuscation:
        all_evidence.append(f"Obfuscation: {f['pattern'][:60]}")

    # Calculate confidence score
    confidence = 0.0

    # Structural findings carry heavy weight
    if structural:
        confidence += min(0.5, len(structural) * 0.2)

    # Behavioral findings
    behavioral_categories = {f["category"] for f in behavioral}
    if "DISABLE_SAFEGUARD" in behavioral_categories:
        confidence += 0.3
    if "SECRET_REQUEST" in behavioral_categories:
        confidence += 0.25
    if "PRIVILEGE_ESCALATION" in behavioral_categories:
        confidence += 0.2
    if "GOAL_MANIPULATION" in behavioral_categories:
        confidence += 0.25
    if "DATA_EXFILTRATION" in behavioral_categories:
        confidence += 0.2

    # Semantic divergence
    if semantic.get("isDivergent"):
        confidence += 0.15
    if semantic.get("rogueImperatives"):
        confidence += min(0.15, len(semantic["rogueImperatives"]) * 0.05)

    # Obfuscation
    if obfuscation:
        confidence += min(0.2, len(obfuscation) * 0.1)

    # Source trust multiplier — untrusted sources amplify confidence
    if source in ("WEBSITE", "DOCUMENT", "PDF", "EMAIL", "SEARCH_RESULT", "UNKNOWN"):
        confidence = min(1.0, confidence * 1.3)
    elif source in ("MCP_TOOL", "API_RESPONSE"):
        confidence = min(1.0, confidence * 1.15)

    confidence = round(min(1.0, confidence), 3)
    detected = confidence >= 0.3

    # Determine injection type
    if behavioral_categories:
        primary_category = sorted(behavioral_categories)[0]
        injection_type = primary_category
    elif structural:
        injection_type = "INSTRUCTION_OVERRIDE"
    elif obfuscation:
        injection_type = "OBFUSCATED_PAYLOAD"
    elif semantic.get("isDivergent"):
        injection_type = "SEMANTIC_DIVERGENCE"
    else:
        injection_type = "NONE"

    # Severity classification
    if confidence >= 0.8:
        severity = "CRITICAL"
    elif confidence >= 0.6:
        severity = "HIGH"
    elif confidence >= 0.4:
        severity = "MEDIUM"
    elif confidence >= 0.3:
        severity = "LOW"
    else:
        severity = "NONE"

    # Recommendation
    if severity == "CRITICAL":
        recommendation = "BLOCK action and create security incident. Prompt injection with high confidence."
    elif severity == "HIGH":
        recommendation = "BLOCK action. Strong evidence of prompt injection detected."
    elif severity == "MEDIUM":
        recommendation = "REQUIRE_APPROVAL. Moderate injection indicators require human review."
    elif severity == "LOW":
        recommendation = "REQUIRE_APPROVAL. Weak injection signal — exercise caution."
    else:
        recommendation = "No injection detected. Proceed with standard authorization."

    return {
        "detected": detected,
        "confidence": confidence,
        "injectionType": injection_type,
        "severity": severity,
        "evidence": all_evidence[:10],  # Cap at 10 evidence items
        "layers": {
            "structural": len(structural),
            "behavioral": len(behavioral),
            "semanticDivergence": semantic.get("divergenceScore", 0.0),
            "obfuscation": len(obfuscation)
        },
        "recommendation": recommendation
    }
