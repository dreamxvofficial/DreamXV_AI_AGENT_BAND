from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import sys
import traceback
import uuid
import zipfile
import io
import json
import base64

# Ensure backend package can be imported by adding the root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.supabase_service import SupabaseService
from backend.services.llm_service import LLMService
from backend.agents.atlas_agent import AtlasAgent
from backend.models.output_models import AtlasOutput, AtlasPhase, AtlasTaskBreakdown

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = SupabaseService()
llm = LLMService()

class AtlasRequest(BaseModel):
    project_id: str
    duration: str
    tools: str
    atlas_id: Optional[str] = None  # Optional parameter to allow regeneration in-place

class DuplicateRequest(BaseModel):
    atlas_id: str

def get_atlas_fallback(project_id: str, duration: str, tools: str) -> AtlasOutput:
    # Handle environment styling check for fallback
    is_web = any(term in tools.lower() for term in ["web", "react", "html", "css", "node", "django", "fastapi", "flask", "js", "ts", "supabase"])
    
    if is_web:
        return AtlasOutput(
            project_id=project_id,
            roadmap=[
                AtlasPhase(name="Phase 1: Project Setup", tasks=["Setup repository", "Initialize frontend & backend folders", "Configure Tailwind/CSS & database client"]),
                AtlasPhase(name="Phase 2: Database & Auth", tasks=["Define Supabase/PostgreSQL schema", "Implement signup/login routes", "Connect auth sessions on frontend"]),
                AtlasPhase(name="Phase 3: Core API Features", tasks=["Create endpoints for project storage", "Build user dashboards", "Wire state management"]),
                AtlasPhase(name="Phase 4: Polish & Deployment", tasks=["Add error boundaries", "Deploy frontend to Vercel/Netlify", "Perform end-to-end user tests"])
            ],
            project_structure=[
                "frontend/",
                "frontend/src/",
                "frontend/src/components/",
                "frontend/src/App.jsx",
                "backend/",
                "backend/api/",
                "backend/main.py",
                "database/",
                "database/schema.sql",
                "docs/",
                "docs/Roadmap.md",
                "README.md"
            ],
            production_flow_map=[
                "Design UI Mockups",
                "Create Database Schema",
                "Build API Server",
                "Connect React Frontend",
                "Setup Authentication Flow",
                "Deploy Application"
            ],
            dependency_map=[
                "Database -> API Service -> Auth Middleware -> Frontend Component"
            ],
            task_breakdown=AtlasTaskBreakdown(
                critical_tasks=["Setup Git repository", "Create responsive dashboard", "Write database models"],
                optional_tasks=["Add light/dark mode theme", "Configure toast notifications"],
                future_expansion=["Implement automated testing", "Integrate caching layers"]
            )
        )
    else:
        return AtlasOutput(
            project_id=project_id,
            roadmap=[
                AtlasPhase(name="Phase 1: Project Setup", tasks=["Setup game repository", "Configure asset folders in engine", "Import style guide colors"]),
                AtlasPhase(name="Phase 2: Core Mechanics", tasks=["Implement player controller", "Create spawning logic", "Build core gameplay loops"]),
                AtlasPhase(name="Phase 3: Level Design & Art", tasks=["Build environments & layouts", "Place NPC landmarks", "Configure lighting & sound effects"]),
                AtlasPhase(name="Phase 4: Game Polish & Export", tasks=["Perform QA playtesting", "Optimize frames/performance", "Generate final package builds"])
            ],
            project_structure=[
                "Assets/",
                "Assets/Scripts/",
                "Assets/Prefabs/",
                "Assets/Materials/",
                "Assets/Animations/",
                "Assets/Scenes/",
                "Docs/",
                "Docs/GDD.md",
                "Docs/Roadmap.md",
                "Docs/Tasks.md",
                "README.md"
            ],
            production_flow_map=[
                "Create Asset Designs",
                "Rig & Animate Assets",
                "Import to Engine",
                "Attach Scripts & Physics",
                "Configure Gameplay HUD",
                "Export Distribution Package"
            ],
            dependency_map=[
                "InputManager -> PlayerController -> CombatSystem -> GameHUD"
            ],
            task_breakdown=AtlasTaskBreakdown(
                critical_tasks=["Map camera behaviors", "Code primary action/move behaviors", "Ensure stable launch build"],
                optional_tasks=["Design simple settings panel", "Add ambient sound layers"],
                future_expansion=["Create secondary levels", "Deploy multi-platform exports"]
            )
        )

