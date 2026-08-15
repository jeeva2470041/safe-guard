"""
Agent Guard — FastAPI Application Entry Point

Runtime Goal-Integrity and Action Authorization for Autonomous AI Agents.
Version 1 Prototype with Simulated Agent.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.connection import connect_to_mongo, close_mongo_connection
from app.api.goals import router as goals_router
from app.api.actions import router as actions_router
from app.api.interception import router as interception_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: connect to MongoDB on startup, close on shutdown."""
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title="Agent Guard",
    description="Runtime Goal-Integrity and Action Authorization for Autonomous AI Agents",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration — allow the Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(goals_router)
app.include_router(actions_router)
app.include_router(interception_router)


@app.get("/")
async def root():
    return {
        "app": "Agent Guard",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
