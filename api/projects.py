from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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


class RegenerateImageRequest(BaseModel):
    project_id: str
    image_id: str


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
            
            # Fetch generated images from project_images table
            images_list = db.get_project_images(project_id)
            project_data["images_list"] = images_list
            
            # Also attach generation stats from the projects record
            project_data["art_generation_status"] = project_record.get("art_generation_status") or "pending"
            project_data["total_images"] = project_record.get("total_images") or 6
            project_data["generated_images"] = project_record.get("generated_images") or 0
            project_data["art_gallery"] = project_data.get("art_gallery") or [img.get("image_url") for img in images_list]

        return {
            "success": True,
            "project": project_data,
            "data": project_data
        }

    # 2. Otherwise, list all projects, optionally filtering by user_id
    projects = db.list_projects(user_id=user_id)
    atlas_projects = db.list_atlas_projects(user_id=user_id)

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
            "is_atlas": False
        })

    for a in atlas_projects:
        created = a.get("created_at")
        created_str = created.isoformat() if hasattr(created, "isoformat") else (str(created) if created else "")
        
        summaries.append({
            "project_id": a.get("id"),
            "title": f"{a.get('title') or 'Untitled'} (Atlas)",
            "created_at": created_str,
            "status": "completed",
            "is_atlas": True,
            "source_project_id": a.get("source_project_id"),
            "tools": a.get("tools"),
            "duration": a.get("duration")
        })

    # Sort summaries chronologically by created_at descending
    summaries.sort(key=lambda x: x.get("created_at") or "", reverse=True)

    return {
        "projects": summaries,
        "total": len(summaries)
    }


@app.post("/api/projects/regenerate-image")
@app.post("/regenerate-image")
async def regenerate_image(req: RegenerateImageRequest):
    try:
        # Fetch the image record
        img_record = db.get_project_image(req.image_id)
        if not img_record:
            return {"success": False, "error": f"Image record '{req.image_id}' not found."}

        prompt = img_record.get("prompt")
        category = img_record.get("category")

        # Trigger image generation
        from backend.services.image_service import ImageService
        image_service = ImageService()

        res_path = await image_service.generate_image(
            prompt,
            project_id=req.project_id,
            image_type=category
        )

        if not res_path:
            return {"success": False, "error": "Image generation service did not return a path."}

        # Convert local path to base64 if needed
        image_url = ""
        if not res_path.startswith("data:image/"):
            from pathlib import Path
            import base64
            img_path = Path(res_path)
            if img_path.exists():
                img_bytes = img_path.read_bytes()
                img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                image_url = f"data:image/png;base64,{img_b64}"
                try:
                    img_path.unlink()
                except Exception:
                    pass
            else:
                image_url = res_path
        else:
            image_url = res_path

        # Update URL in database
        db.update_project_image_url(req.image_id, image_url)

        # Update the project_json manifest image lists too
        all_imgs = db.get_project_images(req.project_id)
        image_urls = [img.get("image_url") for img in all_imgs]

        project_record = db.get_project(req.project_id)
        if project_record:
            project_json = project_record.get("project_json", {})
            if isinstance(project_json, dict):
                if "art" not in project_json or not project_json["art"]:
                    project_json["art"] = {}
                project_json["art"]["image_paths"] = image_urls
                project_json["images"] = image_urls

                db.save_project(
                    project_id=req.project_id,
                    user_id=project_record.get("user_id"),
                    title=project_record.get("title"),
                    prompt=project_record.get("prompt"),
                    project_json=project_json
                )

        return {
            "success": True,
            "image_url": image_url
        }
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        return {"success": False, "error": f"Regeneration failed: {str(e)}", "traceback": tb}


@app.delete("/api/projects")
@app.delete("/")
async def delete_project(project_id: str = Query(...)):
    try:
        # 1. Delete associated images from project_images
        try:
            db.client.table("project_images").delete().eq("project_id", db._get_project_uuid(project_id)).execute()
        except Exception as img_err:
            print(f"Error deleting project images: {img_err}")

        # 2. Delete associated Atlas projects
        try:
            atlas_plans = db.get_atlas_projects_by_source(project_id)
            for plan in atlas_plans:
                db.delete_atlas_project(plan.get("id"))
        except Exception as atlas_err:
            print(f"Error deleting linked atlas projects: {atlas_err}")

        # 3. Delete the project itself
        success = db.delete_project(project_id)
        return {"success": success}
    except Exception as e:
        return {"success": False, "error": str(e)}
