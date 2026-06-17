"""
DreamXV AI Studio — Supabase Service
====================================
Persistent database layer for user authentication and project storage.
"""

from __future__ import annotations

import os
import uuid
from typing import Any, Optional
from supabase import create_client, Client
from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger("supabase_service")


class SupabaseService:
    """Service to interact with Supabase for persistent auth and project data."""

    def __init__(self) -> None:
        settings = get_settings()
        self.url = settings.supabase_url
        self.key = settings.supabase_service_role_key

        if not self.url or self.url == "your_supabase_url_here":
            logger.warning("SUPABASE_URL is not configured in .env!")
        if not self.key or self.key == "your_supabase_service_role_key_here":
            logger.warning("SUPABASE_SERVICE_ROLE_KEY is not configured in .env!")

        # Initialize the supabase client using service role for admin bypass of RLS in backend
        try:
            self.client: Client = create_client(self.url, self.key)
            logger.info("Supabase client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None

    def _resolve_user_uuid(self, identifier: str) -> Optional[str]:
        """Resolve a username, email, or UUID to a valid user UUID."""
        if not identifier:
            return None
        try:
            uuid.UUID(identifier)
            return identifier
        except ValueError:
            user = self.get_user_by_username_or_email(identifier)
            return user.get("id") if user else None

    def _get_project_uuid(self, project_id: str) -> str:
        """Deterministically map any string project_id to a valid UUID format."""
        try:
            uuid.UUID(project_id)
            return project_id
        except ValueError:
            # Generate a namespace-based deterministic UUID
            return str(uuid.uuid5(uuid.NAMESPACE_DNS, project_id))

    def get_user_by_username_or_email(self, identifier: str) -> Optional[dict[str, Any]]:
        """Retrieve user profile by username or email (case-insensitive)."""
        if not self.client:
            logger.error("Supabase client not initialized")
            return None

        identifier_clean = identifier.strip().lower()
        try:
            # Query users where username or email matches identifier
            res = self.client.table("users").select("*").or_(
                f"username.ilike.{identifier_clean},email.ilike.{identifier_clean}"
            ).execute()
            if res.data and len(res.data) > 0:
                logger.info(f"User found in Supabase: {res.data[0].get('username')}")
                return res.data[0]
        except Exception as e:
            logger.error(f"Error fetching user '{identifier_clean}' from Supabase: {e}")
        return None

    def create_user(
        self,
        username: str,
        name: str,
        email: str,
        password_hash: str,
        user_uuid: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        """Insert a new user record in Supabase."""
        if not self.client:
            return None

        user_id = user_uuid if user_uuid else str(uuid.uuid4())
        user_data = {
            "id": user_id,
            "username": username,
            "full_name": name,
            "email": email.strip().lower(),
            "password_hash": password_hash,
            "onboarded": False,
            "onboarding_answers": {}
        }
        try:
            res = self.client.table("users").insert(user_data).execute()
            if res.data:
                logger.info(f"User created in Supabase: {username}")
                return res.data[0]
        except Exception as e:
            logger.error(f"Error creating user in Supabase: {e}")
        return None

    def update_user_onboarding(
        self,
        username: str,
        onboarded: bool,
        onboarding_answers: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Update onboarding answers for a user."""
        if not self.client:
            return None

        try:
            # Find the user record first
            user = self.get_user_by_username_or_email(username)
            if not user:
                logger.warning(f"Onboarding update failed: User '{username}' not found")
                return None

            res = self.client.table("users").update({
                "onboarded": onboarded,
                "onboarding_answers": onboarding_answers
            }).eq("id", user["id"]).execute()
            if res.data:
                logger.info(f"Onboarding updated in Supabase for user: {username}")
                return res.data[0]
        except Exception as e:
            logger.error(f"Error updating user onboarding in Supabase: {e}")
        return None

    def save_project(
        self,
        project_id: str,
        user_id: Optional[str],
        title: str,
        prompt: str,
        project_json: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Save/upsert a project in Supabase."""
        if not self.client:
            return None

        project_uuid = self._get_project_uuid(project_id)
        db_user_id = self._resolve_user_uuid(user_id) if user_id else None

        project_data = {
            "id": project_uuid,
            "user_id": db_user_id,
            "title": title,
            "prompt": prompt,
            "project_json": project_json
        }
        try:
            # Use upsert to support updates
            res = self.client.table("projects").upsert(project_data).execute()
            if res.data:
                logger.info(f"Project saved to Supabase: {project_id} (UUID: {project_uuid})")
                return res.data[0]
        except Exception as e:
            logger.error(f"Error saving project to Supabase: {e}")
        return None

    def list_projects(self, user_id: Optional[str] = None) -> list[dict[str, Any]]:
        """List all projects, optionally filtered by user_id (UUID/email/username)."""
        if not self.client:
            return []

        try:
            query = self.client.table("projects").select("id, user_id, title, prompt, project_json, created_at")
            if user_id:
                db_user_id = self._resolve_user_uuid(user_id)
                if db_user_id:
                    query = query.eq("user_id", db_user_id)
                else:
                    logger.warning(f"Could not resolve user UUID for listing projects: {user_id}")
                    return [] # Return empty list if user filter was requested but not found

            res = query.order("created_at", desc=True).execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error listing projects from Supabase: {e}")
        return []

    def get_project(self, project_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a specific project by project ID (string or UUID)."""
        if not self.client:
            return None

        project_uuid = self._get_project_uuid(project_id)
        try:
            res = self.client.table("projects").select("*").eq("id", project_uuid).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            logger.error(f"Error fetching project '{project_id}' from Supabase: {e}")
        return None

    def save_project_image(
        self,
        project_id: str,
        image_url: str,
        prompt: str,
        category: str
    ) -> Optional[dict[str, Any]]:
        """Save a generated image to project_images table in Supabase."""
        if not self.client:
            return None

        project_uuid = self._get_project_uuid(project_id)
        image_data = {
            "project_id": project_uuid,
            "image_url": image_url,
            "prompt": prompt,
            "category": category
        }
        try:
            res = self.client.table("project_images").insert(image_data).execute()
            if res.data:
                logger.info(f"Saved image to Supabase for project: {project_id} ({category})")
                return res.data[0]
        except Exception as e:
            logger.error(f"Error saving project image to Supabase: {e}")
        return None

    def update_project_art_status(
        self,
        project_id: str,
        status: str,
        generated_count: int,
        total_count: int
    ) -> Optional[dict[str, Any]]:
        """Update art generation progress in projects table."""
        if not self.client:
            return None

        project_uuid = self._get_project_uuid(project_id)
        try:
            res = self.client.table("projects").update({
                "art_generation_status": status,
                "generated_images": generated_count,
                "total_images": total_count
            }).eq("id", project_uuid).execute()
            if res.data:
                logger.info(f"Updated art status for project {project_id}: {status} ({generated_count}/{total_count})")
                return res.data[0]
        except Exception as e:
            logger.error(f"Error updating project art status: {e}")
        return None

    def get_project_images(self, project_id: str) -> list[dict[str, Any]]:
        """Get all images generated for a project."""
        if not self.client:
            return []

        project_uuid = self._get_project_uuid(project_id)
        try:
            res = self.client.table("project_images").select("*").eq("project_id", project_uuid).order("created_at").execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error fetching images for project {project_id}: {e}")
        return []

    def get_project_image(self, image_id: str) -> Optional[dict[str, Any]]:
        """Fetch a single image record by ID."""
        if not self.client:
            return None

        try:
            res = self.client.table("project_images").select("*").eq("id", image_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            logger.error(f"Error fetching project image {image_id}: {e}")
        return None

    def update_project_image_url(self, image_id: str, image_url: str) -> Optional[dict[str, Any]]:
        """Update the image URL for an existing project image (used in regeneration)."""
        if not self.client:
            return None

        try:
            res = self.client.table("project_images").update({
                "image_url": image_url
            }).eq("id", image_id).execute()
            if res.data:
                logger.info(f"Updated image URL for image {image_id}")
                return res.data[0]
        except Exception as e:
            logger.error(f"Error updating project image URL: {e}")
        return None

    def _local_atlas_load(self) -> list[dict[str, Any]]:
        import json
        path = "data/atlas_projects.json"
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _local_atlas_save(self, data: list[dict[str, Any]]):
        import json
        path = "data/atlas_projects.json"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save local atlas projects: {e}")

    def save_atlas_project(
        self,
        atlas_id: str,
        user_id: Optional[str],
        source_project_id: str,
        title: str,
        duration: str,
        tools: str,
        roadmap: list[dict],
        structure: list[str],
        flow_map: list[str],
        dependency_map: list[str],
        tasks: dict,
        generated_files: dict,
        zip_path: Optional[str] = None,
        feasibility_score: float = 0.0,
        success_probability: float = 0.0,
        estimated_completion_days: int = 0,
        required_hours_per_day: float = 0.0
    ) -> Optional[dict[str, Any]]:
        """Save/upsert an Atlas Project record in Supabase."""
        atlas_uuid = self._get_project_uuid(atlas_id)
        db_user_id = self._resolve_user_uuid(user_id) if user_id and self.client else (user_id or "spotifysahir007@gmail.com")
        db_source_project_id = self._get_project_uuid(source_project_id)

        import datetime
        created_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

        atlas_data = {
            "id": atlas_uuid,
            "user_id": db_user_id,
            "source_project_id": db_source_project_id,
            "title": title,
            "duration": duration,
            "tools": tools,
            "roadmap": roadmap,
            "structure": structure,
            "flow_map": flow_map,
            "dependency_map": dependency_map,
            "tasks": tasks,
            "generated_files": generated_files,
            "zip_path": zip_path,
            "created_at": created_str,
            "feasibility_score": feasibility_score,
            "success_probability": success_probability,
            "estimated_completion_days": estimated_completion_days,
            "required_hours_per_day": required_hours_per_day
        }

        if not self.client:
            logger.warning("Supabase client not initialized. Saving Atlas Project locally.")
            local_data = self._local_atlas_load()
            local_data = [x for x in local_data if x.get("id") != atlas_uuid]
            local_data.append(atlas_data)
            self._local_atlas_save(local_data)
            return atlas_data

        try:
            res = self.client.table("atlas_projects").upsert(atlas_data).execute()
            if res.data:
                logger.info(f"Atlas Project saved to Supabase: {atlas_id} (UUID: {atlas_uuid})")
                return res.data[0]
        except Exception as e:
            err_msg = str(e)
            if "atlas_projects" in err_msg and ("PGRST205" in err_msg or "schema cache" in err_msg or "not found" in err_msg):
                logger.warning("atlas_projects table not found in Supabase. Falling back to local data/atlas_projects.json.")
                local_data = self._local_atlas_load()
                local_data = [x for x in local_data if x.get("id") != atlas_uuid]
                local_data.append(atlas_data)
                self._local_atlas_save(local_data)
                return atlas_data
            else:
                logger.error(f"Error saving Atlas Project: {e}")
        return None

    def save_atlas_tasks(self, atlas_id: str, tasks_list: list) -> None:
        """Save tasks list to atlas_tasks table if it exists."""
        if not self.client:
            return
        atlas_uuid = self._get_project_uuid(atlas_id)
        try:
            # Delete old tasks for this atlas project first
            try:
                self.client.table("atlas_tasks").delete().eq("atlas_id", atlas_uuid).execute()
            except Exception:
                pass
            for t in tasks_list:
                db_task = {
                    "atlas_id": atlas_uuid,
                    "task_id": t.get("task_id", ""),
                    "title": t.get("title", ""),
                    "status": t.get("status", "Todo"),
                    "assignee": t.get("assignee", ""),
                    "dependencies": t.get("dependencies", [])
                }
                self.client.table("atlas_tasks").insert(db_task).execute()
            logger.info(f"Saved {len(tasks_list)} tasks to atlas_tasks in Supabase")
        except Exception as e:
            logger.warning(f"Could not save to atlas_tasks (table may not exist): {e}")

    def save_atlas_milestones(self, atlas_id: str, milestones_list: list) -> None:
        """Save milestones list to atlas_milestones table if it exists."""
        if not self.client:
            return
        atlas_uuid = self._get_project_uuid(atlas_id)
        try:
            try:
                self.client.table("atlas_milestones").delete().eq("atlas_id", atlas_uuid).execute()
            except Exception:
                pass
            for m in milestones_list:
                db_milestone = {
                    "atlas_id": atlas_uuid,
                    "title": m.get("title") or str(m),
                    "description": m.get("description", ""),
                    "due_date": m.get("due_date")
                }
                self.client.table("atlas_milestones").insert(db_milestone).execute()
            logger.info(f"Saved {len(milestones_list)} milestones to atlas_milestones in Supabase")
        except Exception as e:
            logger.warning(f"Could not save to atlas_milestones (table may not exist): {e}")

    def save_atlas_flow(self, atlas_id: str, flow_list: list) -> None:
        """Save flow list to atlas_flow table if it exists."""
        if not self.client:
            return
        atlas_uuid = self._get_project_uuid(atlas_id)
        try:
            try:
                self.client.table("atlas_flow").delete().eq("atlas_id", atlas_uuid).execute()
            except Exception:
                pass
            for idx, step in enumerate(flow_list):
                db_flow = {
                    "atlas_id": atlas_uuid,
                    "step_order": idx + 1,
                    "step_name": step
                }
                self.client.table("atlas_flow").insert(db_flow).execute()
            logger.info(f"Saved {len(flow_list)} flow steps to atlas_flow in Supabase")
        except Exception as e:
            logger.warning(f"Could not save to atlas_flow (table may not exist): {e}")

    def save_atlas_risks(self, atlas_id: str, risks_list: list) -> None:
        """Save risks list to atlas_risks table if it exists."""
        if not self.client:
            return
        atlas_uuid = self._get_project_uuid(atlas_id)
        try:
            try:
                self.client.table("atlas_risks").delete().eq("atlas_id", atlas_uuid).execute()
            except Exception:
                pass
            for r in risks_list:
                db_risk = {
                    "atlas_id": atlas_uuid,
                    "category": r.get("category", ""),
                    "description": r.get("description", ""),
                    "severity": r.get("severity", ""),
                    "mitigation": r.get("mitigation", "")
                }
                self.client.table("atlas_risks").insert(db_risk).execute()
            logger.info(f"Saved {len(risks_list)} risks to atlas_risks in Supabase")
        except Exception as e:
            logger.warning(f"Could not save to atlas_risks (table may not exist): {e}")

    def save_atlas_images(self, atlas_id: str, images_list: list) -> None:
        """Save images list to atlas_images table if it exists."""
        if not self.client:
            return
        atlas_uuid = self._get_project_uuid(atlas_id)
        try:
            try:
                self.client.table("atlas_images").delete().eq("atlas_id", atlas_uuid).execute()
            except Exception:
                pass
            for img in images_list:
                db_image = {
                    "atlas_id": atlas_uuid,
                    "image_url": img.get("image_url", ""),
                    "category": img.get("category", "")
                }
                self.client.table("atlas_images").insert(db_image).execute()
            logger.info(f"Saved {len(images_list)} images to atlas_images in Supabase")
        except Exception as e:
            logger.warning(f"Could not save to atlas_images (table may not exist): {e}")

    def save_atlas_exports(self, atlas_id: str, exports_list: list) -> None:
        """Save exports list to atlas_exports table if it exists."""
        if not self.client:
            return
        atlas_uuid = self._get_project_uuid(atlas_id)
        try:
            try:
                self.client.table("atlas_exports").delete().eq("atlas_id", atlas_uuid).execute()
            except Exception:
                pass
            for exp in exports_list:
                db_export = {
                    "atlas_id": atlas_uuid,
                    "file_name": exp.get("file_name", ""),
                    "file_type": exp.get("file_type", ""),
                    "file_url": exp.get("file_url", "")
                }
                self.client.table("atlas_exports").insert(db_export).execute()
            logger.info(f"Saved {len(exports_list)} exports to atlas_exports in Supabase")
        except Exception as e:
            logger.warning(f"Could not save to atlas_exports (table may not exist): {e}")

    def get_atlas_project(self, atlas_id: str) -> Optional[dict[str, Any]]:
        """Fetch an Atlas project by ID."""
        atlas_uuid = self._get_project_uuid(atlas_id)
        if not self.client:
            local_data = self._local_atlas_load()
            return next((x for x in local_data if x.get("id") == atlas_uuid), None)

        try:
            res = self.client.table("atlas_projects").select("*").eq("id", atlas_uuid).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            err_msg = str(e)
            if "atlas_projects" in err_msg and ("PGRST205" in err_msg or "schema cache" in err_msg or "not found" in err_msg):
                local_data = self._local_atlas_load()
                return next((x for x in local_data if x.get("id") == atlas_uuid), None)
            else:
                logger.error(f"Error fetching Atlas Project '{atlas_id}': {e}")
        return None

    def get_atlas_projects_by_source(self, source_project_id: str) -> list[dict[str, Any]]:
        """Fetch all Atlas projects linked to a source project ID."""
        db_source_project_id = self._get_project_uuid(source_project_id)
        if not self.client:
            local_data = self._local_atlas_load()
            return [x for x in local_data if x.get("source_project_id") == db_source_project_id]

        try:
            res = self.client.table("atlas_projects").select("*").eq("source_project_id", db_source_project_id).order("created_at").execute()
            return res.data or []
        except Exception as e:
            err_msg = str(e)
            if "atlas_projects" in err_msg and ("PGRST205" in err_msg or "schema cache" in err_msg or "not found" in err_msg):
                local_data = self._local_atlas_load()
                return [x for x in local_data if x.get("source_project_id") == db_source_project_id]
            else:
                logger.error(f"Error fetching Atlas projects for source project '{source_project_id}': {e}")
        return []

    def list_atlas_projects(self, user_id: Optional[str] = None) -> list[dict[str, Any]]:
        """List all Atlas projects, optionally filtered by user_id."""
        db_user_id = self._resolve_user_uuid(user_id) if user_id and self.client else user_id

        if not self.client:
            local_data = self._local_atlas_load()
            if db_user_id:
                local_data = [x for x in local_data if x.get("user_id") == db_user_id]
            local_data.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return local_data

        try:
            query = self.client.table("atlas_projects").select("*")
            if user_id:
                db_user_id = self._resolve_user_uuid(user_id)
                if db_user_id:
                    query = query.eq("user_id", db_user_id)
                else:
                    return []
            res = query.order("created_at", desc=True).execute()
            return res.data or []
        except Exception as e:
            err_msg = str(e)
            if "atlas_projects" in err_msg and ("PGRST205" in err_msg or "schema cache" in err_msg or "not found" in err_msg):
                local_data = self._local_atlas_load()
                if db_user_id:
                    local_data = [x for x in local_data if x.get("user_id") == db_user_id]
                local_data.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                return local_data
            else:
                logger.error(f"Error listing Atlas projects: {e}")
        return []

    def delete_atlas_project(self, atlas_id: str) -> bool:
        """Delete an Atlas project from Supabase."""
        atlas_uuid = self._get_project_uuid(atlas_id)
        if not self.client:
            local_data = self._local_atlas_load()
            initial_len = len(local_data)
            local_data = [x for x in local_data if x.get("id") != atlas_uuid]
            self._local_atlas_save(local_data)
            return len(local_data) < initial_len

        try:
            res = self.client.table("atlas_projects").delete().eq("id", atlas_uuid).execute()
            if res.data:
                logger.info(f"Atlas Project deleted: {atlas_id} (UUID: {atlas_uuid})")
                return True
        except Exception as e:
            err_msg = str(e)
            if "atlas_projects" in err_msg and ("PGRST205" in err_msg or "schema cache" in err_msg or "not found" in err_msg):
                local_data = self._local_atlas_load()
                initial_len = len(local_data)
                local_data = [x for x in local_data if x.get("id") != atlas_uuid]
                self._local_atlas_save(local_data)
                return len(local_data) < initial_len
            else:
                logger.error(f"Error deleting Atlas Project '{atlas_id}': {e}")
        return False
