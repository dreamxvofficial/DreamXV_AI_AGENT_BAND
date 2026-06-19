from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Ensure backend package can be imported by adding the root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.image_service import ImageService
from backend.services.provider_capabilities import ProviderCapabilityError
from backend.utils.logger import get_logger

logger = get_logger("api_image")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/image")
@app.get("/")
async def serve_image(
    prompt: str = "Game Art Concept",
    project_id: str = "temp",
    provider_type: str = "aimlapi",
):
    image_service = ImageService()
    try:
        # Capability validation happens inside ImageService before any network request.
        img_path_str = await image_service.generate_image(
            prompt,
            project_id=project_id,
            image_type="concept",
            provider_type=provider_type,
        )
        if img_path_str.startswith("data:image/"):
            import base64
            _, encoded = img_path_str.split(",", 1)
            return Response(content=base64.b64decode(encoded), media_type="image/png")
        from pathlib import Path
        img_path = Path(img_path_str)
        if img_path.exists():
            img_bytes = img_path.read_bytes()
            # Clean up /tmp file to conserve ephemeral serverless container disk space
            try:
                img_path.unlink()
            except Exception:
                pass
            return Response(content=img_bytes, media_type="image/png")
    except ProviderCapabilityError as exc:
        logger.warning(f"Rejected image provider: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Image API generation error: {exc}")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    raise HTTPException(status_code=502, detail="AIMLAPI returned no image data.")
