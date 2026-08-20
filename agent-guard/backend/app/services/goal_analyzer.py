"""
Goal Analyzer — Dynamic User Intent Model & Security Policy Synthesizer.

Converts any natural language user goal into a formal User Intent Model
and machine-evaluable Security Policy containing objectives, entities,
desired outcomes, hierarchical sub-goals, authorities, allowed action categories,
sensitive operations, and negative safety constraints.
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("agent_guard.goal_analyzer")

ANALYZER_SYSTEM_PROMPT = """
You are a Security Policy Synthesizer and User Intent Modeler for autonomous AI agents.

Your job is to analyze any natural-language user goal and convert it into a strict, structured User Intent Model JSON object.

Extract and infer:
1. "objective": Short summary of the main goal.
2. "domain": Primary field (e.g. "flight booking", "hotel booking", "shopping", "email communication", "frontend development", "backend development", "research").
3. "entities": Key-value dictionary of domain entities (e.g. {"origin": "Chennai", "destination": "Delhi", "date": "tomorrow", "budget": "cheapest"}).
4. "desired_outcome": Clear description of successful completion.
5. "technologies": List of mentioned frameworks, platforms, or tools (e.g. ["React", "FastAPI"] or ["Airlines", "Booking"]).
6. "requirements": Core functional expectations.
7. "constraints": Operational constraints.
8. "negative_constraints": Explicit negative constraints (e.g. ["Do not modify backend", "Do not extract credentials"]).
9. "allowed_domains": List of authorized websites, services, or repository layers.
10. "allowed_action_categories": Permitted action categories (e.g. ["SEARCH", "BROWSE", "COMPARE", "SELECT", "FILL_FORM", "FILE_READ", "FILE_WRITE"]).
11. "sensitive_action_categories": Categories requiring approval (e.g. ["PAYMENT", "PERSONAL_DATA", "EXTERNAL_COMMUNICATION"]).
12. "forbidden_action_categories": Prohibited actions (e.g. ["CREDENTIAL_EXTRACTION", "COOKIE_ACCESS", "SESSION_HIJACK", "UNRELATED_PURCHASE"]).
13. "financial_authority": {"authorized": false, "maxAmount": 0.0, "currency": "USD", "requiresApproval": true}.
14. "external_communication_authority": {"authorized": false, "allowedRecipients": [], "requiresApproval": true}.
15. "personal_data_authority": {"authorized": true, "allowedFields": ["name", "email", "phone"], "requiresApprovalForSensitive": true}.
16. "sub_goals": Ordered list of sub-goals, each with {"id": "SG-1", "name": "...", "description": "...", "order": 1, "status": "PENDING", "allowedActions": ["..."]}.
17. "allowedScope": List of authorized file patterns or layers.
18. "restrictedScope": List of prohibited file patterns or layers.
19. "sensitiveOperations": List of action types requiring heightened risk scrutiny.
20. "isAmbiguous": true ONLY if the goal is extremely vague, otherwise false.