def compile_markdown_files(title: str, atlas_out: AtlasOutput) -> dict:
    # 1. README.md
    readme = f"# {title} — Production Plan\n\n"
    readme += "Generated by DreamXV Atlas AI Planner.\n\n"
    readme += "This archive contains the complete production layout, development roadmap, workflow maps, and source directories.\n"
    
    # 2. Roadmap.md
    roadmap_md = "# Development Roadmap\n\n"
    for phase in (atlas_out.roadmap or []):
        roadmap_md += f"## {phase.name}\n"
        for task in (phase.tasks or []):
            roadmap_md += f"- [ ] {task}\n"
        roadmap_md += "\n"
        
    # 3. Tasks.md
    tasks_md = "# Project Tasks\n\n"
    tb = atlas_out.task_breakdown
    crit = tb.critical_tasks or []
    opt = tb.optional_tasks or []
    exp = tb.future_expansion or []
    
    tasks_md += "## Critical Path Tasks (MVP)\n"
    for t in crit:
        tasks_md += f"- [ ] {t}\n"
    tasks_md += "\n## Optional Tasks\n"
    for t in opt:
        tasks_md += f"- [ ] {t}\n"
    tasks_md += "\n## Future Expansion\n"
    for t in exp:
        tasks_md += f"- [ ] {t}\n"
        
    # 4. FlowMap.md
    flow_md = "# Production Workflow & Dependencies\n\n"
    flow_md += "## Step-by-Step Workflow\n"
    flow_steps = atlas_out.production_flow_map or []
    for idx, step in enumerate(flow_steps):
        flow_md += f"{idx + 1}. {step}\n"
    flow_md += "\n## Core Dependency Graph\n"
    dep_map = atlas_out.dependency_map or []
    for dep in dep_map:
        flow_md += f"- {dep}\n"
        
    # 5. Structure.md
    struct_md = "# Project Directory Structure\n\n"
    struct_md += "Below is the folder and file layout designed for this project:\n\n```\n"
    struct_list = atlas_out.project_structure or []
    struct_md += "\n".join(struct_list)
    struct_md += "\n```\n"
    
    return {
        "README.md": readme,
        "Roadmap.md": roadmap_md,
        "FlowMap.md": flow_md,
        "Tasks.md": tasks_md,
        "Structure.md": struct_md
    }

def create_atlas_zip_on_disk(atlas_id: str, atlas_data: dict, images: list[dict]) -> str:
    # Try writing to public/exports/atlas/ first, fallback to /tmp/ if read-only
    zip_dir = "public/exports/atlas"
    try:
        os.makedirs(zip_dir, exist_ok=True)
        zip_path = f"{zip_dir}/{atlas_id}.zip"
        # Test write capability
        with open(zip_path, "wb") as f:
            f.write(b"")
    except Exception:
        zip_dir = "/tmp"
        os.makedirs(zip_dir, exist_ok=True)
        zip_path = f"{zip_dir}/{atlas_id}.zip"

    with open(zip_path, "wb") as f_out:
        with zipfile.ZipFile(f_out, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # 1. /docs/ README, Roadmap, FlowMap, Tasks, Structure
            gen_files = atlas_data.get("generated_files") or {}
            for name, content in gen_files.items():
                zip_file.writestr(f"docs/{name}", content or "")
                
            # 2. /art/ AI images
            for idx, img in enumerate(images):
                img_url = img.get("image_url", "")
                if not img_url:
                    continue
                img_bytes = None
                if img_url.startswith("data:image/"):
                    try:
                        header, encoded = img_url.split(",", 1)
                        img_bytes = base64.b64decode(encoded)
                    except Exception as e:
                        print(f"Error decoding base64 image {idx}: {e}")
                elif img_url.startswith("http://") or img_url.startswith("https://"):
                    try:
                        import urllib.request
                        with urllib.request.urlopen(img_url, timeout=10) as response:
                            img_bytes = response.read()
                    except Exception as e:
                        print(f"Error downloading image {idx} from URL: {e}")
                else:
                    try:
                        if os.path.exists(img_url):
                            with open(img_url, "rb") as img_f:
                                img_bytes = img_f.read()
                    except Exception as e:
                        print(f"Error reading image {idx} from path: {e}")
                
                if img_bytes:
                    zip_file.writestr(f"art/concept_{idx+1}.png", img_bytes)
                        
            # 3. /project_structure/ Generated empty folders
            project_structure = atlas_data.get("structure") or []
            for path in project_structure:
                cleaned_path = path.strip()
                if cleaned_path.endswith("/"):
                    zip_file.writestr(f"project_structure/{cleaned_path}", "")
                else:
                    zip_file.writestr(f"project_structure/{cleaned_path}", f"# Placeholder for {cleaned_path.split('/')[-1]}\n")
                    
            # 4. metadata.json
            metadata = {
                "atlas_id": atlas_id,
                "source_project_id": atlas_data.get("source_project_id"),
                "title": atlas_data.get("title"),
                "duration": atlas_data.get("duration"),
                "tools": atlas_data.get("tools"),
                "created_at": str(atlas_data.get("created_at") or "")
            }
            zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))
            
    return zip_path

