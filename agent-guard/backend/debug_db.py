import asyncio
from app.database.connection import get_database

async def check():
    db = get_database()
    print("=== SESSIONS ===")
    sessions = await db.agent_sessions.find({}).to_list(10)
    for s in sessions:
        print(s)
    
    print("\n=== RECENT GOALS ===")
    goals = await db.goals.find({}).sort("createdAt", -1).to_list(10)
    for g in goals:
        print(g.get("goalId"), g.get("status"), g.get("createdAt"), g.get("userGoal")[:30])
    
    print("\n=== ALL ACTIONS ===")
    actions = await db.actions.find({}).sort("timestamp", -1).to_list(20)
    for a in actions:
        print(a.get("goalId"), a.get("actionId"), a.get("actionType"), a.get("target"), a.get("decision"))

if __name__ == "__main__":
    asyncio.run(check())
