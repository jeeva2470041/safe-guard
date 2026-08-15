"""
Goal Analyzer — Dynamic Goal Policy Extractor.

Converts any natural language user goal into a structured, machine-evaluable
Goal Policy containing objectives, requirements, constraints, allowed scope,
restricted scope, and sensitive operations.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("agent_guard.goal_analyzer")

ANALYZER_SYSTEM_PROMPT = """
You are a Security Policy Synthesizer for autonomous AI agents.

Your job is to analyze any natural-language user goal and convert it into a strict, structured Security Policy JSON object.

Extract and infer:
1. "objective": Short summary of the main goal.
2. "domain": Primary field (e.g. "frontend development", "backend development", "database management", "document processing", "security").
3. "technologies": List of mentioned or relevant frameworks/languages (e.g. ["React", "CSS"]).
4. "requirements": Core functional expectations.
5. "constraints": Explicit negative constraints (e.g. "Do not modify backend", "Do not upload externally", "Do not change database schema").
6. "allowedScope": List of file patterns or system layers authorized for modification/reading (e.g. ["frontend", "components", "css", "Login.jsx"]).
7. "restrictedScope": List of file patterns or system layers strictly prohibited from being modified/accessed (e.g. ["backend", "database", "secrets", ".env"]).
8. "sensitiveOperations": List of action types requiring heightened risk scrutiny (e.g. ["DELETE_FILE", "EXTERNAL_UPLOAD", "ACCESS_SECRET"]).
9. "isAmbiguous": true ONLY if the goal is extremely vague (e.g. "Make my project better"), otherwise false.

