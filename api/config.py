from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import sys
from pathlib import Path

# Ensure backend package can be imported by adding the root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import get_settings
from backend.services.image_service import mask_api_key

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SetupRequest(BaseModel):
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    featherless_api_key: str
    aiml_api_key: str
    band_api_key: str

@app.get("/api/config/status")
@app.get("/status")
@app.get("/")
async def get_config_status():
    settings = get_settings()
    
    # Check if they are configured and not using default placeholder values
    keys_to_check = {
        "supabase_url": ("your_supabase_url_here", settings.supabase_url),
        "supabase_anon_key": ("your_supabase_anon_key_here", settings.supabase_anon_key),
        "supabase_service_role_key": ("your_supabase_service_role_key_here", settings.supabase_service_role_key),
        "featherless_api_key": ("your_key_here", settings.featherless_api_key),
        "aiml_api_key": ("your_key_here", settings.aiml_api_key),
        "band_api_key": ("your_key_here", settings.band_api_key)
    }
    
    missing_keys = []
    for key, (placeholder, val) in keys_to_check.items():
        if not val or val == placeholder or val.strip() == "":
            missing_keys.append(key)
            
    is_configured = len(missing_keys) == 0
    
    return {
        "success": True,
        "status": "configured" if is_configured else "pending",
        "missing_keys": missing_keys,
        "config": {
            "supabase_url": settings.supabase_url if settings.supabase_url != "your_supabase_url_here" else "",
            "supabase_anon_key": settings.supabase_anon_key if settings.supabase_anon_key != "your_supabase_anon_key_here" else "",
            "supabase_service_role_key": settings.supabase_service_role_key if settings.supabase_service_role_key != "your_supabase_service_role_key_here" else "",
            "featherless_api_key": settings.featherless_api_key if settings.featherless_api_key != "your_key_here" else "",
            "aiml_api_key": mask_api_key(settings.aiml_api_key) if settings.aiml_api_key != "your_key_here" else "",
            "band_api_key": settings.band_api_key if settings.band_api_key != "your_key_here" else ""
        }
    }

@app.post("/api/config/setup")
@app.post("/setup")
async def save_config_setup(req: SetupRequest):
    try:
        if os.getenv("VERCEL"):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Vercel environment variables cannot be persisted by this endpoint. "
                    "Set AIML_API_KEY in Vercel Project Settings for the correct environment, "
                    "then redeploy."
                ),
            )
        project_root = Path(__file__).resolve().parent.parent
        env_path = project_root / ".env"
        
        # Read current .env content or initialize empty
        lines = []
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
        # Parse current env dict
        env_dict = {}
        for line in lines:
            if "=" in line and not line.strip().startswith("#"):
                key, val = line.split("=", 1)
                env_dict[key.strip()] = val.strip().strip('"').strip("'")
                
        # Update with new values
        env_dict["SUPABASE_URL"] = req.supabase_url
        env_dict["SUPABASE_ANON_KEY"] = req.supabase_anon_key
        env_dict["SUPABASE_SERVICE_ROLE_KEY"] = req.supabase_service_role_key
        env_dict["FEATHERLESS_API_KEY"] = req.featherless_api_key
        # Settings.aiml_api_key maps to AIML_API_KEY. The legacy spelling can
        # otherwise leave an older deployment key active.
        env_dict["AIML_API_KEY"] = req.aiml_api_key
        env_dict.pop("AIMLAPI_API_KEY", None)
        env_dict["BAND_API_KEY"] = req.band_api_key
        
        # Write back to .env
        new_content = ""
        for key, val in env_dict.items():
            new_content += f'{key}="{val}"\n'
            
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        # Force reload settings from config
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path, override=True)
        get_settings.cache_clear()
        
        return {
            "success": True,
            "message": "Configuration updated successfully and .env written."
        }
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
