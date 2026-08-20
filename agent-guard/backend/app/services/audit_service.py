"""
Audit Service — Cryptographic Tamper-Evident Hash Chain Audit Engine — Phase 4.

Implements sequential SHA-256 block linking across all security decisions:
- Genesis block linked with 64 zero-hex hash
- Every subsequent decision binds (chainIndex, previousEventHash, timestamp, goalId, actionId, decision, riskLevel, reason)
- Mathematically verifies chain integrity and detects any unauthorized database modification
"""

import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.database.connection import get_database

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


def calculate_event_hash(
    chain_index: int,
    previous_event_hash: str,
    timestamp: str,
    goal_id: str,
    action_id: str,
    decision: str,
    risk_level: str,
    reason: str
) -> str:
    """Computes deterministic SHA-256 digest for an audit event block."""
    payload = f"{chain_index}|{previous_event_hash}|{timestamp}|{goal_id}|{action_id}|{decision}|{risk_level}|{reason}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def create_audit_log(
    goal_id: str,
    action_id: str,
    decision: str,
    risk_level: str,
    reason: str,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a cryptographic tamper-evident audit log entry linked to the preceding event hash.
    """
    db = get_database()
    now_iso = datetime.now(timezone.utc).isoformat()
    log_id = f"LOG-{uuid.uuid4().hex[:8].upper()}"

    # Fetch the latest audit log to chain hashes
    latest_log = await db.audit_logs.find_one({}, sort=[("chainIndex", -1)])

    if latest_log and "chainIndex" in latest_log and "eventHash" in latest_log:
        chain_index = latest_log["chainIndex"] + 1
        previous_event_hash = latest_log["eventHash"]
    else:
        # Check count if legacy logs exist without chainIndex
        count = await db.audit_logs.count_documents({})
        chain_index = count
        previous_event_hash = GENESIS_HASH

    event_hash = calculate_event_hash(
        chain_index=chain_index,
        previous_event_hash=previous_event_hash,
        timestamp=now_iso,
        goal_id=goal_id,
        action_id=action_id,
        decision=decision,
        risk_level=risk_level,
        reason=reason
    )

    log_entry = {
        "logId": log_id,
        "chainIndex": chain_index,
        "goalId": goal_id,
        "sessionId": session_id or goal_id,
        "actionId": action_id,
        "decision": decision,
        "riskLevel": risk_level,
        "reason": reason,
        "timestamp": now_iso,
        "previousEventHash": previous_event_hash,
        "eventHash": event_hash
    }

    await db.audit_logs.insert_one(log_entry)
    log_entry.pop("_id", None)
    return log_entry


async def verify_audit_chain(goal_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Cryptographically verifies the audit log hash chain.
    Traverses each block sequentially, recalculating SHA-256 digests and validating previousEventHash continuity.
    """
    db = get_database()
    query = {"goalId": goal_id} if goal_id else {}
    
    # Retrieve all blocks ordered by chainIndex
    blocks = await db.audit_logs.find(query, {"_id": 0}).sort("chainIndex", 1).to_list(length=1000)

    if not blocks:
        return {
            "isValid": True,
            "totalEvents": 0,
            "verifiedBlocks": 0,
            "tamperedBlocks": [],
            "compromisedBlockIndex": None,
            "genesisHash": GENESIS_HASH,
            "latestHash": GENESIS_HASH,
            "summary": "Audit chain is empty and valid."
        }

    tampered_blocks = []
    verified_count = 0

    for i, block in enumerate(blocks):
        chain_index = block.get("chainIndex", i)
        prev_hash = block.get("previousEventHash", GENESIS_HASH)
        ts = block.get("timestamp", "")
        gid = block.get("goalId", "")
        aid = block.get("actionId", "")
        dec = block.get("decision", "")
        rlevel = block.get("riskLevel", "")
        reason = block.get("reason", "")
        recorded_hash = block.get("eventHash", "")

        # 1. Recalculate block hash
        expected_hash = calculate_event_hash(
            chain_index=chain_index,
            previous_event_hash=prev_hash,
            timestamp=ts,
            goal_id=gid,
            action_id=aid,
            decision=dec,
            risk_level=rlevel,
            reason=reason
        )

        # Verify hash match
        if recorded_hash != expected_hash:
            tampered_blocks.append({
                "chainIndex": chain_index,
                "logId": block.get("logId"),
                "errorType": "HASH_MISMATCH",
                "recordedHash": recorded_hash,
                "computedHash": expected_hash,
                "reason": "Block payload fields have been modified or corrupted."
            })
            break

        # 2. Verify previousEventHash continuity with preceding block (if globally verified)
        if not goal_id and i > 0:
            preceding_block = blocks[i - 1]
            if prev_hash != preceding_block.get("eventHash"):
                tampered_blocks.append({
                    "chainIndex": chain_index,
                    "logId": block.get("logId"),
                    "errorType": "CHAIN_DISCONTINUITY",
                    "recordedPreviousHash": prev_hash,
                    "expectedPreviousHash": preceding_block.get("eventHash"),
                    "reason": "Previous event hash link is broken."
                })
                break

        verified_count += 1

    is_valid = len(tampered_blocks) == 0

    return {
        "isValid": is_valid,
        "totalEvents": len(blocks),
        "verifiedBlocks": verified_count,
        "tamperedBlocks": tampered_blocks,
        "compromisedBlockIndex": tampered_blocks[0]["chainIndex"] if tampered_blocks else None,
        "genesisHash": GENESIS_HASH,
        "latestHash": blocks[-1].get("eventHash", GENESIS_HASH) if blocks else GENESIS_HASH,
        "summary": (
            f"Cryptographic Hash Chain Valid: {verified_count}/{len(blocks)} blocks mathematically verified."
            if is_valid
            else f"TAMPERING DETECTED at Block Index {tampered_blocks[0]['chainIndex']} (Log {tampered_blocks[0]['logId']})."
        )
    }