@app.post("/api/atlas/generate")
@app.post("/api/atlas")
@app.post("/")
async def generate_atlas(req: AtlasRequest):
    try:
        # Fetch project details from database
        project_record = db.get_project(req.project_id)
        if not project_record:
            # Fallback mock data structure for testing or local mode
            project_data = {
                "project_id": req.project_id,
                "title": "Mock Adventure Project",
                "story": {"summary": "A sample post-apocalyptic tactical zombie game"},
                "world": {"description": "A dark ruined city environment"},
                "characters": [{"name": "Hero", "role": "Protagonist", "backstory": "A survivor"}],
                "gameplay": {"core_loop": "Scavenge resources and shoot zombies"},
                "qa": {"overall_assessment": "High consistency"},
                "documentation": {"elevator_pitch": "Survival RPG", "technical_summary": "Built with core engine"}
            }
        else:
            project_data = project_record.get("project_json", {})
            if not isinstance(project_data, dict):
                project_data = {}
            project_data["project_id"] = req.project_id
            project_data["title"] = project_record.get("title") or "Untitled Project"

        agent = AtlasAgent(llm)
        try:
            atlas_out = await agent.run(
                project_data=project_data,
                duration=req.duration,
                tools=req.tools
            )
        except Exception as agent_exc:
            print(f"Atlas agent generation failed: {agent_exc}. Triggering fallback.")
            atlas_out = get_atlas_fallback(req.project_id, req.duration, req.tools)

        # 1. Compile 5 markdown files
        title = project_data.get("title") or "Untitled Project"
        generated_files = compile_markdown_files(title, atlas_out)

        # 2. Determine Atlas ID
        atlas_id = req.atlas_id if req.atlas_id else str(uuid.uuid4())

        # 3. Create the Atlas data dictionary for saving & ZIP generation
        user_id = project_record.get("user_id") if project_record else "spotifysahir007@gmail.com"
        atlas_data = {
            "title": title,
            "duration": req.duration,
            "tools": req.tools,
            "source_project_id": req.project_id,
            "roadmap": [phase.model_dump() if hasattr(phase, "model_dump") else phase for phase in atlas_out.roadmap],
            "structure": atlas_out.project_structure,
            "flow_map": atlas_out.production_flow_map,
            "dependency_map": atlas_out.dependency_map,
            "tasks": atlas_out.task_breakdown.model_dump() if hasattr(atlas_out.task_breakdown, "model_dump") else atlas_out.task_breakdown,
            "generated_files": generated_files
        }

        # 4. Fetch source project images (if available)
        images = []
        if project_record:
            images = db.get_project_images(req.project_id)

        # 5. Build ZIP file on backend
        zip_path = create_atlas_zip_on_disk(atlas_id, atlas_data, images)

        # 6. Save in Supabase
        db.save_atlas_project(
            atlas_id=atlas_id,
            user_id=user_id,
            source_project_id=req.project_id,
            title=title,
            duration=req.duration,
            tools=req.tools,
            roadmap=atlas_data["roadmap"],
            structure=atlas_data["structure"],
            flow_map=atlas_data["flow_map"],
            dependency_map=atlas_data["dependency_map"],
            tasks=atlas_data["tasks"],
            generated_files=generated_files,
            zip_path=zip_path
        )

        return {
            "success": True,
            "atlas": {
                "id": atlas_id,
                **atlas_data,
                "project_structure": atlas_data["structure"],
                "production_flow_map": atlas_data["flow_map"],
                "task_breakdown": atlas_data["tasks"]
            }
        }
    except Exception as e:
        tb = traceback.format_exc()
        return {
            "success": False,
            "error": str(e),
            "traceback": tb
        }

