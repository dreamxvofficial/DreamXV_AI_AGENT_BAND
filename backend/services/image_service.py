"""
DreamXV AI Studio — Image Generation Service
=============================================
Generates images using AIMLAPI's /v1/images/generations/ endpoint.
Featherless AI does not support image generation, so AIMLAPI is used directly.
Images are saved to outputs/images/.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

import httpx

from backend.config import get_settings
from backend.utils.helpers import sanitize_filename
from backend.utils.logger import get_logger

logger = get_logger("image_service")

# Maximum images per project (enforced)
MAX_IMAGES_PER_PROJECT = 3


class ImageService:
    """Generate and save images via AIMLAPI."""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.aiml_api_key
        self._base_url = settings.aiml_base_url
        self._model = settings.aiml_image_model
        self._images_dir = settings.images_dir

        # Ensure output directory exists
        self._images_dir.mkdir(parents=True, exist_ok=True)

    async def generate_image(
        self,
        prompt: str,
        *,
        project_id: str,
        image_type: str = "concept",
        filename: Optional[str] = None,
    ) -> str:
        """
        Generate an image from a text prompt and save it to disk.

        Args:
            prompt: Text description for image generation.
            project_id: Associated project ID (for organizing outputs).
            image_type: Category — 'character', 'environment', or 'cover'.
            filename: Override output filename (auto-generated if None).

        Returns:
            Absolute file path of the saved image.
        """
        # Build project-specific subdirectory
        project_dir = self._images_dir / sanitize_filename(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)

        # Check image limit
        existing = list(project_dir.glob("*.png")) + list(project_dir.glob("*.jpg"))
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

        # Call AIMLAPI image generation endpoint
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
            response.raise_for_status()

        data = response.json()

        # Extract and save image
        if "data" in data and len(data["data"]) > 0:
            image_data = data["data"][0]

            if "b64_json" in image_data:
                # Base64-encoded image
                img_bytes = base64.b64decode(image_data["b64_json"])
                output_path.write_bytes(img_bytes)
                logger.info(f"Image saved: {output_path}")
            elif "url" in image_data:
                # URL-based response — download the image
                async with httpx.AsyncClient(timeout=60.0) as dl_client:
                    img_response = await dl_client.get(image_data["url"])
                    img_response.raise_for_status()
                    output_path.write_bytes(img_response.content)
                    logger.info(f"Image downloaded and saved: {output_path}")
            else:
                raise ValueError("Unexpected image response format from AIMLAPI")
        else:
            raise ValueError("No image data returned from AIMLAPI")

        return str(output_path)

    async def generate_project_images(
        self,
        prompts: list[str],
        *,
        project_id: str,
        image_types: Optional[list[str]] = None,
    ) -> list[str]:
        """
        Generate multiple images for a project (up to MAX_IMAGES_PER_PROJECT).

        Args:
            prompts: List of image generation prompts.
            project_id: Associated project ID.
            image_types: Optional list of types matching prompts.

        Returns:
            List of saved file paths.
        """
        if image_types is None:
            image_types = ["concept"] * len(prompts)

        # Enforce limit
        prompts = prompts[:MAX_IMAGES_PER_PROJECT]
        image_types = image_types[:MAX_IMAGES_PER_PROJECT]

        paths: list[str] = []
        for prompt, img_type in zip(prompts, image_types):
            try:
                path = await self.generate_image(
                    prompt,
                    project_id=project_id,
                    image_type=img_type,
                )
                paths.append(path)
            except Exception as exc:
                logger.error(f"Image generation failed for type={img_type}: {exc}")
                # Continue with remaining images
                continue

        return paths
