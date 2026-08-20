"""
Async MongoDB connection using Motor.
Reads MONGODB_URI and DATABASE_NAME from environment variables.
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

client: AsyncIOMotorClient = None
db = None


def get_mongo_uri() -> str:
    """Get the current MongoDB connection URI from environment."""
    load_dotenv()
    return os.getenv(
        "MONGODB_URI",
        "mongodb+srv://ecofood:JeevaPriya2006@ecofoodcluster.dgo2kvl.mongodb.net/?appName=ecofoodcluster"
    )


def get_db_name() -> str:
    """Get the database name from environment."""
    load_dotenv()
    return os.getenv("DATABASE_NAME", "agent_guard")


async def connect_to_mongo():
    """Initialize the MongoDB client and database reference with index creation."""
    global client, db
    uri = get_mongo_uri()
    db_name = get_db_name()

    try:
        # Create async client with reasonable timeout settings
        client = AsyncIOMotorClient(
            uri,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
        )
        db = client[db_name]

        # Verify connectivity by issuing a ping
        await client.admin.command("ping")
        print(f"Connected to MongoDB Atlas: {db_name}")

        # Create indexes for efficient querying
        await db.goals.create_index("goalId", unique=True)
        await db.actions.create_index("goalId")
        await db.actions.create_index("actionId", unique=True)
        await db.audit_logs.create_index("actionId")
        await db.audit_logs.create_index("goalId")

    except Exception as e:
        print(f"MongoDB connection warning/error: {e}")
        # Retain client and db instance so operations can retry or surface errors cleanly
        if client is None:
            client = AsyncIOMotorClient(uri)
            db = client[db_name]


async def close_mongo_connection():
    """Close the MongoDB client connection."""
    global client, db
    if client:
        client.close()
        client = None
        db = None
        print("MongoDB connection closed.")


def get_database():
    """Return the database instance."""
    global client, db
    if db is None:
        uri = get_mongo_uri()
        db_name = get_db_name()
        client = AsyncIOMotorClient(uri)
        db = client[db_name]
    return db
