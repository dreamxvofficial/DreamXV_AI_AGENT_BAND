"""
DreamXV AI Studio — Export Service
==================================
Handles exporting completed projects to JSON files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from backend.config import get_settings
from backend.models.output_models import ProjectOutput
from backend.utils.helpers import sanitize_filename
from backend.utils.logger import get_logger

logger = get_logger("export")


import os

class ExportService:
    """Export completed project data to persistent storage."""

    def __init__(self) -> None:
        settings = get_settings()
        self._outputs_dir = settings.outputs_dir
        if not os.getenv("VERCEL"):
            try:
                self._outputs_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning(f"Could not create outputs dir: {e}")

    def save_project(self, project: ProjectOutput) -> str:
        """
        Save a completed ProjectOutput to a JSON file.

        Args:
            project: The completed project data.

        Returns:
            File path of the saved project.
        """
        if os.getenv("VERCEL"):
            logger.info("Running on Vercel: skipped saving project to file system.")
            return ""

        filename = f"{sanitize_filename(project.project_id)}.json"
        output_path = self._outputs_dir / filename

        try:
            output_path.write_text(
                project.model_dump_json(indent=2),
                encoding="utf-8",
            )
            logger.info(f"Project exported: {output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"Failed to write project JSON to disk: {e}")
            return ""

    def load_project(self, project_id: str) -> Optional[ProjectOutput]:
        """
        Load a project from disk by ID.

        Returns:
            ProjectOutput if found, None otherwise.
        """
        filename = f"{sanitize_filename(project_id)}.json"
        file_path = self._outputs_dir / filename

        if not file_path.exists():
            return None

        raw = file_path.read_text(encoding="utf-8")
        return ProjectOutput.model_validate_json(raw)

    def list_projects(self) -> list[dict]:
        """
        List all saved projects.

        Returns:
            List of project summary dicts with id, title, created_at.
        """
        projects = []
        if not self._outputs_dir.exists():
            return projects
        for f in sorted(self._outputs_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                projects.append({
                    "project_id": data.get("project_id", f.stem),
                    "title": data.get("title", "Untitled"),
                    "created_at": data.get("created_at", ""),
                    "status": "completed",
                })
            except Exception as exc:
                logger.warning(f"Failed to read project file {f}: {exc}")
                continue
        return projects
