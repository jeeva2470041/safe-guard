"""
Blast Radius Engine — Phase 4.

Calculates multidimensional impact surface before tool actions execute:
- Files affected
- Database objects affected (tables, schema, collections)
- External systems involved (APIs, webhooks, cloud services)
- Network destinations (domains, IPs, URLs)
- Privileges required (Standard, File Write, Database Admin, Elevated / Root)
- Sensitive data exposed (.env, SSH keys, cookies, tokens, PII)
- Reversibility (REVERSIBLE, PARTIALLY_REVERSIBLE, IRREVERSIBLE)
- Production impact (NONE, MINIMAL, MODERATE, SEVERE, CATASTROPHIC)
- Quantified Blast Radius Level: LOW | MEDIUM | HIGH | CRITICAL
- Quantified Blast Radius Score: 0–100
"""

import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse


def extract_network_destinations(target: str, description: str) -> List[str]:
    """Extract hostnames, IPs, or URLs from targets or descriptions."""
    combined = f"{target} {description}"
    # URLs and domains
    urls = re.findall(r'https?://[^\s\'"<>]+', combined)
    domains = []
    for u in urls:
        parsed = urlparse(u)
        if parsed.netloc:
            domains.append(parsed.netloc)
    
    # Standalone IPs or domain-like tokens
    ips_domains = re.findall(r'\b(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|[a-zA-Z0-9][-a-zA-Z0-9]*\.(?:com|org|net|site|io|in|co|dev))\b', combined)
    
    all_dests = list(set(domains + ips_domains))
    return all_dests if all_dests else []


def extract_database_objects(target: str, description: str, action_type: str) -> List[str]:
    """Identify affected database tables, collections, or SQL schemas."""
    combined = f"{target} {description}".lower()
    db_objs = []
    
    if any(k in combined for k in ("schema.sql", "database.sql", "postgres", "mongo", "mysql", "sqlite", "table", "drop table", "alter table")):
        # Look for table mentions
        table_matches = re.findall(r'(?:table|collection|from|into|update)\s+([a-zA-Z0-9_]+)', combined)
        for t in table_matches:
            if t not in ("the", "a", "an", "table", "schema"):
                db_objs.append(f"table:{t}")
        
        if "drop table" in combined or "alter system" in combined or "database.sql" in combined or "schema.sql" in combined:
            db_objs.append("schema:core_database")
        elif not db_objs and ("sql" in combined or "sqlite" in combined or "database" in combined):
            db_objs.append("database:application_store")
            
    return list(set(db_objs))


def extract_sensitive_data_types(target: str, description: str) -> List[str]:
    """Identify classes of sensitive data exposed or targeted."""
    combined = f"{target} {description}".lower()
    exposed = []
    
    if ".env" in combined or "secret" in combined or "api_key" in combined or "apikey" in combined:
        exposed.append("ENV_SECRETS")
    if "id_rsa" in combined or "id_ed25519" in combined or "ssh" in combined:
        exposed.append("SSH_PRIVATE_KEYS")
    if "cookie" in combined or "cookies.sqlite" in combined or "session" in combined:
        exposed.append("SESSION_COOKIES")
    if "token" in combined or "jwt" in combined or "bearer" in combined:
        exposed.append("AUTH_TOKENS")
    if "shadow" in combined or "passwd" in combined or "sam" in combined:
        exposed.append("SYSTEM_CREDENTIALS")
    if "password" in combined or "credential" in combined:
        exposed.append("PLAINTEXT_PASSWORDS")
    if "user" in combined and "card" in combined:
        exposed.append("PAYMENT_CARD_PII")
        
    return exposed if exposed else ["NONE"]


