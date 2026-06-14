from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel
import base64
from pathlib import Path
import os
import sys

# Ensure backend package can be imported by adding the root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.band_manager import BandManager
from backend.models.schemas import GenerateProjectRequest
from backend.utils.logger import get_logger

logger = get_logger("api_generate_project")

app = FastAPI()

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error occurred: {exc}")
    # Return 200 with success: False or 400 with success: False. Let's return 400 with success: False.
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": f"Invalid request input: {str(exc)}"
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.error(f"HTTP exception occurred: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception occurred: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc)
        }
    )

@app.post("/api/generate-project")
@app.post("/")
async def generate_project(request: GenerateProjectRequest):
    logger.info(f"Vercel Serverless: Received project generation request for prompt='{request.prompt[:50]}'")
    
    # Initialize BandManager and execute the pipeline synchronously
    manager = BandManager()
    
    # We let exceptions bubble to exception_handler
    project = await manager.generate_project(request.prompt, request.user_id)
    
    base64_images = []
    # Convert any saved image files to inline base64 data URLs
    if project.art and project.art.image_paths:
        for path_str in project.art.image_paths:
            try:
                # If it's already a base64 inline string, use it directly
                if path_str.startswith("data:image/"):
                    base64_images.append(path_str)
                    continue
                
                img_path = Path(path_str)
                if img_path.exists():
                    img_bytes = img_path.read_bytes()
                    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                    base64_images.append(f"data:image/png;base64,{img_b64}")
                    # Clean up /tmp image to conserve serverless memory
                    try:
                        img_path.unlink()
                    except Exception:
                        pass
                else:
                    base64_images.append(path_str)
            except Exception as img_err:
                logger.error(f"Failed to convert image {path_str} to base64: {img_err}")
                base64_images.append(path_str)
        
    # Clean up the project JSON export in /tmp if saved
    try:
        from backend.config import get_settings
        settings = get_settings()
        json_path = settings.outputs_dir / f"dxv_{project.project_id}.json"
        if json_path.exists():
            json_path.unlink()
    except Exception:
        pass

    # Return structured success/data envelope
    return {
        "success": True,
        "data": {
            "project_id": project.project_id,
            "title": project.title or "Zombie Survival RPG",
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "story": {
                "title": project.story.title if project.story else "",
                "lore": project.story.lore if project.story else "",
                "summary": project.story.summary if project.story else "",
                "acts": project.story.acts if project.story else [],
                "themes": project.story.themes if project.story else []
            } if project.story else None,
            "characters": [
                {
                    "name": c.name,
                    "role": c.role,
                    "backstory": c.backstory,
                    "abilities": c.abilities,
                    "personality_traits": c.personality_traits
                }
                for c in project.characters
            ] if project.characters else [],
            "world": {
                "name": project.world.name if project.world else "",
                "description": project.world.description if project.world else "",
                "regions": project.world.regions if project.world else [],
                "lore_elements": project.world.lore_elements if project.world else [],
                "atmosphere": project.world.atmosphere if project.world else ""
            } if project.world else None,
            "gameplay": {
                "core_loop": project.gameplay.core_loop if project.gameplay else "",
                "mechanics": project.gameplay.mechanics if project.gameplay else [],
                "progression_system": project.gameplay.progression_system if project.gameplay else "",
                "difficulty_curve": project.gameplay.difficulty_curve if project.gameplay else ""
            } if project.gameplay else None,
            "art": {
                "prompts": project.art.prompts if project.art else [],
                "image_paths": base64_images,
                "style_guide": project.art.style_guide if project.art else ""
            } if project.art else None,
            "qa": {
                "consistency_score": project.qa.consistency_score if project.qa else 0.0,
                "issues": project.qa.issues if project.qa else [],
                "suggestions": project.qa.suggestions if project.qa else [],
                "overall_assessment": project.qa.overall_assessment if project.qa else ""
            } if project.qa else None,
            "images": base64_images
        }
    }
