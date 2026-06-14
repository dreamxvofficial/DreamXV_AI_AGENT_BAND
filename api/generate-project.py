from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
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

@app.post("/api/generate-project")
@app.post("/")
async def generate_project(request: GenerateProjectRequest):
    logger.info(f"Vercel Serverless: Received project generation request for prompt='{request.prompt[:50]}'")
    
    # Initialize BandManager and execute the pipeline synchronously
    manager = BandManager()
    try:
        project = await manager.generate_project(request.prompt, request.user_id)
        
        base64_images = []
        # Convert any saved image files to inline base64 data URLs
        if project.art and project.art.image_paths:
            for path_str in project.art.image_paths:
                try:
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

        # Return the exact schema requested by the instructions
        return {
            "title": project.title or "Zombie Survival RPG",
            "story": project.story.summary if project.story else "",
            "world": project.world.description if project.world else "",
            "gameplay": project.gameplay.core_loop if project.gameplay else "",
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
            "images": base64_images,
            
            # Keep additional identifiers for frontend compatibility
            "project_id": project.project_id,
            "created_at": project.created_at.isoformat() if project.created_at else None
        }
    except Exception as exc:
        logger.error(f"Project generation failed: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Project generation failed: {str(exc)}"}
        )
