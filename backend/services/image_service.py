"""
DreamXV AI Studio — Image Generation Service
=============================================
Generates images using AIMLAPI's /v1/images/generations/ endpoint.
Featherless AI does not support image generation, so AIMLAPI is used directly.
Images are saved to outputs/images/ (or returned inline on Vercel).
"""

from __future__ import annotations

import base64
import json
import os
import struct
from pathlib import Path
from typing import Optional

import httpx

from backend.config import get_settings
from backend.services.provider_capabilities import validate_provider_capability
from backend.utils.helpers import sanitize_filename
from backend.utils.logger import get_logger

logger = get_logger("image_service")

# Maximum images per project (enforced)
MAX_IMAGES_PER_PROJECT = 10


def mask_api_key(value: str) -> str:
    """Return a deployment-safe key fingerprint for log comparison."""
    if not value:
        return "<missing>"
    if len(value) <= 12:
        return f"<set:length={len(value)}>"
    return f"{value[:6]}...{value[-6:]} (length={len(value)})"


class ImageService:
    """Generate and save images via AIMLAPI."""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.aiml_api_key
        self._base_url = settings.aiml_base_url
        self._model = settings.aiml_image_model
        self._images_dir = settings.images_dir
        self._endpoint = f"{self._base_url.rstrip('/')}/images/generations/"
        self._api_key_source = os.getenv("AIML_API_KEY_SOURCE", "<missing>")

        logger.info(
            "IMAGE_RUNTIME_CONFIG: "
            f"provider=AIMLAPI endpoint={self._endpoint} model={self._model} "
            f"api_key={mask_api_key(self._api_key)} key_source={self._api_key_source} "
            f"vercel_env={os.getenv('VERCEL_ENV', '<local>')} "
            f"deployment_sha={os.getenv('VERCEL_GIT_COMMIT_SHA', '<unknown>')}"
        )

        # Ensure output directory exists (skip on Vercel)
        if not os.getenv("VERCEL"):
            try:
                self._images_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning(f"Could not create images dir: {e}")

    async def generate_image(
        self,
        prompt: str,
        *,
        project_id: str,
        image_type: str = "concept",
        filename: Optional[str] = None,
        provider_type: str = "aimlapi",
    ) -> str:
        """
        Generate an image from a text prompt and save it to disk (or return base64 on Vercel).

        Args:
            prompt: Text description for image generation.
            project_id: Associated project ID (for organizing outputs).
            image_type: Category — 'character', 'environment', or 'cover'.
            filename: Override output filename (auto-generated if None).

        Returns:
            Absolute file path of the saved image, or base64 data URL.
        """
        provider = validate_provider_capability(provider_type, "image")
        if provider != "aimlapi":
            # Defensive guard: currently AIMLAPI is the sole image-capable provider.
            raise ValueError(f"Image provider '{provider}' is not routed by ImageService.")
        if not self._api_key or self._api_key == "your_key_here" or self._api_key.startswith("your_"):
            raise RuntimeError("AIMLAPI image generation is not configured: missing API key.")
        if not self._base_url or not self._model:
            raise RuntimeError("AIMLAPI image generation is not configured: missing base URL or image model.")

        existing = []
        output_path = None
        
        if not os.getenv("VERCEL"):
            # Build project-specific subdirectory
            project_dir = self._images_dir / sanitize_filename(project_id)
            try:
                project_dir.mkdir(parents=True, exist_ok=True)
                existing = list(project_dir.glob("*.png")) + list(project_dir.glob("*.jpg"))
            except Exception as e:
                logger.warning(f"Could not create project images dir: {e}")

            if len(existing) >= MAX_IMAGES_PER_PROJECT:
                logger.warning(
                    f"Image limit reached for project {project_id} "
                    f"({len(existing)}/{MAX_IMAGES_PER_PROJECT}). Skipping."
                )
                raise ValueError(
                    f"Maximum of {MAX_IMAGES_PER_PROJECT} images per project reached."
                )

            # Determine output filename
            if filename is None:
                index = len(existing) + 1
                safe_type = sanitize_filename(image_type)
                filename = f"{safe_type}_{index:02d}.png"

            output_path = project_dir / filename

        logger.info(f"Generating image: type={image_type}, model={self._model}")
        logger.debug(f"Image prompt: {prompt[:100]}...")

        # AIMLAPI is the only image provider. Featherless is text-only.
        image_generated = False
        img_bytes = None
        provider_errors: list[str] = []

        if not image_generated:
            try:
                request_body = {
                    "model": self._model,
                    "prompt": prompt,
                    "n": 1,
                    "response_format": "b64_json",
                }
                logger.info("IMAGE_PROVIDER: AIMLAPI")
                logger.info(f"IMAGE_ENDPOINT: {self._endpoint}")
                logger.info(f"MODEL_NAME: {self._model}")
                logger.info(f"API_KEY_FINGERPRINT: {mask_api_key(self._api_key)}")
                logger.info(f"IMAGE_REQUEST_BODY: {json.dumps(request_body, ensure_ascii=False)}")
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        self._endpoint,
                        headers={
                            "Authorization": f"Bearer {self._api_key}",
                            "Content-Type": "application/json",
                        },
                        json=request_body,
                    )
                    logger.info(f"HTTP_STATUS: {response.status_code}")
                    if response.status_code != 200:
                        logger.warning(f"IMAGE_RESPONSE_BODY: {response.text}")
                        message = f"AIMLAPI returned HTTP {response.status_code}: {response.text}"
                        logger.warning(f"ERROR_MESSAGE: {message}")
                        raise RuntimeError(message)

                data = response.json()
                response_fields = [
                    sorted(item.keys()) for item in data.get("data", [])
                    if isinstance(item, dict)
                ]
                logger.info(
                    "IMAGE_RESPONSE_BODY: "
                    f"<success payload omitted; data_fields={response_fields}>"
                )

                # Extract and save image
                if "data" in data and len(data["data"]) > 0:
                    image_data = data["data"][0]

                    if "b64_json" in image_data:
                        # Base64-encoded image
                        img_bytes = base64.b64decode(image_data["b64_json"])
                        logger.info(f"Image generated via AIMLAPI")
                        image_generated = True
                    elif "url" in image_data:
                        # URL-based response — download the image
                        async with httpx.AsyncClient(timeout=60.0) as dl_client:
                            img_response = await dl_client.get(image_data["url"])
                            img_response.raise_for_status()
                            img_bytes = img_response.content
                            logger.info(f"Image downloaded via AIMLAPI")
                            image_generated = True
                    else:
                        raise ValueError("Unexpected image response format from AIMLAPI")
                else:
                    raise ValueError("No image data returned from AIMLAPI")
            except Exception as exc:
                provider_errors.append(f"AIMLAPI: {exc}")
                logger.warning(f"ERROR_MESSAGE: AIMLAPI image generation failed: {exc}")

        if not image_generated or not self._is_valid_image(img_bytes):
            detail = "; ".join(provider_errors) or "provider returned no valid image data"
            raise RuntimeError(f"Image generation failed: {detail}")

        if img_bytes:
            if os.getenv("VERCEL"):
                img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                return f"data:image/png;base64,{img_b64}"
            elif output_path:
                try:
                    output_path.write_bytes(img_bytes)
                    logger.info(f"Image saved: {output_path}")
                    return str(output_path)
                except Exception as w_exc:
                    logger.error(f"Failed to write image to disk: {w_exc}")
                    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                    return f"data:image/png;base64,{img_b64}"
        
        return ""

    @staticmethod
    def _is_valid_image(data: Optional[bytes]) -> bool:
        """Reject empty/tiny fallback payloads before they can be saved as successful art."""
        if not data or len(data) < 1024:
            return False
        if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
            width, height = struct.unpack(">II", data[16:24])
            return width >= 128 and height >= 128
        if data.startswith(b"\xff\xd8\xff"):
            return True
        if data.startswith((b"RIFF", b"GIF8")):
            return True
        return False

    async def generate_project_images(
        self,
        prompts: list[str],
        *,
        project_id: str,
        image_types: Optional[list[str]] = None,
    ) -> list[str]:
        """
        Generate multiple images for a project (up to MAX_IMAGES_PER_PROJECT) in parallel.

        Args:
            prompts: List of image generation prompts.
            project_id: Associated project ID.
            image_types: Optional list of types matching prompts.

        Returns:
            List of saved file paths (or base64 strings).
        """
        import asyncio
        if image_types is None:
            image_types = ["concept"] * len(prompts)

        # Enforce limit
        prompts = prompts[:MAX_IMAGES_PER_PROJECT]
        image_types = image_types[:MAX_IMAGES_PER_PROJECT]

        tasks = []
        for prompt, img_type in zip(prompts, image_types):
            tasks.append(self.generate_image(
                prompt,
                project_id=project_id,
                image_type=img_type,
            ))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        paths: list[str] = []
        for res, img_type in zip(results, image_types):
            if isinstance(res, Exception):
                logger.error(f"Image generation failed for type={img_type}: {res}")
            elif res:
                paths.append(res)

        return paths
