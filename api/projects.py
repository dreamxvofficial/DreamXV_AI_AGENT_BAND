from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
import sys

# Ensure backend package can be imported by adding the root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.supabase_service import SupabaseService

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = SupabaseService()


@app.get("/api/projects")
@app.get("/")
async def get_projects(
    user_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None)
):
    # 1. If project_id is requested, return full details of that project
    if project_id:
        project_record = db.get_project(project_id)
        if not project_record:
            return {"success": False, "error": f"Project '{project_id}' not found."}

        # In Supabase, the full project dictionary is stored under "project_json"
        project_data = project_record.get("project_json", {})

        # Ensure project_id matches what is requested
        if isinstance(project_data, dict):
            project_data["project_id"] = project_id

        return {
            "success": True,
            "project": project_data,
            "data": project_data
        }

    # 2. Otherwise, list all projects, optionally filtering by user_id
    projects = db.list_projects(user_id=user_id)

    summaries = []
    for p in projects:
        proj_json = p.get("project_json", {})
        proj_id = proj_json.get("project_id") or p.get("id")
        created = p.get("created_at")
        created_str = created.isoformat() if hasattr(created, "isoformat") else (str(created) if created else "")

        summaries.append({
            "project_id": proj_id,
            "title": p.get("title") or proj_json.get("title") or "Untitled",
            "created_at": created_str,
            "status": proj_json.get("status") or "completed",
        })

    return {
        "projects": summaries,
        "total": len(summaries)
    }
