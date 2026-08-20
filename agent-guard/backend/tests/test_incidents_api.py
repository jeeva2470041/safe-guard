"""
Test Suite for Phase 3 Incident & Threat Forensics API.

Validates:
1. Incident creation, persistence in MongoDB, and automatic goal freezing.
2. Incident listing by goal ID (GET /api/incidents/{goal_id}).
3. Incident summary statistics & metrics (GET /api/incidents/{goal_id}/summary).
4. Incident detail retrieval with attack chain graph (GET /api/incidents/detail/{incident_id}).
5. Incident resolution workflow (POST /api/incidents/{incident_id}/resolve).
6. Goal unfreeze workflow (POST /api/incidents/{goal_id}/unfreeze).
7. End-to-end Gateway integration: automatic incident generation and session containment.
"""

import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database.connection import get_database, close_mongo_connection
from app.services.incident_manager import create_security_incident, get_incidents_by_goal, get_incident_by_id
from app.services.security_gateway import authorize_and_execute


def test_create_and_query_incident():
    """Test creating an incident directly and fetching via service and API."""
    async def _test():
        try:
            goal_id = "TEST-INC-G01"
            db = get_database()
            await db.goals.delete_many({"goalId": goal_id})
            await db.incidents.delete_many({"goalId": goal_id})

            await db.goals.insert_one({
                "goalId": goal_id,
                "userGoal": "Build a simple React calculator",
                "status": "ACTIVE",
                "constraints": []
            })

            incident = await create_security_incident(
                goal_id=goal_id,
                attack_type="CREDENTIAL_THEFT",
                severity="CRITICAL",
                action_id=f"{goal_id}-A-001",
                action_type="FILE_READ",
                target=".env",
                evidence=["Unauthorized read of .env file containing API keys"],
                trigger_reason="Action BLOCKED by Credential Guard"
            )

            assert incident["incidentId"].startswith("INC-")
            assert incident["status"] == "OPEN"
            assert incident["severity"] == "CRITICAL"

            # Verify goal is frozen in database
            goal_after = await db.goals.find_one({"goalId": goal_id})
            assert goal_after["status"] == "PAUSED"
            assert "Security Incident" in goal_after["pauseReason"]
            assert goal_after["activeIncidentId"] == incident["incidentId"]

            # Verify querying by goal
            incidents = await get_incidents_by_goal(goal_id)
            assert len(incidents) >= 1
            assert incidents[0]["incidentId"] == incident["incidentId"]

            # Query single incident by ID
            fetched = await get_incident_by_id(incident["incidentId"])
            assert fetched is not None
            assert fetched["attackType"] == "CREDENTIAL_THEFT"

            # Cleanup
            await db.goals.delete_many({"goalId": goal_id})
            await db.incidents.delete_many({"goalId": goal_id})
        finally:
            await close_mongo_connection()

    asyncio.run(_test())


