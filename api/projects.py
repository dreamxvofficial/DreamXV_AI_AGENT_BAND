from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Ensure backend package can be imported by adding the root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.band_manager import BandManager

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/projects")
@app.get("/")
async def list_projects():
    manager = BandManager()
    projects = manager.list_projects()
    summaries = [
        {
            "project_id": p["project_id"],
            "title": p.get("title", "Untitled"),
            "created_at": p.get("created_at", ""),
            "status": p.get("status", "completed"),
        }
        for p in projects
    ]
    return {
        "projects": summaries,
        "total": len(summaries)
    }