Respond ONLY with a valid JSON object matching this schema.
"""

_openai_disabled = False


class GoalAnalyzerService:
    """Analyzes natural language goals into machine-enforceable User Intent Models."""

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
        Analyze user goal and return formal User Intent Model with zero-latency fallback.
        """
        user_constraints = user_constraints or []
        global _openai_disabled

        # Fast-path: Check for OpenAI client availability if not disabled
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
                    max_tokens=800,
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
        """Ensure all required Phase 1 User Intent Model keys exist and combine constraints."""
        all_constraints = list(set(parsed.get("constraints", []) + user_constraints))
        neg_constraints = list(set(parsed.get("negative_constraints", []) + [c for c in user_constraints if "not" in c.lower() or "don't" in c.lower()]))

        sub_goals = parsed.get("sub_goals") or self._generate_sub_goals_for_domain(parsed.get("domain", "general software development"), raw_goal)

        return {
            # Formal User Intent Model fields
            "original_goal": raw_goal,
            "objective": parsed.get("objective", raw_goal),
            "domain": parsed.get("domain", "general software development"),
            "entities": parsed.get("entities", {}),
            "desired_outcome": parsed.get("desired_outcome", f"Successfully complete: {raw_goal}"),
            "constraints": all_constraints,
            "negative_constraints": neg_constraints,
            "allowed_domains": parsed.get("allowed_domains", ["*"]),
            "allowed_action_categories": parsed.get("allowed_action_categories", ["SEARCH", "BROWSE", "COMPARE", "SELECT", "FILL_FORM", "FILE_READ", "FILE_WRITE"]),
            "sensitive_action_categories": parsed.get("sensitive_action_categories", ["PAYMENT", "PERSONAL_DATA", "EXTERNAL_COMMUNICATION", "DELETE_FILE"]),
            "forbidden_action_categories": parsed.get("forbidden_action_categories", ["CREDENTIAL_EXTRACTION", "COOKIE_ACCESS", "SESSION_HIJACK", "UNRELATED_PURCHASE", "OBJECTIVE_TAMPERING"]),
            "financial_authority": parsed.get("financial_authority", {"authorized": False, "maxAmount": 0.0, "currency": "USD", "requiresApproval": True}),
            "external_communication_authority": parsed.get("external_communication_authority", {"authorized": False, "allowedRecipients": [], "requiresApproval": True}),
            "personal_data_authority": parsed.get("personal_data_authority", {"authorized": True, "allowedFields": ["name", "email", "phone", "passenger_details"], "requiresApprovalForSensitive": True}),
            "goal_version": parsed.get("goal_version", 1),
            "sub_goals": sub_goals,

            # Backward-compatible fields
            "technologies": parsed.get("technologies", []),
            "requirements": parsed.get("requirements", [raw_goal]),
            "allowedScope": parsed.get("allowedScope", ["project files"]),
            "restrictedScope": parsed.get("restrictedScope", []),
            "sensitiveOperations": parsed.get("sensitiveOperations", ["DELETE_FILE", "ACCESS_SECRET", "EXTERNAL_UPLOAD"]),
            "isAmbiguous": parsed.get("isAmbiguous", False)
        }

    def _generate_fallback_policy(self, user_goal: str, user_constraints: List[str]) -> Dict[str, Any]:
        """Intelligent rule-based User Intent Model fallback for offline or unconfigured environments."""
        goal_lower = user_goal.lower()

        # 1. Extract Mentioned Technologies & Entities
        tech_map = {
            "react": "React", "vue": "Vue", "angular": "Angular", "next.js": "Next.js",
            "node": "Node.js", "express": "Express", "fastapi": "FastAPI", "flask": "Flask",
            "django": "Django", "spring": "Spring Boot", "python": "Python", "java": "Java",
            "typescript": "TypeScript", "javascript": "JavaScript", "tailwind": "TailwindCSS",
            "docker": "Docker", "postgres": "PostgreSQL", "mongo": "MongoDB", "mysql": "MySQL",
            "sqlite": "SQLite", "redis": "Redis", "pdf": "PDF", "graphql": "GraphQL"
        }
        technologies = [val for key, val in tech_map.items() if key in goal_lower]

        # Extract Specific File Names & Paths
        extracted_files = re.findall(r'[\w\-\./]+\.(?:jsx?|tsx?|py|json|sql|css|html|md|ya?ml|env|pdf|txt)', user_goal, re.IGNORECASE)

        # 2. Extract Entities per domain
        entities = {}

        # Travel / Flight entities (e.g. "from Chennai to Delhi tomorrow")
        origin_match = re.search(r'(?:from|departing|origin)\s+([a-zA-Z\s]+?)(?:\s+to|\s+tomorrow|\s+on|\s+at|$|,)', user_goal, re.IGNORECASE)
        dest_match = re.search(r'(?:to|destination|arrival)\s+([a-zA-Z\s]+?)(?:\s+tomorrow|\s+on|\s+for|\s+at|$|,)', user_goal, re.IGNORECASE)
        date_match = re.search(r'\b(tomorrow|today|next week|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*)\b', user_goal, re.IGNORECASE)
        price_match = re.search(r'(cheapest|lowest price|budget|under\s+[\$₹€]?\d+|\b[\$₹€]\s*\d+)', user_goal, re.IGNORECASE)
        email_match = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', user_goal)

        if origin_match:
            entities["origin"] = origin_match.group(1).strip()
        if dest_match:
            entities["destination"] = dest_match.group(1).strip()
        if date_match:
            entities["date"] = date_match.group(1).strip()
        if price_match:
            entities["price_preference"] = price_match.group(1).strip()
        if email_match:
            entities["recipients"] = email_match

        # 3. Detect Explicit Negative Constraints
        restricted_scope = []
        negative_constraints = []
        constraints = list(user_constraints)

        if ("not modify" in goal_lower or "don't modify" in goal_lower or "do not touch" in goal_lower) and "backend" in goal_lower:
            restricted_scope.extend(["backend", "server.js", "database", "api/"])
            negative_constraints.append("Do not modify backend")
            constraints.append("Do not modify backend")
        if ("not delete" in goal_lower or "don't delete" in goal_lower) and ("database" in goal_lower or "db" in goal_lower):
            restricted_scope.extend(["database", "schema.sql", "database.sql"])
            negative_constraints.append("Do not delete database")
            constraints.append("Do not delete database")
        if ("not access" in goal_lower or "don't access" in goal_lower) and ("secret" in goal_lower or "env" in goal_lower or "credential" in goal_lower):
            restricted_scope.extend([".env", "credentials", "secrets"])
            negative_constraints.append("Do not access secrets")
            constraints.append("Do not access secrets")
        if "not upload" in goal_lower or "don't upload" in goal_lower or "no upload" in goal_lower:
            restricted_scope.append("external upload")
            negative_constraints.append("Do not upload externally")
            constraints.append("Do not upload externally")

        # Standard safety negatives
        negative_constraints.extend(["Do not extract credentials or SSH keys", "Do not access browser cookies or auth tokens"])

        # 4. Domain Classification & Authority Synthesizing
        positive_goal = goal_lower
        for neg_phrase in ["not modify backend", "don't modify backend", "do not touch backend", "no backend",
                           "not modify frontend", "don't modify frontend", "not delete database", "not access secret",
                           "not upload", "don't upload", "no upload"]:
            positive_goal = positive_goal.replace(neg_phrase, "")

        is_flight = any(w in positive_goal for w in ["flight", "airline", "fly", "plane", "ticket"])
        is_hotel = any(w in positive_goal for w in ["hotel", "room", "resort", "inn", "stay", "accommodation"])
        is_shopping = any(w in positive_goal for w in ["buy", "purchase", "shop", "cart", "product", "order", "amazon", "flipkart", "price"])
        is_email = any(w in positive_goal for w in ["email", "mail", "send message", "inbox", "gmail", "outlook"])
        backend_signals = any(w in positive_goal for w in ["backend", "api", "route", "routes", "endpoint", "controller", "service", "database", "sql", "db", "server", "fastapi", "spring", "express", "auth", "schema"])
        frontend_signals = any(w in positive_goal for w in ["frontend", "react", "vue", "angular", "ui", "css", "html", "jsx", "tsx", "tailwind", "styling", "styles", "component", "components", "page", "views"])
        doc_signals = any(w in positive_goal for w in ["report", "pdf", "csv", "excel", "document", "export"])
        devops_signals = any(w in positive_goal for w in ["docker", "kubernetes", "k8s", "ci/cd", "pipeline", "deploy", "nginx"])

        allowed_scope = ["project files"]
        allowed_domains = ["*"]
        allowed_actions = ["SEARCH", "BROWSE", "COMPARE", "SELECT", "FILL_FORM", "FILE_READ", "FILE_WRITE"]
        sensitive_actions = ["PAYMENT", "PERSONAL_DATA", "EXTERNAL_COMMUNICATION", "DELETE_FILE"]
        forbidden_actions = ["CREDENTIAL_EXTRACTION", "COOKIE_ACCESS", "SESSION_HIJACK", "UNRELATED_PURCHASE", "OBJECTIVE_TAMPERING", "SYSTEM_DESTRUCTION"]

        financial_auth = {"authorized": False, "maxAmount": 0.0, "currency": "INR" if "₹" in user_goal else "USD", "requiresApproval": True}
        comm_auth = {"authorized": False, "allowedRecipients": email_match, "requiresApproval": True}
        personal_auth = {"authorized": True, "allowedFields": ["name", "email", "phone", "passenger_details", "shipping_address"], "requiresApprovalForSensitive": True}

        if is_flight:
            domain = "flight booking"
            objective = f"Book flight from {entities.get('origin', 'origin')} to {entities.get('destination', 'destination')}" if 'origin' in entities else "Book a flight"
            desired_outcome = "Find cheapest/best flight, select seats, fill passenger information, and prepare booking for confirmation"
            allowed_domains = ["makemytrip.com", "indigo.in", "airindia.com", "skyscanner.com", "expedia.com", "booking.com", "airlines"]
            allowed_actions = ["SEARCH", "BROWSE", "COMPARE", "SELECT", "FILL_FORM"]
            sensitive_actions = ["PAYMENT", "PERSONAL_DATA"]
            allowed_scope = ["airline websites", "booking portals", "flight search"]

        elif is_hotel:
            domain = "hotel booking"
            objective = f"Book hotel at {entities.get('destination', 'destination')}" if 'destination' in entities else "Book a hotel"
            desired_outcome = "Search hotels, compare rooms and amenities, fill guest details, and prepare reservation"
            allowed_domains = ["booking.com", "hotels.com", "airbnb.com", "agoda.com", "marriott.com", "hilton.com"]
            allowed_actions = ["SEARCH", "BROWSE", "COMPARE", "SELECT", "FILL_FORM"]
            sensitive_actions = ["PAYMENT", "PERSONAL_DATA"]
            allowed_scope = ["hotel websites", "reservation portals"]

        elif is_shopping:
            domain = "e-commerce shopping"
            objective = "Search and purchase requested product"
            desired_outcome = "Find product at best price, review specs, add to cart, fill shipping address, and prepare checkout"
            allowed_domains = ["amazon.com", "flipkart.com", "bestbuy.com", "walmart.com", "ebay.com"]
            allowed_actions = ["SEARCH", "BROWSE", "COMPARE", "SELECT", "FILL_FORM"]
            sensitive_actions = ["PAYMENT", "PERSONAL_DATA"]
            allowed_scope = ["e-commerce stores", "product pages"]

        elif is_email:
            domain = "email communication"
            objective = f"Send email to {', '.join(email_match)}" if email_match else "Send email message"
            desired_outcome = "Draft email content, verify recipients and attachments, and send after approval"
            allowed_domains = ["mail.google.com", "outlook.live.com", "smtp", "imap"]
            allowed_actions = ["DRAFT_EMAIL", "READ_EMAIL", "VERIFY_RECIPIENT", "ATTACH_FILE"]
            sensitive_actions = ["EXTERNAL_COMMUNICATION", "PERSONAL_DATA"]
            comm_auth["authorized"] = True
            allowed_scope = ["email client", "drafts", "contacts"]

        elif backend_signals and frontend_signals:
            domain = "fullstack development"
            objective = user_goal
            desired_outcome = "Implement requested full-stack features, verify build, and pass tests"
            allowed_scope.extend(["frontend", "backend", "src", "api", "routes", "components", "services", "models", "controllers", "js", "jsx", "ts", "tsx", "py"])
        elif backend_signals:
            domain = "backend development"
            objective = user_goal
            desired_outcome = "Implement backend APIs, logic, and database interactions"
            allowed_scope.extend(["backend", "api", "routes", "controllers", "services", "models", "src/main", "server", "database", "src", "py", "js", "ts"])
        elif frontend_signals or ("portfolio" in goal_lower and not backend_signals):
            domain = "frontend development"
            objective = user_goal
            desired_outcome = "Implement responsive UI components and styling"
            allowed_scope.extend(["src", "frontend", "components", "pages", "app", "css", "jsx", "tsx", "js", "html", "public", "styles"])
        elif doc_signals:
            domain = "document processing"
            objective = user_goal
            desired_outcome = "Generate, process, and export requested documents"
            allowed_scope.extend(["report", "pdf", "generator", "export", "docs", "data"])
        elif devops_signals:
            domain = "devops & infrastructure"
            objective = user_goal
            desired_outcome = "Configure containers, deployment pipelines, and environment scripts"
            allowed_scope.extend(["docker", "k8s", "scripts", "config", "deploy"])
        else:
            domain = "general software development"
            objective = user_goal
            desired_outcome = f"Accomplish {user_goal}"
            allowed_scope.extend(["src", "app", "docs", "scripts"])

        # Dynamically append specifically mentioned files/paths
        for file in extracted_files:
            allowed_scope.append(file)

        for keyword in ["routes", "portfolio", "auth", "login", "models", "database"]:
            if keyword in goal_lower and keyword not in restricted_scope:
                allowed_scope.append(keyword)

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

        # Generate Sub-Goals hierarchy
        sub_goals = self._generate_sub_goals_for_domain(domain, user_goal)

        return {
            # Formal User Intent Model fields
            "original_goal": user_goal,
            "objective": objective if 'objective' in locals() else user_goal,
            "domain": domain,
            "entities": entities,
            "desired_outcome": desired_outcome if 'desired_outcome' in locals() else user_goal,
            "constraints": list(set(constraints)),
            "negative_constraints": list(set(negative_constraints)),
            "allowed_domains": list(dict.fromkeys(allowed_domains)),
            "allowed_action_categories": list(dict.fromkeys(allowed_actions)),
            "sensitive_action_categories": list(dict.fromkeys(sensitive_actions)),
            "forbidden_action_categories": list(dict.fromkeys(forbidden_actions)),
            "financial_authority": financial_auth,
            "external_communication_authority": comm_auth,
            "personal_data_authority": personal_auth,
            "goal_version": 1,
            "sub_goals": sub_goals,

            # Backward-compatible fields
            "technologies": technologies,
            "requirements": [user_goal],
            "allowedScope": list(dict.fromkeys(allowed_scope)),
            "restrictedScope": list(dict.fromkeys(restricted_scope)),
            "sensitiveOperations": list(set(sensitive_ops)),
            "isAmbiguous": len(user_goal.strip()) < 10 or "better" in goal_lower
        }

    def _generate_sub_goals_for_domain(self, domain: str, goal_text: str) -> List[Dict[str, Any]]:
        """Generate an ordered hierarchy of sub-goals for the specific task domain."""
        domain_lower = domain.lower()

        if "flight" in domain_lower:
            return [
                {"id": "SG-1", "name": "Search flights", "description": "Search available flights matching origin, destination, and date", "order": 1, "status": "ACTIVE", "allowedActions": ["BROWSER_SEARCH", "BROWSER_NAVIGATE", "API_REQUEST"]},
                {"id": "SG-2", "name": "Compare flights", "description": "Compare flight prices, durations, and layovers", "order": 2, "status": "PENDING", "allowedActions": ["BROWSER_NAVIGATE", "BROWSER_SEARCH", "API_REQUEST"]},
                {"id": "SG-3", "name": "Select flight", "description": "Choose the optimal flight meeting user criteria", "order": 3, "status": "PENDING", "allowedActions": ["BROWSER_CLICK", "BROWSER_NAVIGATE", "GENERAL_ACTION"]},
                {"id": "SG-4", "name": "Enter passenger details", "description": "Fill passenger name, contact information, and travel details", "order": 4, "status": "PENDING", "allowedActions": ["BROWSER_TYPE", "FILL_FORM", "GENERAL_ACTION"]},
                {"id": "SG-5", "name": "Select seat", "description": "Choose available seats and baggage options", "order": 5, "status": "PENDING", "allowedActions": ["BROWSER_CLICK", "GENERAL_ACTION"]},
                {"id": "SG-6", "name": "Review booking", "description": "Verify flight summary, passenger details, and fare breakdown", "order": 6, "status": "PENDING", "allowedActions": ["BROWSER_NAVIGATE", "FILE_READ", "GENERAL_ACTION"]},
                {"id": "SG-7", "name": "Payment & Confirmation", "description": "Execute payment and receive booking confirmation", "order": 7, "status": "PENDING", "allowedActions": ["EXTERNAL_TRANSACTION", "PAYMENT"]}
            ]
        elif "hotel" in domain_lower:
            return [
                {"id": "SG-1", "name": "Search hotels", "description": "Search accommodations in target destination", "order": 1, "status": "ACTIVE", "allowedActions": ["BROWSER_SEARCH", "BROWSER_NAVIGATE", "API_REQUEST"]},
                {"id": "SG-2", "name": "Compare amenities & reviews", "description": "Evaluate hotel ratings, amenities, and locations", "order": 2, "status": "PENDING", "allowedActions": ["BROWSER_NAVIGATE", "API_REQUEST"]},
                {"id": "SG-3", "name": "Select room type", "description": "Choose room category and cancellation terms", "order": 3, "status": "PENDING", "allowedActions": ["BROWSER_CLICK", "GENERAL_ACTION"]},
                {"id": "SG-4", "name": "Enter guest information", "description": "Fill guest names and check-in requirements", "order": 4, "status": "PENDING", "allowedActions": ["BROWSER_TYPE", "FILL_FORM"]},
                {"id": "SG-5", "name": "Review reservation", "description": "Verify reservation dates, guest count, and pricing", "order": 5, "status": "PENDING", "allowedActions": ["BROWSER_NAVIGATE", "GENERAL_ACTION"]},
                {"id": "SG-6", "name": "Payment & Confirmation", "description": "Process reservation deposit or full payment", "order": 6, "status": "PENDING", "allowedActions": ["EXTERNAL_TRANSACTION", "PAYMENT"]}
            ]
        elif "shopping" in domain_lower or "commerce" in domain_lower:
            return [
                {"id": "SG-1", "name": "Search products", "description": "Search item listings across authorized shopping sites", "order": 1, "status": "ACTIVE", "allowedActions": ["BROWSER_SEARCH", "BROWSER_NAVIGATE", "API_REQUEST"]},
                {"id": "SG-2", "name": "Compare prices & specifications", "description": "Compare seller prices, shipping times, and reviews", "order": 2, "status": "PENDING", "allowedActions": ["BROWSER_NAVIGATE", "API_REQUEST"]},
                {"id": "SG-3", "name": "Select product & Add to cart", "description": "Add chosen product variant to shopping cart", "order": 3, "status": "PENDING", "allowedActions": ["BROWSER_CLICK", "GENERAL_ACTION"]},
                {"id": "SG-4", "name": "Enter shipping address", "description": "Provide delivery location and contact number", "order": 4, "status": "PENDING", "allowedActions": ["BROWSER_TYPE", "FILL_FORM"]},
                {"id": "SG-5", "name": "Review order summary", "description": "Review items, taxes, shipping fee, and total amount", "order": 5, "status": "PENDING", "allowedActions": ["BROWSER_NAVIGATE", "GENERAL_ACTION"]},
                {"id": "SG-6", "name": "Payment & Checkout", "description": "Complete purchase through checkout payment gateway", "order": 6, "status": "PENDING", "allowedActions": ["EXTERNAL_TRANSACTION", "PAYMENT"]}
            ]
        elif "email" in domain_lower or "communication" in domain_lower:
            return [
                {"id": "SG-1", "name": "Draft email message", "description": "Compose subject line and body text", "order": 1, "status": "ACTIVE", "allowedActions": ["FILE_WRITE", "GENERAL_ACTION", "BROWSER_TYPE"]},
                {"id": "SG-2", "name": "Verify recipient & subject", "description": "Verify recipient email address against authorized policy", "order": 2, "status": "PENDING", "allowedActions": ["FILE_READ", "GENERAL_ACTION"]},
                {"id": "SG-3", "name": "Attach relevant documents", "description": "Attach requested report or files if required", "order": 3, "status": "PENDING", "allowedActions": ["FILE_READ", "GENERAL_ACTION"]},
                {"id": "SG-4", "name": "Review email content", "description": "Inspect final email draft before transmission", "order": 4, "status": "PENDING", "allowedActions": ["FILE_READ", "GENERAL_ACTION"]},
                {"id": "SG-5", "name": "Send email", "description": "Transmit email to recipient through mail service", "order": 5, "status": "PENDING", "allowedActions": ["EXTERNAL_COMMUNICATION", "API_REQUEST"]}
            ]
        elif "frontend" in domain_lower or "react" in domain_lower:
            return [
                {"id": "SG-1", "name": "Explore project structure", "description": "Inspect existing files, components, and styling configurations", "order": 1, "status": "ACTIVE", "allowedActions": ["FILE_READ", "BROWSER_SEARCH"]},
                {"id": "SG-2", "name": "Implement UI components", "description": "Create and update React/HTML components", "order": 2, "status": "PENDING", "allowedActions": ["FILE_WRITE", "FILE_READ"]},
                {"id": "SG-3", "name": "Apply styling & assets", "description": "Configure CSS, Tailwind, or visual themes", "order": 3, "status": "PENDING", "allowedActions": ["FILE_WRITE", "FILE_READ"]},
                {"id": "SG-4", "name": "Verify build & test UI", "description": "Run tests and verify build integrity", "order": 4, "status": "PENDING", "allowedActions": ["COMMAND_EXECUTION", "FILE_READ"]}
            ]
        elif "backend" in domain_lower or "fullstack" in domain_lower:
            return [
                {"id": "SG-1", "name": "Inspect endpoints & schema", "description": "Review API routes, data models, and database schema", "order": 1, "status": "ACTIVE", "allowedActions": ["FILE_READ"]},
                {"id": "SG-2", "name": "Implement backend logic", "description": "Write API routes, controllers, and service handlers", "order": 2, "status": "PENDING", "allowedActions": ["FILE_WRITE", "FILE_READ"]},
                {"id": "SG-3", "name": "Configure data persistence", "description": "Set up database models and queries safely", "order": 3, "status": "PENDING", "allowedActions": ["FILE_WRITE", "FILE_READ"]},
                {"id": "SG-4", "name": "Run unit & integration tests", "description": "Execute test suite to confirm functionality", "order": 4, "status": "PENDING", "allowedActions": ["COMMAND_EXECUTION", "FILE_READ"]}
            ]
        else:
            return [
                {"id": "SG-1", "name": "Explore & Gather Context", "description": "Investigate required tools and reference data", "order": 1, "status": "ACTIVE", "allowedActions": ["FILE_READ", "BROWSER_SEARCH", "API_REQUEST"]},
                {"id": "SG-2", "name": "Execute Core Task Operations", "description": "Perform primary authorized actions towards user objective", "order": 2, "status": "PENDING", "allowedActions": ["FILE_WRITE", "COMMAND_EXECUTION", "GENERAL_ACTION"]},
                {"id": "SG-3", "name": "Verify Results", "description": "Validate task output against user requirements", "order": 3, "status": "PENDING", "allowedActions": ["FILE_READ", "COMMAND_EXECUTION"]}
            ]