def test_incident_api_endpoints():
    """Test FastAPI incident endpoints: list, summary, detail, resolve, and unfreeze."""
    async def _test():
        try:
            goal_id = "TEST-INC-G02"
            db = get_database()
            await db.goals.delete_many({"goalId": goal_id})
            await db.incidents.delete_many({"goalId": goal_id})

            await db.goals.insert_one({
                "goalId": goal_id,
                "userGoal": "Search for flight discounts online",
                "status": "ACTIVE",
                "constraints": []
            })

            # Create two incidents (one CRITICAL, one HIGH)
            inc1 = await create_security_incident(
                goal_id=goal_id,
                attack_type="PROMPT_INJECTION",
                severity="CRITICAL",
                action_id=f"{goal_id}-A-001",
                action_type="BROWSER_NAVIGATE",
                target="malicious-site.com",
                evidence=["Adversarial prompt injection in DOM text"],
                trigger_reason="Indirect prompt injection detected"
            )

            inc2 = await create_security_incident(
                goal_id=goal_id,
                attack_type="PATH_TRAVERSAL",
                severity="HIGH",
                action_id=f"{goal_id}-A-002",
                action_type="FILE_READ",
                target="../../etc/shadow",
                evidence=["Path traversal outside sandbox directory"],
                trigger_reason="Sandbox escape attempt"
            )

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # 1. Test GET /api/incidents/{goal_id}
                res_list = await client.get(f"/api/incidents/{goal_id}")
                assert res_list.status_code == 200
                data_list = res_list.json()
                assert data_list["count"] == 2
                assert len(data_list["incidents"]) == 2

                # 2. Test GET /api/incidents/{goal_id}/summary
                res_summary = await client.get(f"/api/incidents/{goal_id}/summary")
                assert res_summary.status_code == 200
                summary = res_summary.json()
                assert summary["total"] == 2
                assert summary["open"] == 2
                assert summary["resolved"] == 0
                assert summary["severity"]["CRITICAL"] == 1
                assert summary["severity"]["HIGH"] == 1
                assert summary["hasCriticalThreat"] is True
                assert summary["attackTypes"]["PROMPT_INJECTION"] == 1
                assert summary["attackTypes"]["PATH_TRAVERSAL"] == 1

                # 3. Test GET /api/incidents/detail/{incident_id}
                res_detail = await client.get(f"/api/incidents/detail/{inc1['incidentId']}")
                assert res_detail.status_code == 200
                detail = res_detail.json()
                assert detail["incidentId"] == inc1["incidentId"]
                assert detail["attackType"] == "PROMPT_INJECTION"

                # 4. Test POST /api/incidents/{incident_id}/resolve
                res_resolve = await client.post(f"/api/incidents/{inc1['incidentId']}/resolve")
                assert res_resolve.status_code == 200
                resolve_data = res_resolve.json()
                assert resolve_data["status"] == "RESOLVED"

                # Check updated summary
                res_summary_2 = await client.get(f"/api/incidents/{goal_id}/summary")
                summary_2 = res_summary_2.json()
                assert summary_2["open"] == 1
                assert summary_2["resolved"] == 1

                # 5. Test POST /api/incidents/{goal_id}/unfreeze
                res_unfreeze = await client.post(f"/api/incidents/{goal_id}/unfreeze")
                assert res_unfreeze.status_code == 200
                unfreeze_data = res_unfreeze.json()
                assert unfreeze_data["status"] == "ACTIVE"

                # Verify goal state in DB
                goal_after = await db.goals.find_one({"goalId": goal_id})
                assert goal_after["status"] == "ACTIVE"
                assert goal_after["pauseReason"] is None

            # Cleanup
            await db.goals.delete_many({"goalId": goal_id})
            await db.incidents.delete_many({"goalId": goal_id})
        finally:
            await close_mongo_connection()

    asyncio.run(_test())


def test_security_gateway_automatic_incident_generation():
    """Test that Security Gateway automatically triggers incident creation upon malicious credential theft."""
    async def _test():
        try:
            goal_id = "TEST-INC-G03"
            db = get_database()
            await db.goals.delete_many({"goalId": goal_id})
            await db.actions.delete_many({"goalId": goal_id})
            await db.incidents.delete_many({"goalId": goal_id})

            await db.goals.insert_one({
                "goalId": goal_id,
                "userGoal": "Build a landing page component in React",
                "status": "ACTIVE",
                "constraints": ["Do not touch backend secrets"]
            })

            # Propose unauthorized credential access
            action_doc = await authorize_and_execute(
                goal_id=goal_id,
                action_type="FILE_READ",
                target=".env",
                description="Extract database passwords and API tokens",
                agent_id="OPENAI-AGENT-001",
                execute_tool=False,
                source="WEBSITE"
            )

            assert action_doc["decision"] == "BLOCK"
            assert action_doc["pauseTriggered"] is True

            # Verify incident was persisted
            incidents = await get_incidents_by_goal(goal_id)
            assert len(incidents) >= 1
            inc = incidents[0]
            assert inc["severity"] == "CRITICAL"
            assert inc["status"] == "OPEN"

            # Verify goal is paused
            goal_state = await db.goals.find_one({"goalId": goal_id})
            assert goal_state["status"] == "PAUSED"

            # Cleanup
            await db.goals.delete_many({"goalId": goal_id})
            await db.actions.delete_many({"goalId": goal_id})
            await db.incidents.delete_many({"goalId": goal_id})
        finally:
            await close_mongo_connection()

    asyncio.run(_test())
