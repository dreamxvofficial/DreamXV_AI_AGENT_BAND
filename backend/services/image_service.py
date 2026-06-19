"""
DreamXV AI Studio — Image Generation Service
=============================================
Generates images using AIMLAPI's /v1/images/generations/ endpoint.
Featherless AI does not support image generation, so AIMLAPI is used directly.
Images are saved to outputs/images/ (or returned inline on Vercel).
"""

from __future__ import annotations

import base64
import os
import struct
from pathlib import Path
from typing import Optional

import httpx

from backend.config import get_settings
from backend.utils.helpers import sanitize_filename
from backend.utils.logger import get_logger

logger = get_logger("image_service")

# Maximum images per project (enforced)
MAX_IMAGES_PER_PROJECT = 10


class ImageService:
    """Generate and save images via AIMLAPI."""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.aiml_api_key
        self._base_url = settings.aiml_base_url
        self._model = settings.aiml_image_model
        self._featherless_api_key = settings.featherless_api_key
        self._featherless_base_url = settings.featherless_base_url
        self._images_dir = settings.images_dir

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

        # Call image generation endpoint (Featherless AI first, then fallback to AIMLAPI)
        image_generated = False
        img_bytes = None
        provider_errors: list[str] = []
        
        # 1. Try Featherless AI if supported/available
        if self._featherless_api_key and self._featherless_api_key != "your_key_here" and not self._featherless_api_key.startswith("your_"):
            try:
                logger.info("IMAGE_PROVIDER: Featherless AI")
                logger.info("MODEL_NAME: flux/schnell")
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self._featherless_base_url}/images/generations",
                        headers={
                            "Authorization": f"Bearer {self._featherless_api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "flux/schnell",
                            "prompt": prompt,
                            "n": 1,
                            "response_format": "b64_json",
                        },
                    )
                    logger.info(f"HTTP_STATUS: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        if "data" in data and len(data["data"]) > 0:
                            image_data = data["data"][0]
                            if "b64_json" in image_data:
                                img_bytes = base64.b64decode(image_data["b64_json"])
                                logger.info(f"Image generated via Featherless AI")
                                image_generated = True
                            elif "url" in image_data:
                                async with httpx.AsyncClient(timeout=30.0) as dl_client:
                                    img_response = await dl_client.get(image_data["url"])
                                    img_response.raise_for_status()
                                    img_bytes = img_response.content
                                    logger.info(f"Image generated via Featherless AI (URL)")
                                    image_generated = True
                    else:
                        message = f"Featherless returned HTTP {response.status_code}: {response.text[:300]}"
                        provider_errors.append(message)
                        logger.warning(f"ERROR_MESSAGE: {message}")
            except Exception as f_exc:
                provider_errors.append(f"Featherless: {f_exc}")
                logger.info(f"ERROR_MESSAGE: Featherless image generation failed: {f_exc}")

        # 2. Fallback to AIMLAPI
        if not image_generated:
            try:
                logger.info("IMAGE_PROVIDER: AIMLAPI")
                logger.info(f"MODEL_NAME: {self._model}")
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        f"{self._base_url}/images/generations",
                        headers={
                            "Authorization": f"Bearer {self._api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self._model,
                            "prompt": prompt,
                            "n": 1,
                            "response_format": "b64_json",
                        },
                    )
                    logger.info(f"HTTP_STATUS: {response.status_code}")
                    if response.status_code != 200:
                        message = f"AIMLAPI returned HTTP {response.status_code}: {response.text[:500]}"
                        logger.warning(f"ERROR_MESSAGE: {message}")
                        raise RuntimeError(message)

                data = response.json()

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
