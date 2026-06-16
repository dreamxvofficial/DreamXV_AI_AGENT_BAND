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
            "name": name,
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

            res = query.order("created_at", descending=True).execute()
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
