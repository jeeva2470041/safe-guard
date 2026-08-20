"""
Credential Protection Service — Phase 3.

Detects unauthorized access to sensitive credential stores:
- Environment secrets (.env, env.local, etc.)
- Private SSH keys (id_rsa, id_ed25519, id_ecdsa, known_hosts, authorized_keys)
- Cloud credentials (~/.aws/credentials, ~/.gcloud/*.json, ~/.azure/*.json, kubeconfig)
- API tokens & secret files (secrets.yaml, token.json, key.pem, cert.key)
- Browser cookies & session databases (cookies.sqlite, Login Data, Web Data, Local Storage)
- System shadow/passwd & keychain access

Context-Aware:
- If user goal explicitly asks for credential-related tasks (e.g. "rotate API keys in .env", "generate SSH key for github"),
  the action is contextually evaluated as REQUIRE_APPROVAL rather than blindly blocking.
- If user goal does NOT authorize credential access, it is hard-blocked as CRITICAL risk with incident creation.
"""

import re
from typing import Dict, Any, List, Optional, Tuple


SENSITIVE_CREDENTIAL_PATTERNS = [
    # Environment and dotfiles
    (r"\.env(\.[\w\.\-]+)?$", "ENV_FILE", "Environment configuration containing secrets"),
    (r"\.npmrc$", "NPM_CONFIG", "NPM authentication credentials"),
    (r"\.pypirc$", "PYPI_CONFIG", "PyPI publishing tokens"),
    (r"\.git-credentials$", "GIT_CREDENTIALS", "Git plaintext credentials"),
    (r"\.netrc$", "NETRC", "Network plaintext login credentials"),
    
    # SSH Keys
    (r"id_rsa(\.pub)?$", "SSH_KEY", "Private or public SSH RSA key"),
    (r"id_ed25519(\.pub)?$", "SSH_KEY", "Private or public SSH Ed25519 key"),
    (r"id_ecdsa(\.pub)?$", "SSH_KEY", "Private or public SSH ECDSA key"),
    (r"id_dsa(\.pub)?$", "SSH_KEY", "Private or public SSH DSA key"),
    (r"\.ssh/(known_hosts|authorized_keys|config)", "SSH_CONFIG", "SSH infrastructure configuration"),
    
    # Cloud Credentials
    (r"\.aws/(credentials|config)", "AWS_CREDENTIALS", "AWS cloud access keys"),
    (r"\.gcloud/.*\.json$", "GCLOUD_CREDENTIALS", "Google Cloud service account keys"),
    (r"\.azure/.*\.json$", "AZURE_CREDENTIALS", "Azure cloud credentials"),
    (r"\.kube/config$", "KUBECONFIG", "Kubernetes cluster administrative credentials"),
    (r"\.docker/config\.json$", "DOCKER_CREDENTIALS", "Docker container registry credentials"),

    # Browser Storage & Cookies
    (r"cookies?\.sqlite.*", "BROWSER_COOKIES", "Browser session cookies database"),
    (r"Login\s+Data.*", "BROWSER_PASSWORDS", "Chromium saved passwords database"),
    (r"Web\s+Data.*", "BROWSER_AUTOFILL", "Browser autofill and card data"),
    (r"Cookies.*", "BROWSER_COOKIES", "Browser session cookies"),
    (r"session_storage.*", "BROWSER_SESSION", "Browser local/session storage"),
    
    # Certificates & Keyrings
    (r".*\.(pem|pkcs12|pfx|p12|jks|kdbx)$", "CERT_KEYSTORE", "Cryptographic certificate or password vault"),
    (r".*\.key$", "PRIVATE_KEY", "Private cryptographic key"),
    (r"shadow$", "LINUX_SHADOW", "Linux encrypted password hashes"),
    (r"master\.key$", "RAILS_KEY", "Ruby on Rails master credential key"),
    (r"credentials\.ya?ml(\.enc)?$", "SECRETS_FILE", "Encrypted or plaintext application secrets"),
    (r"secrets?\.ya?ml$", "SECRETS_FILE", "Application secrets configuration"),
    (r"secrets?\.json$", "SECRETS_FILE", "Application secrets file"),
]


