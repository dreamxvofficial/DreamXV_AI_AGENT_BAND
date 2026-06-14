from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Ensure backend package can be imported by adding the root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/agents")
@app.get("/api/agent-status")
@app.get("/")
async def agent_status(project_id: str = None):
    # Return a dummy list of completed agents to prevent polling exceptions
    return {
        "project_id": project_id or "pending",
        "agents": [
            {"agent_name": "Chief Agent", "status": "completed"},
            {"agent_name": "Story Agent", "status": "completed"},
            {"agent_name": "Character Agent", "status": "completed"},
            {"agent_name": "World Agent", "status": "completed"},
            {"agent_name": "Gameplay Agent", "status": "completed"},
            {"agent_name": "Art Agent", "status": "completed"},
            {"agent_name": "QA Agent", "status": "completed"}
        ]
    }