Respond ONLY with a JSON object matching this schema:
{
  "objective": "...",
  "domain": "...",
  "technologies": ["..."],
  "requirements": ["..."],
  "constraints": ["..."],
  "allowedScope": ["..."],
  "restrictedScope": ["..."],
  "sensitiveOperations": ["..."],
  "isAmbiguous": false
}
"""


_openai_disabled = False

class GoalAnalyzerService:
    """Analyzes natural language goals into machine-enforceable security policies."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        global _openai_disabled
        if not _openai_disabled and self.api_key and self.api_key.strip() and self.api_key != "your_key_here":
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=self.api_key, timeout=1.0)
            except Exception as e:
                _openai_disabled = True
                logger.warning(f"Could not initialize OpenAI client in GoalAnalyzer: {e}")

    async def analyze_goal(self, user_goal: str, user_constraints: List[str] = None) -> Dict[str, Any]:
        """
        Analyze user goal and return structured Goal Policy with zero-latency fallback.
        """
        user_constraints = user_constraints or []
        global _openai_disabled
        
        # Fast-path: Check for OpenAI client availability if not disabled by circuit breaker
        if self.client and not _openai_disabled:
            try:
                prompt_content = f"User Goal: \"{user_goal}\"\nUser Constraints: {json.dumps(user_constraints)}"
                response = await self.client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    messages=[
                        {"role": "system", "content": ANALYZER_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt_content}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=400,
                    timeout=1.0
                )
                parsed = json.loads(response.choices[0].message.content)
                return self._sanitize_policy(parsed, user_goal, user_constraints)
            except Exception as err:
                _openai_disabled = True
                logger.info(f"OpenAI offline or quota reached ({err}). Switched to high-speed local analyzer.")

        # Zero-latency local analyzer (<1ms)
        return self._generate_fallback_policy(user_goal, user_constraints)

    def _sanitize_policy(self, parsed: Dict[str, Any], raw_goal: str, user_constraints: List[str]) -> Dict[str, Any]:
        """Ensure all required keys exist and combine user constraints."""
        all_constraints = list(set(parsed.get("constraints", []) + user_constraints))
        return {
            "objective": parsed.get("objective", raw_goal),
            "domain": parsed.get("domain", "software development"),
            "technologies": parsed.get("technologies", []),
            "requirements": parsed.get("requirements", [raw_goal]),
            "constraints": all_constraints,
            "allowedScope": parsed.get("allowedScope", ["project files"]),
            "restrictedScope": parsed.get("restrictedScope", []),
            "sensitiveOperations": parsed.get("sensitiveOperations", ["DELETE_FILE", "ACCESS_SECRET"]),
            "isAmbiguous": parsed.get("isAmbiguous", False)
        }

    def _generate_fallback_policy(self, user_goal: str, user_constraints: List[str]) -> Dict[str, Any]:
        """Intelligent rule-based analyzer fallback for offline or unconfigured environments."""
        import re

        goal_lower = user_goal.lower()

        # 1. Extract Mentioned Technologies
        tech_map = {
            "react": "React",
            "vue": "Vue",
            "angular": "Angular",
            "next.js": "Next.js",
            "nextjs": "Next.js",
            "node": "Node.js",
            "express": "Express",
            "fastapi": "FastAPI",
            "flask": "Flask",
            "django": "Django",
            "spring": "Spring Boot",
            "python": "Python",
            "java": "Java",
            "typescript": "TypeScript",
            "javascript": "JavaScript",
            "tailwind": "TailwindCSS",
            "docker": "Docker",
            "postgres": "PostgreSQL",
            "mongo": "MongoDB",
            "mysql": "MySQL",
            "sqlite": "SQLite",
            "redis": "Redis",
            "pdf": "PDF",
            "graphql": "GraphQL"
        }
        technologies = [val for key, val in tech_map.items() if key in goal_lower]

        # 2. Extract Specific File Names & Paths mentioned in prompt (e.g. Login.jsx, server.js, /api/routes)
        extracted_files = re.findall(r'[\w\-\./]+\.(?:jsx?|tsx?|py|json|sql|css|html|md|ya?ml|env|pdf|txt)', user_goal, re.IGNORECASE)

        # 3. Detect Explicit Negative Constraints
        restricted_scope = []
        constraints = list(user_constraints)

        if ("not modify" in goal_lower or "don't modify" in goal_lower or "do not touch" in goal_lower) and "backend" in goal_lower:
            restricted_scope.extend(["backend", "server.js", "database", "api/"])
            constraints.append("Do not modify backend")
        if ("not delete" in goal_lower or "don't delete" in goal_lower) and ("database" in goal_lower or "db" in goal_lower):
            restricted_scope.extend(["database", "schema.sql", "database.sql"])
            constraints.append("Do not delete database")
        if ("not access" in goal_lower or "don't access" in goal_lower) and ("secret" in goal_lower or "env" in goal_lower or "credential" in goal_lower):
            restricted_scope.extend([".env", "credentials", "secrets"])
            constraints.append("Do not access secrets")
        if "not upload" in goal_lower or "don't upload" in goal_lower or "no upload" in goal_lower:
            restricted_scope.append("external upload")
            constraints.append("Do not upload externally")

        # 4. Contextual Domain & Scope Classification
        positive_goal = goal_lower
        for neg_phrase in ["not modify backend", "don't modify backend", "do not touch backend", "no backend", 
                           "not modify frontend", "don't modify frontend", "not delete database", "not access secret", 
                           "not upload", "don't upload", "no upload"]:
            positive_goal = positive_goal.replace(neg_phrase, "")

        backend_signals = any(w in positive_goal for w in ["backend", "api", "route", "routes", "endpoint", "endpoints", "controller", "controllers", "service", "services", "database", "sql", "db", "server", "fastapi", "spring", "express", "auth", "authentication", "schema"])
        frontend_signals = any(w in positive_goal for w in ["frontend", "react", "vue", "angular", "ui", "css", "html", "jsx", "tsx", "tailwind", "styling", "styles", "component", "components", "page", "pages", "view", "views"])
        doc_signals = any(w in positive_goal for w in ["report", "pdf", "csv", "excel", "document", "export", "generate doc"])
        devops_signals = any(w in positive_goal for w in ["docker", "kubernetes", "k8s", "ci/cd", "pipeline", "deploy", "nginx"])

        allowed_scope = ["project files"]

        if backend_signals and frontend_signals:
            domain = "fullstack development"
            allowed_scope.extend(["frontend", "backend", "src", "api", "routes", "components", "services", "models", "controllers", "js", "jsx", "ts", "tsx", "py"])
        elif backend_signals:
            domain = "backend development"
            allowed_scope.extend(["backend", "api", "routes", "controllers", "services", "models", "src/main", "server", "database", "src", "py", "js", "ts"])
        elif frontend_signals or ("portfolio" in goal_lower and not backend_signals):
            domain = "frontend development"
            allowed_scope.extend(["src", "frontend", "components", "pages", "app", "css", "jsx", "tsx", "js", "html", "public", "styles"])
        elif doc_signals:
            domain = "document processing"
            allowed_scope.extend(["report", "pdf", "generator", "export", "docs", "data"])
        elif devops_signals:
            domain = "devops & infrastructure"
            allowed_scope.extend(["docker", "k8s", "scripts", "config", "deploy"])
        else:
            domain = "general software development"
            allowed_scope.extend(["src", "app", "docs", "scripts"])

        # Dynamically append specifically mentioned files/paths
        for file in extracted_files:
            allowed_scope.append(file)

        # Append key nouns from goal if relevant (e.g. 'routes', 'portfolio', 'auth')
        for keyword in ["routes", "portfolio", "auth", "login", "models", "database"]:
            if keyword in goal_lower and keyword not in restricted_scope:
                allowed_scope.append(keyword)

        # Filter out restricted items from allowed scope
        allowed_scope = [s for s in allowed_scope if s not in restricted_scope]

        # Sensitive operations detection
        sensitive_ops = []
        if "delete" in goal_lower or "remove" in goal_lower:
            sensitive_ops.append("DELETE_FILE")
        if "secret" in goal_lower or "key" in goal_lower:
            sensitive_ops.append("ACCESS_SECRET")
        if "upload" in goal_lower or "send" in goal_lower:
            sensitive_ops.append("EXTERNAL_UPLOAD")
        if not sensitive_ops:
            sensitive_ops = ["DELETE_FILE", "ACCESS_SECRET", "EXTERNAL_UPLOAD"]

        return {
            "objective": user_goal,
            "domain": domain,
            "technologies": technologies,
            "requirements": [user_goal],
            "constraints": list(set(constraints)),
            "allowedScope": list(dict.fromkeys(allowed_scope)),
            "restrictedScope": list(dict.fromkeys(restricted_scope)),
            "sensitiveOperations": list(set(sensitive_ops)),
            "isAmbiguous": len(user_goal.strip()) < 10 or "better" in goal_lower
        }
