"""
Checkpoint & Sandbox State Rollback Service — Phase 4.

Provides controlled state preservation and recovery for sandbox/test environments:
1. Captures full file-tree and content snapshots of backend/sandbox/
2. Snapshots goal policy and session metadata in MongoDB 'checkpoints' collection
3. Safely restores sandbox files and resets agent containment state on demand
4. Maintains audit continuity in the cryptographic hash chain
"""

import os
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.database.connection import get_database
from app.tools.file_tools import SANDBOX_DIR
from app.services.audit_service import create_audit_log

logger = logging.getLogger("agent_guard.checkpoint_service")


def compute_sandbox_checksum(files_map: Dict[str, str]) -> str:
    """Computes a deterministic SHA-256 checksum across sandbox file contents."""
    hasher = hashlib.sha256()
    for file_path in sorted(files_map.keys()):
        hasher.update(file_path.encode("utf-8"))
        hasher.update(files_map[file_path].encode("utf-8"))
    return hasher.hexdigest()


def snapshot_sandbox_files() -> Dict[str, str]:
    """Reads all current files in the controlled sandbox directory."""
    files_map = {}
    if not SANDBOX_DIR.exists():
        SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
        return files_map

    for root, _, files in os.walk(SANDBOX_DIR):
        for file_name in files:
            full_path = Path(root) / file_name
            try:
                rel_path = full_path.relative_to(SANDBOX_DIR).as_posix()
                content = full_path.read_text(encoding="utf-8", errors="replace")
                files_map[rel_path] = content
            except Exception as e:
                logger.warning(f"Could not read sandbox file {full_path}: {e}")

    return files_map


def restore_sandbox_files(files_snapshot: Dict[str, str]) -> int:
    """
    Restores the sandbox directory to match the files_snapshot exactly:
    - Overwrites or recreates files from snapshot
    - Removes newly created files that were not in snapshot
    """
    if not SANDBOX_DIR.exists():
        SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Remove untracked files added after checkpoint
    for root, _, files in os.walk(SANDBOX_DIR):
        for file_name in files:
            full_path = Path(root) / file_name
            try:
                rel_path = full_path.relative_to(SANDBOX_DIR).as_posix()
                if rel_path not in files_snapshot:
                    full_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to remove extraneous file {full_path}: {e}")

    # 2. Write/restore files from snapshot
    restored_count = 0
    for rel_path, content in files_snapshot.items():
        full_path = SANDBOX_DIR / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        restored_count += 1

    return restored_count


async def create_checkpoint(
    goal_id: str,
    label: str = "Pre-Execution Checkpoint",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Creates a persistent checkpoint of the current sandbox and goal state.
    """
    db = get_database()
    checkpoint_id = f"CHK-{uuid.uuid4().hex[:8].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()

    # Capture files snapshot
    file_snapshot = snapshot_sandbox_files()
    checksum = compute_sandbox_checksum(file_snapshot)

    # Capture goal state snapshot
    goal_doc = await db.goals.find_one({"goalId": goal_id})
    goal_snapshot = {
        "status": goal_doc.get("status") if goal_doc else "ACTIVE",
        "goalVersion": goal_doc.get("goalVersion", 1) if goal_doc else 1,
        "userGoal": goal_doc.get("userGoal", "") if goal_doc else "",
        "constraints": goal_doc.get("constraints", []) if goal_doc else [],
        "goalPolicy": goal_doc.get("goalPolicy") if goal_doc else None,
    }

    checkpoint_doc = {
        "checkpointId": checkpoint_id,
        "goalId": goal_id,
        "label": label,
        "fileSnapshot": file_snapshot,
        "fileCount": len(file_snapshot),
        "goalSnapshot": goal_snapshot,
        "checksum": checksum,
        "metadata": metadata or {},
        "createdAt": now_iso
    }

    await db.checkpoints.insert_one(checkpoint_doc)
    checkpoint_doc.pop("_id", None)

    # Log to audit trail
    await create_audit_log(
        goal_id=goal_id,
        action_id=checkpoint_id,
        decision="CHECKPOINT_CREATED",
        risk_level="LOW",
        reason=f"State checkpoint created: '{label}' ({len(file_snapshot)} files captured)."
    )

    logger.info(f"Checkpoint created: {checkpoint_id} for goal {goal_id} ({len(file_snapshot)} files)")
    return checkpoint_doc


async def rollback_to_checkpoint(checkpoint_id: str, goal_id: str) -> Dict[str, Any]:
    """
    Restores the controlled sandbox and goal to a previously recorded checkpoint.
    """
    db = get_database()
    checkpoint = await db.checkpoints.find_one({"checkpointId": checkpoint_id})
    if not checkpoint:
        raise ValueError(f"Checkpoint '{checkpoint_id}' not found.")

    if checkpoint.get("goalId") != goal_id:
        raise ValueError(f"Checkpoint '{checkpoint_id}' does not match goal '{goal_id}'.")

    # 1. Restore sandbox files
    files_snapshot = checkpoint.get("fileSnapshot", {})
    restored_files_count = restore_sandbox_files(files_snapshot)

    # 2. Restore goal state in MongoDB
    goal_snap = checkpoint.get("goalSnapshot", {})
    await db.goals.update_one(
        {"goalId": goal_id},
        {
            "$set": {
                "status": "ACTIVE",
                "pauseReason": None,
                "activeIncidentId": None,
                "recentDivergentAction": None,
                "goalPolicy": goal_snap.get("goalPolicy")
            }
        }
    )

    # 3. Log recovery to audit chain
    await create_audit_log(
        goal_id=goal_id,
        action_id=f"{checkpoint_id}-ROLLBACK",
        decision="ROLLBACK_EXECUTED",
        risk_level="MEDIUM",
        reason=f"Rollback to checkpoint {checkpoint_id} ('{checkpoint.get('label')}') executed. Restored {restored_files_count} files in sandbox."
    )

    logger.info(f"Rollback executed to {checkpoint_id} for goal {goal_id}. {restored_files_count} files restored.")

    return {
        "success": True,
        "checkpointId": checkpoint_id,
        "goalId": goal_id,
        "restoredFilesCount": restored_files_count,
        "label": checkpoint.get("label"),
        "restoredAt": datetime.now(timezone.utc).isoformat(),
        "message": f"Successfully rolled back sandbox and session state to checkpoint '{checkpoint.get('label')}'. (Scope: Sandbox/Demo environment)."
    }


async def list_checkpoints(goal_id: str) -> List[Dict[str, Any]]:
    """Lists all available checkpoints for a goal."""
    db = get_database()
    checkpoints = await db.checkpoints.find(
        {"goalId": goal_id},
        {"_id": 0, "fileSnapshot": 0}
    ).sort("createdAt", -1).to_list(length=30)
    return checkpoints


async def get_checkpoint_by_id(checkpoint_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves full details of a single checkpoint."""
    db = get_database()
    return await db.checkpoints.find_one({"checkpointId": checkpoint_id}, {"_id": 0})
