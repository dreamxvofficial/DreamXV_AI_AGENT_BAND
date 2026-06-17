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
import traceback
import asyncio

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

# Required Environment Variables Checklist
REQUIRED_ENV_VARS = [
    "FEATHERLESS_API_KEY",
    "FEATHERLESS_BASE_URL",
    "FEATHERLESS_MODEL",
    "AIML_API_KEY",
    "AIML_BASE_URL",
    "AIML_MODEL"
]


def run_startup_diagnostics():
    print("--- STARTUP DIAGNOSTICS ---")
    for var in REQUIRED_ENV_VARS:
        if os.getenv(var):
            print(f"  ✓ {var} exists")
        else:
            print(f"  ✗ {var} is MISSING!")
    print("---------------------------")


async def test_featherless() -> bool:
    print("Testing Featherless AI connection...")
    try:
        from backend.services.featherless_service import FeatherlessService
        service = FeatherlessService()
        messages = [{"role": "user", "content": "Say hello from Dream XV."}]
        response = await service.generate(messages, max_tokens=50)
        print(f"Featherless AI connection successful: {response[:80]}")
        return True
    except Exception as e:
        print(f"Featherless AI connection test failed (will use AIMLAPI fallback): {e}")
        return False


@app.on_event("startup")
async def startup_event():
    run_startup_diagnostics()
    # Don't await test — just fire and forget so startup isn't blocked
    asyncio.create_task(test_featherless())


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": f"Invalid request input: {str(exc)}",
            "traceback": ""
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.error(f"HTTP exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": str(exc.detail) or f"HTTP {exc.status_code}",
            "traceback": ""
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    logger.error(f"Unhandled exception: {exc}\n{tb}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc) or "An unexpected server error occurred.",
            "traceback": tb
        }
    )


# Reuse global BandManager instance
_global_manager = None


def get_manager() -> BandManager:
    global _global_manager
    if _global_manager is None:
        _global_manager = BandManager()
    return _global_manager


def _build_project_data(project, base64_images: list) -> dict:
    """Safely serialize a ProjectOutput into a JSON-serializable dict."""
    from backend.models.output_models import ArtOutput

    return {
        "project_id": project.project_id,
        "title": project.title or "Untitled Project",
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
            for c in (project.characters or [])
        ],
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
            "prompts": project.art.prompts if isinstance(project.art, ArtOutput) else [],
            "image_paths": base64_images,
            "style_guide": (
                project.art.style_guide if isinstance(project.art, ArtOutput)
                else (project.art.get("warning", "") if isinstance(project.art, dict) else "")
            )
        } if project.art else None,
        "qa": {
            "consistency_score": project.qa.consistency_score if project.qa else 0.0,
            "issues": project.qa.issues if project.qa else [],
            "suggestions": project.qa.suggestions if project.qa else [],
            "overall_assessment": project.qa.overall_assessment if project.qa else ""
        } if project.qa else None,
        "review": {
            "consistency_score": project.review.consistency_score if project.review else 0.0,
            "issues": [
                {
                    "category": issue.category,
                    "description": issue.description,
                    "severity": issue.severity,
                    "suggested_fix": issue.suggested_fix,
                    "references": issue.references,
                }
                for issue in (project.review.issues if project.review else [])
            ],
            "summary": project.review.summary if project.review else ""
        } if project.review else None,
        "documentation": {
            "readme": project.documentation.readme if project.documentation else "",
            "gdd": project.documentation.gdd if project.documentation else "",
            "feature_list": project.documentation.feature_list if project.documentation else [],
            "core_mechanics": project.documentation.core_mechanics if project.documentation else [],
            "monetization": project.documentation.monetization if project.documentation else [],
            "future_expansion": project.documentation.future_expansion if project.documentation else [],
            "technical_summary": project.documentation.technical_summary if project.documentation else "",
            "elevator_pitch": project.documentation.elevator_pitch if project.documentation else ""
        } if project.documentation else None,
        "images": base64_images,
        "art_gallery": getattr(project, "art_gallery", [])
    }


@app.post("/api/generate-project")
@app.post("/")
async def generate_project(request: GenerateProjectRequest):
    logger.info(f"Received project generation request — prompt='{request.prompt[:80]}'")

    try:
        # Verify environment variables
        missing_vars = [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]
        if missing_vars:
            err_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(err_msg)
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": err_msg, "traceback": ""}
            )

        manager = get_manager()

        # Run project generation with overall timeout safety net
        try:
            project = await asyncio.wait_for(
                manager.generate_project(request.prompt, request.user_id),
                timeout=600.0  # 10 min outer safety net — inner agents have their own timeouts
            )
        except asyncio.TimeoutError:
            err_msg = "Project generation timed out after 600 seconds."
            logger.error(err_msg)
            return JSONResponse(
                status_code=504,
                content={"success": False, "error": err_msg, "traceback": "asyncio.TimeoutError"}
            )

        # Convert image file paths to base64 inline data URLs
        base64_images = []
        from backend.models.output_models import ArtOutput
        if project.art and isinstance(project.art, ArtOutput) and project.art.image_paths:
            for path_str in project.art.image_paths:
                try:
                    if str(path_str).startswith("data:image/"):
                        base64_images.append(path_str)
                        continue
                    img_path = Path(path_str)
                    if img_path.exists():
                        img_bytes = img_path.read_bytes()
                        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                        base64_images.append(f"data:image/png;base64,{img_b64}")
                        try:
                            img_path.unlink()
                        except Exception:
                            pass
                    else:
                        base64_images.append(path_str)
                except Exception as img_err:
                    logger.error(f"Failed to convert image {path_str} to base64: {img_err}")
                    base64_images.append(path_str)

        # Clean up JSON export file if present
        try:
            from backend.config import get_settings
            settings = get_settings()
            json_path = settings.outputs_dir / f"dxv_{project.project_id}.json"
            if json_path.exists():
                json_path.unlink()
        except Exception:
            pass

        project_data = _build_project_data(project, base64_images)

        logger.info(f"Project generation successful — id={project.project_id}, title='{project.title}'")
        return {
            "success": True,
            "project": project_data,
            "data": project_data
        }

    except Exception as e:
        tb = traceback.format_exc()
        err_msg = str(e) or "An unexpected error occurred during project generation."
        logger.error(f"Project generation exception: {err_msg}\n{tb}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": err_msg,
                "traceback": tb
            }
        )