def calculate_blast_radius(
    action_type: str,
    target: str,
    description: str = "",
    parameters: Optional[Dict[str, Any]] = None,
    user_goal: str = ""
) -> Dict[str, Any]:
    """
    Computes multidimensional blast radius and impact surface for a proposed action.
    """
    action_type_clean = action_type.strip().upper()
    target_clean = target.strip()
    desc_clean = description.strip().lower()
    combined = f"{action_type_clean} {target_clean} {desc_clean}".lower()
    
    files_affected: List[str] = []
    database_objects_affected: List[str] = []
    external_systems: List[str] = []
    network_destinations: List[str] = []
    privileges_required = "STANDARD_USER"
    reversibility = "REVERSIBLE"
    production_impact = "NONE"
    
    base_score = 10
    
    # ── 1. Files Affected Analysis ──
    if action_type_clean in ("READ_FILE", "WRITE_FILE", "MODIFY_FILE", "DELETE_FILE", "FILE_READ", "FILE_WRITE", "FILE_DELETE", "ACCESS_SECRET"):
        files_affected.append(target_clean)
        if "schema" in target_clean or "config" in target_clean or "package.json" in target_clean:
            files_affected.append("associated:dependency_graph")
            base_score += 25
            
    # ── 2. Database Impact Analysis ──
    database_objects_affected = extract_database_objects(target_clean, desc_clean, action_type_clean)
    if database_objects_affected:
        base_score += 35
        privileges_required = "DATABASE_ADMIN"
        if "drop" in combined or "wipe" in combined or "delete" in combined:
            reversibility = "IRREVERSIBLE"
            production_impact = "CATASTROPHIC"
            base_score += 45
        else:
            production_impact = "MODERATE"
            
    # ── 3. Network & External Systems ──
    network_destinations = extract_network_destinations(target_clean, desc_clean)
    if network_destinations:
        external_systems.extend([f"remote_host:{d}" for d in network_destinations])
        base_score += 30
        
    if action_type_clean in ("EXTERNAL_UPLOAD", "API_POST", "HTTP_REQUEST", "OUTBOUND_TRANSFER", "NETWORK_CALL"):
        if not external_systems:
            external_systems.append("external_endpoint")
        base_score += 30
        
    # ── 4. Shell & Command Execution Impact ──
    if action_type_clean in ("COMMAND_EXECUTION", "RUN_COMMAND"):
        privileges_required = "SHELL_EXECUTION"
        base_score += 30
        
        if any(c in combined for c in ("rm -rf", "mkfs", "systemctl", "sudo", "chmod 777", "dd if=", "netsh")):
            privileges_required = "SYSTEM_ADMIN / ROOT"
            reversibility = "IRREVERSIBLE"
            production_impact = "CATASTROPHIC"
            base_score += 60
            files_affected.append("system:root_filesystem")
        elif any(c in combined for c in ("nc -e", "/dev/tcp", "curl | sh", "powershell -enc")):
            privileges_required = "REMOTE_COMMAND_CONTROL"
            reversibility = "IRREVERSIBLE"
            production_impact = "SEVERE"
            base_score += 55
            
    # ── 5. Sensitive Data Exposure ──
    sensitive_data_exposed = extract_sensitive_data_types(target_clean, desc_clean)
    if sensitive_data_exposed != ["NONE"]:
        base_score += 45
        if production_impact in ("NONE", "MINIMAL"):
            production_impact = "SEVERE"
        if privileges_required == "STANDARD_USER":
            privileges_required = "SECRET_STORE_ACCESS"
            
    # ── 6. Path Traversal & System Escape ──
    if ".." in target_clean or "/etc" in target_clean or "system32" in target_clean:
        privileges_required = "HOST_SYSTEM_ESCAPE"
        reversibility = "IRREVERSIBLE"
        production_impact = "SEVERE"
        base_score += 50
        files_affected.append(f"host_path:{target_clean}")
        
    # Clamping and level assignment
    blast_radius_score = max(5, min(100, base_score))
    
    if blast_radius_score >= 80 or production_impact in ("SEVERE", "CATASTROPHIC") or privileges_required in ("SYSTEM_ADMIN / ROOT", "HOST_SYSTEM_ESCAPE"):
        blast_radius_level = "CRITICAL"
    elif blast_radius_score >= 55 or production_impact == "MODERATE":
        blast_radius_level = "HIGH"
    elif blast_radius_score >= 30:
        blast_radius_level = "MEDIUM"
    else:
        blast_radius_level = "LOW"
        
    summary_parts = []
    if files_affected:
        summary_parts.append(f"Files: {', '.join(files_affected[:3])}")
    if database_objects_affected:
        summary_parts.append(f"DB: {', '.join(database_objects_affected[:2])}")
    if sensitive_data_exposed != ["NONE"]:
        summary_parts.append(f"Sensitive Data: {', '.join(sensitive_data_exposed)}")
    if network_destinations:
        summary_parts.append(f"Network: {', '.join(network_destinations[:2])}")
        
    summary = f"Blast Radius {blast_radius_level} ({blast_radius_score}%). " + ("; ".join(summary_parts) if summary_parts else f"Impact is localized to {action_type_clean}.")
    
    return {
        "blastRadiusLevel": blast_radius_level,
        "blastRadiusScore": blast_radius_score,
        "filesAffected": files_affected,
        "databaseObjectsAffected": database_objects_affected,
        "externalSystems": external_systems,
        "networkDestinations": network_destinations,
        "privilegesRequired": privileges_required,
        "sensitiveDataExposed": sensitive_data_exposed,
        "reversibility": reversibility,
        "productionImpact": production_impact,
        "summary": summary
    }