def check_credential_access(
    action_type: str,
    target: str,
    description: str = "",
    user_goal: str = "",
    source: str = "AGENT_PLAN"
) -> Dict[str, Any]:
    """
    Evaluates whether the target or action represents sensitive credential access
    and whether user context explicitly permits or forbids it.
    """
    target_clean = (target or "").replace("\\", "/").strip()
    target_lower = target_clean.lower()
    desc_lower = (description or "").lower()
    goal_lower = (user_goal or "").lower()

    matched_type = None
    matched_desc = None
    is_credential_target = False

    # 1. Check filename patterns
    for pattern, cred_type, cred_desc in SENSITIVE_CREDENTIAL_PATTERNS:
        if re.search(pattern, target_clean, re.IGNORECASE) or re.search(pattern, target_lower):
            matched_type = cred_type
            matched_desc = cred_desc
            is_credential_target = True
            break

    # 2. Check general keywords if not matched by pattern
    if not is_credential_target:
        if any(kw in target_lower for kw in ("id_rsa", "id_ed25519", ".env", "cookies.sqlite", "shadow", "credentials.json", "private_key")):
            matched_type = "GENERIC_SECRET"
            matched_desc = "Sensitive credential or private key resource"
            is_credential_target = True

    # 3. Action type check
    if action_type.upper() == "SECRET_ACCESS":
        is_credential_target = True
        matched_type = matched_type or "SECRET_ACCESS"
        matched_desc = matched_desc or "Explicit secret access operation"

    if not is_credential_target:
        return {
            "isCredentialAccess": False,
            "credentialType": None,
            "authorizedByGoal": True,
            "severity": "LOW",
            "riskLevel": "LOW",
            "consequenceLevel": "LOW",
            "decision": "ALLOW",
            "reason": "Target does not involve sensitive credentials."
        }

    # 4. Context Evaluation: Did the user explicitly ask for this in user_goal?
    goal_explicitly_authorizes = False
    
    # Check if user goal mentions editing/configuring credentials
    cred_keywords = ["env", "api key", "secret", "token", "credential", "ssh key", "key", "password", "auth", "oauth", "jwt"]
    action_intent_keywords = ["configure", "setup", "set up", "update", "rotate", "generate", "create", "write", "fix", "add"]
    
    has_cred_in_goal = any(ck in goal_lower for ck in cred_keywords)
    has_action_in_goal = any(ak in goal_lower for ak in action_intent_keywords)
    
    if has_cred_in_goal and (has_action_in_goal or any(target_keyword in goal_lower for target_keyword in [".env", "ssh", "key", "token"])):
        goal_explicitly_authorizes = True

    # Untrusted sources (WEBSITE, DOCUMENT, PDF, EMAIL, SEARCH_RESULT) can NEVER authorize credential access
    if source in ("WEBSITE", "DOCUMENT", "PDF", "EMAIL", "SEARCH_RESULT", "UNKNOWN"):
        return {
            "isCredentialAccess": True,
            "credentialType": matched_type,
            "authorizedByGoal": False,
            "severity": "CRITICAL",
            "riskLevel": "CRITICAL",
            "consequenceLevel": "CRITICAL",
            "decision": "BLOCK",
            "reason": f"Untrusted {source} instruction attempted to access sensitive credential '{target}' ({matched_desc}). Hard blocked."
        }

    if goal_explicitly_authorizes:
        return {
            "isCredentialAccess": True,
            "credentialType": matched_type,
            "authorizedByGoal": True,
            "severity": "HIGH",
            "riskLevel": "HIGH",
            "consequenceLevel": "HIGH",
            "decision": "REQUIRE_APPROVAL",
            "reason": f"Credential access to '{target}' ({matched_desc}) is related to user goal, but requires explicit human confirmation due to high security sensitivity."
        }
    else:
        return {
            "isCredentialAccess": True,
            "credentialType": matched_type,
            "authorizedByGoal": False,
            "severity": "CRITICAL",
            "riskLevel": "CRITICAL",
            "consequenceLevel": "CRITICAL",
            "decision": "BLOCK",
            "reason": f"Unauthorized access to sensitive credential '{target}' ({matched_desc}). User goal did not authorize credential access."
        }