@app.get("/api/atlas/download")
async def download_atlas(atlas_id: str):
    atlas = db.get_atlas_project(atlas_id)
    if not atlas:
        raise HTTPException(status_code=404, detail="Atlas project not found")
        
    zip_path = atlas.get("zip_path")
    if zip_path and os.path.exists(zip_path):
        return FileResponse(zip_path, media_type="application/zip", filename=f"{atlas_id}_atlas_production_kit.zip")
        
    # If file missing on disk (Stateless deployment), regenerate it on the fly!
    images = []
    source_project_id = atlas.get("source_project_id")
    if source_project_id:
        images = db.get_project_images(source_project_id)
        
    new_zip_path = create_atlas_zip_on_disk(atlas_id, atlas, images)
    
    # Save the updated path in Supabase
    db.save_atlas_project(
        atlas_id=atlas_id,
        user_id=atlas.get("user_id"),
        source_project_id=source_project_id,
        title=atlas.get("title"),
        duration=atlas.get("duration"),
        tools=atlas.get("tools"),
        roadmap=atlas.get("roadmap"),
        structure=atlas.get("structure"),
        flow_map=atlas.get("flow_map"),
        dependency_map=atlas.get("dependency_map"),
        tasks=atlas.get("tasks"),
        generated_files=atlas.get("generated_files"),
        zip_path=new_zip_path
    )
    
    return FileResponse(new_zip_path, media_type="application/zip", filename=f"{atlas_id}_atlas_production_kit.zip")

@app.post("/api/atlas/duplicate")
async def duplicate_atlas(req: DuplicateRequest):
    try:
        atlas = db.get_atlas_project(req.atlas_id)
        if not atlas:
            return {"success": False, "error": "Original Atlas project not found"}
            
        new_id = str(uuid.uuid4())
        new_title = f"{atlas.get('title') or 'Untitled'} - Copy"
        
        # Save a duplicate record
        db.save_atlas_project(
            atlas_id=new_id,
            user_id=atlas.get("user_id"),
            source_project_id=atlas.get("source_project_id"),
            title=new_title,
            duration=atlas.get("duration"),
            tools=atlas.get("tools"),
            roadmap=atlas.get("roadmap"),
            structure=atlas.get("structure"),
            flow_map=atlas.get("flow_map"),
            dependency_map=atlas.get("dependency_map"),
            tasks=atlas.get("tasks"),
            generated_files=atlas.get("generated_files"),
            zip_path=atlas.get("zip_path")  # Point to same ZIP initially
        )
        
        return {
            "success": True,
            "atlas_id": new_id
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/atlas")
@app.delete("/")
async def delete_atlas(atlas_id: str = Query(...)):
    try:
        atlas = db.get_atlas_project(atlas_id)
        if not atlas:
            return {"success": False, "error": "Atlas project not found"}
            
        # Optional: delete zip file from disk if present
        zip_path = atlas.get("zip_path")
        if zip_path and os.path.exists(zip_path):
            try:
                os.unlink(zip_path)
            except Exception:
                pass
                
        success = db.delete_atlas_project(atlas_id)
        return {"success": success}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/atlas")
@app.get("/")
async def get_atlas(
    atlas_id: Optional[str] = Query(None),
    source_project_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None)
):
    # If requesting details of specific Atlas
    if atlas_id:
        atlas = db.get_atlas_project(atlas_id)
        if not atlas:
            return {"success": False, "error": "Atlas project not found"}
        if isinstance(atlas, dict):
            atlas["project_structure"] = atlas.get("structure") or []
            atlas["production_flow_map"] = atlas.get("flow_map") or []
            atlas["task_breakdown"] = atlas.get("tasks") or {}
        return {
            "success": True,
            "atlas": atlas
        }
        
    # If requesting all Atlas plans linked to a source project
    if source_project_id:
        plans = db.get_atlas_projects_by_source(source_project_id)
        for p in plans:
            if isinstance(p, dict):
                p["project_structure"] = p.get("structure") or []
                p["production_flow_map"] = p.get("flow_map") or []
                p["task_breakdown"] = p.get("tasks") or {}
        return {
            "success": True,
            "plans": plans
        }
        
    # If requesting all Atlas plans for a user
    if user_id:
        plans = db.list_atlas_projects(user_id=user_id)
        for p in plans:
            if isinstance(p, dict):
                p["project_structure"] = p.get("structure") or []
                p["production_flow_map"] = p.get("flow_map") or []
                p["task_breakdown"] = p.get("tasks") or {}
        return {
            "success": True,
            "plans": plans
        }

    return {
        "status": "ready",
        "platform": "DreamXV AI Studio",
        "feature": "DreamXV Atlas",
        "description": "Generate AI-powered development roadmaps, project structures, and production workflows for your projects."
    }
