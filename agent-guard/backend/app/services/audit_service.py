"""
Audit Service — Writes security decision records to the audit_logs collection.
"""

import uuid
from datetime import datetime, timezone
from app.database.connection import get_database


async def create_audit_log(
    goal_id: str,
    action_id: str,
    decision: str,
    risk_level: str,
    reason: str,
) -> dict:
    """
    Create an audit log entry for a security decision.

    Args:
        goal_id: The goal this action belongs to
        action_id: The action being audited
        decision: ALLOW | REQUIRE_APPROVAL | BLOCKED
        risk_level: LOW | MEDIUM | HIGH | CRITICAL
        reason: Explanation of the decision

    Returns:
        The created audit log document
    """
    db = get_database()

    log_entry = {
        "logId": f"LOG-{uuid.uuid4().hex[:8].upper()}",
        "goalId": goal_id,
        "actionId": action_id,
        "decision": decision,
        "riskLevel": risk_level,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    await db.audit_logs.insert_one(log_entry)
    return log_entry
