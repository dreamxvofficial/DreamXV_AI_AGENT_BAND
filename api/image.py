from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import base64
import os
import sys

# Ensure backend package can be imported by adding the root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.image_service import ImageService
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
async def serve_image(prompt: str = "Game Art Concept", project_id: str = "temp"):
    image_service = ImageService()
    try:
        # Generate image (will call AIMLAPI or output the mock placeholder PNG to /tmp)
        img_path_str = await image_service.generate_image(
            prompt,
            project_id=project_id,
            image_type="concept"
        )
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
    except Exception as exc:
        logger.error(f"Image API generation error: {exc}")
        
    # Final base64 solid color fallback PNG
    tiny_png = (
        "iVBORw0KGgoAAAANSUhEUgAAAQAAAAEAAQMAAAB5o5OKAAAAA1BMVEUKGjoGf18hAAAA"
        "H0lEQVRo3u3BAQ0AAADCoPdPbQ43oAAAAAAAAAAAAIB3A1wAAQEp59ADAAAAAElFTkSu"
        "QmCC"
    )
    img_bytes = base64.b64decode(tiny_png)
    return Response(content=img_bytes, media_type="image/png")
