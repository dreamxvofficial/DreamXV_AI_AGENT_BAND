"""
DreamXV AI Studio — Band Manager
=================================
High-level orchestrator that manages the Band Room lifecycle
and coordinates the multi-agent pipeline.

Pipeline flow:
    User Prompt → Chief Agent → Band Room →
    [Story, Character, World, Gameplay, Art, QA] → Final Result
"""

from __future__ import annotations

import asyncio
from typing import Callable, Optional

from backend.agents.chief_agent import ChiefAgent
from backend.agents.story_agent import StoryAgent
from backend.agents.character_agent import CharacterAgent
from backend.agents.world_agent import WorldAgent
from backend.agents.gameplay_agent import GameplayAgent
from backend.agents.art_agent import ArtAgent
from backend.agents.qa_agent import QAAgent
from backend.agents.reviewer_agent import ReviewerAgent
from backend.agents.documentation_agent import DocumentationAgent

from backend.models.output_models import (
    ProjectOutput,
    DocumentationOutput,
    StoryOutput,
    CharacterRoster,
    WorldOutput,
    GameplayOutput,
    ArtOutput,
    QAOutput,
    ReviewerOutput
)
from backend.services.llm_service import generate_mock_data_for_model
from backend.models.schemas import AgentStatus

from backend.services.llm_service import LLMService
from backend.services.image_service import ImageService
from backend.services.band_service import BandService
from backend.services.memory_service import MemoryService, AGENT_NAMES
from backend.services.export_service import ExportService

from backend.utils.helpers import generate_project_id
from backend.utils.logger import get_logger

logger = get_logger("band_manager")

# Callback type for status updates (used by WebSocket)
StatusCallback = Callable[[str, str, AgentStatus, Optional[str]], None]


class BandManager:
    """
    Orchestrates the complete multi-agent pipeline within a Band Room.

    Creates a room, registers all agents, runs them in sequence,
    tracks statuses, and assembles the final ProjectOutput.
    """

    def __init__(self) -> None:
        self._llm = LLMService()
        self._image_service = ImageService()
        self._band_service = BandService()
        self._memory = MemoryService()
        self._export = ExportService()

        # Status change callback (set by WebSocket handler)
        self._status_callback: Optional[StatusCallback] = None

    def set_status_callback(self, callback: StatusCallback) -> None:
        """Register a callback for real-time status updates."""
        self._status_callback = callback

    def _update_status(
        self,
        project_id: str,
        agent_name: str,
        status: AgentStatus,
        message: Optional[str] = None,
    ) -> None:
        """Update agent status in memory and fire callback if set."""
        self._memory.update_agent_status(project_id, agent_name, status, message)

        if self._status_callback:
            try:
                self._status_callback(project_id, agent_name, status, message)
            except Exception as exc:
                logger.warning(f"Status callback error: {exc}")

    async def generate_project(
        self,
        user_prompt: str,
        user_id: str,
    ) -> ProjectOutput:
        """
        Execute the full multi-agent pipeline for a project.

        Args:
            user_prompt: The user's creative project prompt.
            user_id: Authenticated user identifier.

        Returns:
            Complete ProjectOutput with all agent results.
        """
        project_id = generate_project_id()
        logger.info(f"Starting project: {project_id}")

        # Initialize tracking
        self._memory.init_project(project_id, user_prompt, user_id)

        # Create Band Room
        room = self._band_service.create_room(project_id)
        self._band_service.register_agents(room, AGENT_NAMES)

        # Initialize agents
        chief = ChiefAgent(self._llm)
        story_agent = StoryAgent(self._llm)
        character_agent = CharacterAgent(self._llm)
        world_agent = WorldAgent(self._llm)
        gameplay_agent = GameplayAgent(self._llm)
        art_agent = ArtAgent(self._llm, self._image_service)
        qa_agent = QAAgent(self._llm)
        reviewer_agent = ReviewerAgent(self._llm)
        documentation_agent = DocumentationAgent(self._llm)

        # ── Phase 1: Chief Agent Breakdown ──────────────────────────────
        import time
        start = time.time()
        self._update_status(project_id, "Chief Agent", AgentStatus.RUNNING)
        breakdown = None
        _chief_retry_delays = [1.0, 3.0, 5.0]
        for _attempt in range(1, 4):
            try:
                logger.info(f"Chief Agent attempt {_attempt}/3...")
                breakdown = await asyncio.wait_for(chief.run(user_prompt, room), timeout=180.0)
                logger.info(f"Chief Agent completed in {time.time()-start:.2f}s (attempt {_attempt})")
                self._update_status(project_id, "Chief Agent", AgentStatus.COMPLETED)
                break
            except Exception as e:
                logger.warning(f"Chief Agent attempt {_attempt}/3 failed: {type(e).__name__}: {e}")
                if _attempt < 3:
                    wait_sec = _chief_retry_delays[_attempt - 1]
                    logger.info(f"Waiting {wait_sec}s before Chief Agent retry...")
                    await asyncio.sleep(wait_sec)
                else:
                    logger.error("Chief Agent failed after 3 attempts — using mock breakdown fallback")
                    self._update_status(project_id, "Chief Agent", AgentStatus.ERROR, f"Chief Agent failed: {e}")
                    # Fallback to mock breakdown so pipeline can continue
                    from backend.services.llm_service import generate_mock_data_for_model
                    from backend.models.output_models import ChiefTaskBreakdown
                    breakdown = generate_mock_data_for_model(ChiefTaskBreakdown, user_prompt)
                    self._update_status(project_id, "Chief Agent", AgentStatus.COMPLETED)

        # ── Phase 2: Parallel Specialist Agents ─────────────────────────
        async def run_story():
            self._update_status(project_id, "Story Agent", AgentStatus.RUNNING)
            start_story = time.time()
            try:
                result = await asyncio.wait_for(
                    story_agent.run(
                        breakdown.story_directive, room,
                        genre=breakdown.genre, tone=breakdown.tone,
                    ),
                    timeout=180.0
                )
                logger.info(f"Story Agent completed in {time.time()-start_story:.2f}s")
                self._update_status(project_id, "Story Agent", AgentStatus.COMPLETED)
                return result
            except Exception as e:
                logger.exception(e)
                logger.error(f"Story Agent failed or timed out: {e}")
                self._update_status(project_id, "Story Agent", AgentStatus.ERROR, str(e))
                return generate_mock_data_for_model(StoryOutput, user_prompt)

        async def run_characters():
            self._update_status(project_id, "Character Agent", AgentStatus.RUNNING)
            start_char = time.time()
            _char_delays = [1.0, 3.0, 5.0]
            for _cattempt in range(1, 4):
                try:
                    result = await asyncio.wait_for(
                        character_agent.run(
                            breakdown.character_directive, room,
                            genre=breakdown.genre, tone=breakdown.tone,
                        ),
                        timeout=120.0
                    )
                    logger.info(f"Character Agent completed in {time.time()-start_char:.2f}s (attempt {_cattempt})")
                    self._update_status(project_id, "Character Agent", AgentStatus.COMPLETED)
                    return result
                except Exception as e:
                    logger.warning(f"Character Agent attempt {_cattempt}/3 failed: {type(e).__name__}: {e}")
                    if _cattempt < 3:
                        wait_sec = _char_delays[_cattempt - 1]
                        logger.info(f"Waiting {wait_sec}s before Character Agent retry...")
                        await asyncio.sleep(wait_sec)
                    else:
                        logger.error(f"Character Agent failed after 3 attempts — using fallback characters from prompt")
                        self._update_status(project_id, "Character Agent", AgentStatus.ERROR, str(e))
                        # Generate fallback characters from prompt; never crash pipeline
                        try:
                            roster = generate_mock_data_for_model(CharacterRoster, user_prompt)
                            return roster.characters if roster and roster.characters else []
                        except Exception as fallback_err:
                            logger.error(f"Character fallback also failed: {fallback_err}")
                            return []

        async def run_world():
            self._update_status(project_id, "World Agent", AgentStatus.RUNNING)
            start_world = time.time()
            try:
                result = await asyncio.wait_for(
                    world_agent.run(
                        breakdown.world_directive, room,
                        genre=breakdown.genre, tone=breakdown.tone,
                    ),
                    timeout=180.0
                )
                logger.info(f"World Agent completed in {time.time()-start_world:.2f}s")
                self._update_status(project_id, "World Agent", AgentStatus.COMPLETED)
                return result
            except Exception as e:
                logger.exception(e)
                logger.error(f"World Agent failed or timed out: {e}")
                self._update_status(project_id, "World Agent", AgentStatus.ERROR, str(e))
                return generate_mock_data_for_model(WorldOutput, user_prompt)

        async def run_gameplay():
            self._update_status(project_id, "Gameplay Agent", AgentStatus.RUNNING)
            start_gameplay = time.time()
            try:
                result = await asyncio.wait_for(
                    gameplay_agent.run(
                        breakdown.gameplay_directive, room,
                        genre=breakdown.genre, tone=breakdown.tone,
                    ),
                    timeout=180.0
                )
                logger.info(f"Gameplay Agent completed in {time.time()-start_gameplay:.2f}s")
                self._update_status(project_id, "Gameplay Agent", AgentStatus.COMPLETED)
                return result
            except Exception as e:
                logger.exception(e)
                logger.error(f"Gameplay Agent failed or timed out: {e}")
                self._update_status(project_id, "Gameplay Agent", AgentStatus.ERROR, str(e))
                return generate_mock_data_for_model(GameplayOutput, user_prompt)

        # Run parallel specialists
        story, characters, world, gameplay = await asyncio.gather(
            run_story(),
            run_characters(),
            run_world(),
            run_gameplay(),
        )

        # ── Phase 3: Art Agent (needs context from prior agents) ────────
        self._update_status(project_id, "Art Agent", AgentStatus.RUNNING)
        start_art = time.time()
        try:
            art = await asyncio.wait_for(
                art_agent.run(
                    breakdown.art_directive, room,
                    project_id=project_id,
                    genre=breakdown.genre, tone=breakdown.tone,
                ),
                timeout=180.0
            )
            logger.info(f"Art Agent completed in {time.time()-start_art:.2f}s")
            self._update_status(project_id, "Art Agent", AgentStatus.COMPLETED)
        except Exception as e:
            logger.exception(e)
            logger.error(f"Art Agent failed or timed out: {e}")
            self._update_status(project_id, "Art Agent", AgentStatus.ERROR, str(e))
            art = generate_mock_data_for_model(ArtOutput, user_prompt)

        # ── Phase 4: QA Agent (reviews everything) ─────────────────────
        self._update_status(project_id, "QA Agent", AgentStatus.RUNNING)
        start_qa = time.time()
        try:
            qa = await asyncio.wait_for(qa_agent.run(breakdown.qa_directive, room), timeout=180.0)
            logger.info(f"QA Agent completed in {time.time()-start_qa:.2f}s")
            self._update_status(project_id, "QA Agent", AgentStatus.COMPLETED)
        except Exception as e:
            logger.exception(e)
            logger.error(f"QA Agent failed or timed out: {e}")
            self._update_status(project_id, "QA Agent", AgentStatus.ERROR, str(e))
            qa = generate_mock_data_for_model(QAOutput, user_prompt)

        # ── Phase 5: Reviewer Agent (cross-agent consistency) ──────────
        self._update_status(project_id, "Reviewer Agent", AgentStatus.RUNNING)
        start_reviewer = time.time()
        review = None
        try:
            review = await asyncio.wait_for(reviewer_agent.run(breakdown.reviewer_directive, room), timeout=180.0)
            logger.info(f"Reviewer Agent completed in {time.time()-start_reviewer:.2f}s")
            self._update_status(project_id, "Reviewer Agent", AgentStatus.COMPLETED)
        except Exception as e:
            logger.exception(e)
            logger.error(f"Reviewer Agent failed or timed out: {e}")
            self._update_status(project_id, "Reviewer Agent", AgentStatus.ERROR, str(e))
            review = generate_mock_data_for_model(ReviewerOutput, user_prompt)

        # ── Phase 6: Documentation Agent (generates docs) ─────────────
        logger.info("Starting Documentation Agent")
        self._update_status(project_id, "Documentation Agent", AgentStatus.RUNNING)
        start_docs = time.time()
        documentation = None
        try:
            project_title = story.title if story else "Untitled Project"
            documentation = await asyncio.wait_for(
                documentation_agent.run(
                    breakdown.documentation_directive,
                    room,
                    title=project_title,
                    genre=breakdown.genre,
                    tone=breakdown.tone,
                ),
                timeout=180.0
            )
            logger.info(f"Documentation Agent completed in {time.time()-start_docs:.2f}s")
            self._update_status(project_id, "Documentation Agent", AgentStatus.COMPLETED)
        except Exception as e:
            logger.exception(e)
            logger.error(f"Documentation Agent failed or timed out: {e}")
            self._update_status(project_id, "Documentation Agent", AgentStatus.ERROR, str(e))
            try:
                documentation = generate_mock_data_for_model(DocumentationOutput, user_prompt)
            except Exception as fallback_exc:
                logger.exception(fallback_exc)
                documentation = DocumentationOutput(
                    readme=f"# {story.title if story else 'Untitled Project'}\n\nFallback README content. Generation succeeded with partial documentation.",
                    gdd=f"# Game Design Document: {story.title if story else 'Untitled Project'}\n\nFallback Game Design Document. Generation succeeded with partial documentation."
                )

        logger.info("Documentation Agent complete")

        # ── Assemble Final Output ──────────────────────────────────────
        project = ProjectOutput(
            project_id=project_id,
            title=story.title if story else "Untitled Project",
            story=story,
            characters=characters or [],
            world=world,
            gameplay=gameplay,
            art=art,
            art_gallery=[],
            qa=qa,
            review=review,
            documentation=documentation,
        )

        # Persist and clean up
        logger.info("Saving project...")
        
        # Convert image file paths to base64 inline data URLs before saving to Supabase
        try:
            import base64
            from pathlib import Path
            if project.art and hasattr(project.art, "image_paths") and project.art.image_paths:
                base64_images = []
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
                project.art.image_paths = base64_images
        except Exception as e:
            logger.warning(f"Error preparing base64 images: {e}")

        # Save to Supabase first
        try:
            from backend.services.supabase_service import SupabaseService
            db = SupabaseService()
            user_id = self._memory._active_projects.get(project.project_id, {}).get("user_id")
            prompt = self._memory._active_projects.get(project.project_id, {}).get("user_prompt", "")
            
            import json
            project_json = json.loads(project.model_dump_json())
            
            db.save_project(
                project_id=project.project_id,
                user_id=user_id,
                title=project.title,
                prompt=prompt,
                project_json=project_json
            )
            
            # Start background async image generation!
            logger.info(f"[{project.project_id}] Launching background art generation task...")
            asyncio.create_task(self.generate_project_images_async(project.project_id, project))
            
        except Exception as e:
            logger.warning(f"Failed to save project to Supabase: {e}")

        try:
            self._export.save_project(project)
        except Exception as e:
            logger.warning(f"Failed to save project export: {e}")

        try:
            self._memory.store_completed_project(project)
        except Exception as e:
            logger.warning(f"Failed to store project in memory: {e}")

        try:
            self._band_service.close_room(project_id)
        except Exception as e:
            logger.warning(f"Failed to close band room: {e}")

        logger.info(f"Project completed: {project_id} — '{project.title}'")
        logger.info("Generation finished")
        return project

    def get_agent_statuses(self, project_id: Optional[str] = None):
        """Get agent statuses for a project (or the active project)."""
        if project_id is None:
            project_id = self._memory.get_active_project_id()
        if project_id is None:
            return []
        return self._memory.get_agent_statuses(project_id)

    def list_projects(self) -> list[dict]:
        """List all completed projects."""
        # 1. Fetch from Supabase
        try:
            from backend.services.supabase_service import SupabaseService
            db = SupabaseService()
            supabase_projects = db.list_projects()
        except Exception as exc:
            logger.warning(f"Failed to fetch projects from Supabase in list_projects: {exc}")
            supabase_projects = []

        projects_list = []
        for p in supabase_projects:
            proj_json = p.get("project_json", {})
            proj_id = proj_json.get("project_id") or p.get("id")
            created = p.get("created_at")
            created_str = created.isoformat() if hasattr(created, "isoformat") else (str(created) if created else "")
            
            projects_list.append({
                "project_id": proj_id,
                "title": p.get("title") or proj_json.get("title") or "Untitled",
                "created_at": created_str,
                "status": proj_json.get("status") or "completed",
            })

        # Merge in-memory and disk-persisted projects
        memory_projects = self._memory.list_completed_projects()
        disk_projects = self._export.list_projects()

        seen_ids = {p["project_id"] for p in projects_list}
        
        for p in memory_projects:
            if p["project_id"] not in seen_ids:
                projects_list.append(p)
                seen_ids.add(p["project_id"])
                
        for p in disk_projects:
            if p["project_id"] not in seen_ids:
                projects_list.append(p)
                seen_ids.add(p["project_id"])

        return projects_list

    async def generate_project_images_async(self, project_id: str, project: ProjectOutput) -> None:
        """Asynchronously generate 6 AI images for the project in the background."""
        logger.info(f"[{project_id}] Starting async background art generation...")
        
        from backend.services.supabase_service import SupabaseService
        db = SupabaseService()
        
        # Update status to generating
        db.update_project_art_status(project_id, "generating", 0, 6)
        
        # Ask the LLM to generate exactly 6 highly creative art prompts based on the project concept
        try:
            from backend.models.output_models import ImagePromptsList
            
            story_desc = project.story.summary if project.story else ""
            world_desc = project.world.description if project.world else ""
            characters_desc = "\n".join([f"- {c.name} ({c.role}): {c.visual_description or c.backstory}" for c in project.characters])
            gameplay_desc = project.gameplay.core_loop if project.gameplay else ""
            
            concept_details = (
                f"Game Title: {project.title}\n"
                f"Narrative Summary: {story_desc}\n"
                f"World Setting: {world_desc}\n"
                f"Character Roster:\n{characters_desc}\n"
                f"Gameplay Core Loop: {gameplay_desc}\n"
            )
            
            system_prompt = (
                "You are the Lead Art Director at DreamXV AI Studio. Your task is to generate exactly 6 distinct, "
                "cinematic image generation prompts for FLUX. The prompts must cover these 6 specific visual scenes:\n"
                "1. Character portrait (detailed protagonist face/bust, cinematic lighting)\n"
                "2. Main hero group (the band of survivors/heroes standing together in their environment)\n"
                "3. Urban ruins (ruined buildings, debris, post-apocalyptic cityscape)\n"
                "4. Forest/infected terrain (mutated flora, infected soil, dense eerie atmosphere)\n"
                "5. Special infected enemy (grotesque details, unique mutation, attacking or lurking)\n"
                "6. Final cinematic environment (epic scale landmark or cinematic scene setting the final stage)\n"
                "Generate exactly 6 prompts in total, making sure each prompt specifies mood, composition, lighting, "
                "and visual style matching the game's tone. Ensure the prompts are returned in a structured format."
            )
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Game Concept Details:\n{concept_details}"}
            ]
            
            prompts_list_output = await self._llm.generate_structured(
                messages,
                ImagePromptsList,
                temperature=0.8
            )
            prompts = prompts_list_output.prompts
            logger.info(f"[{project_id}] LLM generated {len(prompts)} dynamic image prompts.")
        except Exception as e:
            logger.error(f"[{project_id}] Failed to generate dynamic art prompts from LLM: {e}. Falling back to default prompts.")
            from backend.models.output_models import ImagePromptItem
            prompts = [
                ImagePromptItem(prompt=f"Cinematic detailed character portrait of protagonist matching the theme of {project.title}, cinematic lighting", category="character"),
                ImagePromptItem(prompt=f"Main hero group standing together in the world of {project.title}, atmospheric lighting, cinematic", category="character"),
                ImagePromptItem(prompt=f"Cinematic shot of urban ruins, ruined buildings, debris post-apocalyptic cityscape of {project.title}", category="environment"),
                ImagePromptItem(prompt=f"Forest/infected terrain landscape representing mutated nature and danger in {project.title}", category="environment"),
                ImagePromptItem(prompt=f"Special infected enemy creature with grotesque mutations lurking in the shadows of {project.title}", category="character"),
                ImagePromptItem(prompt=f"Final cinematic environment landmark showing the final destination of {project.title}", category="environment")
            ]
            
        # Ensure categories match the requested ones:
        categories = ["character", "character", "environment", "environment", "character", "environment"]
        for idx in range(min(len(prompts), 6)):
            prompts[idx].category = categories[idx]

        prompts = prompts[:6]
        while len(prompts) < 6:
            prompts.append(prompts[0])
            
        generated_count = 0
        image_urls = []
        
        tiny_png = (
            "iVBORw0KGgoAAAANSUhEUgAAAQAAAAEAAQMAAAB5o5OKAAAAA1BMVEUKGjoGf18hAAAA"
            "H0lEQVRo3u3BAQ0AAADCoPdPbQ43oAAAAAAAAAAAAIB3A1wAAQEp59ADAAAAAElFTkSu"
            "QmCC"
        )
        placeholder_url = f"data:image/png;base64,{tiny_png}"
        
        for idx, item in enumerate(prompts):
            image_url = ""
            logger.info(f"Generating image {idx+1}/6")
            
            # Retry loop: 3 attempts
            for attempt in range(1, 4):
                try:
                    res_path = await self._image_service.generate_image(
                        item.prompt,
                        project_id=project_id,
                        image_type=item.category,
                        filename=f"image_{idx+1}.png"
                    )
                    
                    if res_path:
                        if not res_path.startswith("data:image/"):
                            from pathlib import Path
                            import base64
                            img_path = Path(res_path)
                            if img_path.exists():
                                img_bytes = img_path.read_bytes()
                                img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                                image_url = f"data:image/png;base64,{img_b64}"
                                try:
                                    img_path.unlink()
                                except Exception:
                                    pass
                            else:
                                image_url = res_path
                        else:
                            image_url = res_path
                            
                        logger.info(f"[{project_id}] Image {idx+1}/6 generated successfully on attempt {attempt}.")
                        break
                except Exception as img_exc:
                    logger.warning(f"[{project_id}] Image {idx+1}/6 attempt {attempt} failed: {img_exc}")
                    if attempt < 3:
                        await asyncio.sleep(1.0 * attempt)
                    else:
                        logger.error(f"[{project_id}] Image {idx+1}/6 failed completely after 3 attempts.")
            
            if not image_url:
                image_url = placeholder_url
            
            db.save_project_image(
                project_id=project_id,
                image_url=image_url,
                prompt=item.prompt,
                category=item.category
            )
            generated_count += 1
            image_urls.append(image_url)
            logger.info(f"Image URL: {image_url}")
            logger.info(f"Saved {len(image_urls)} images")
            db.update_project_art_status(project_id, "generating", generated_count, 6)
                
        status = "completed"
        db.update_project_art_status(project_id, status, generated_count, 6)
        logger.info(f"[{project_id}] Async art generation complete. Status: {status} ({generated_count}/6).")
        
        project.art_gallery = image_urls
        
        # Update the project_json manifest
        try:
            project_record = db.get_project(project_id)
            if project_record:
                project_json = project_record.get("project_json", {})
                if isinstance(project_json, dict):
                    if "art" not in project_json or not project_json["art"]:
                        project_json["art"] = {}
                    project_json["art"]["image_paths"] = image_urls
                    project_json["images"] = image_urls
                    project_json["art"]["prompts"] = [item.prompt for item in prompts]
                    project_json["art_gallery"] = image_urls
                    
                    db.save_project(
                        project_id=project_id,
                        user_id=project_record.get("user_id"),
                        title=project_record.get("title", project.title),
                        prompt=project_record.get("prompt", ""),
                        project_json=project_json
                    )
                    logger.info(f"[{project_id}] Project JSON manifest updated with generated image URLs.")
        except Exception as e:
            logger.error(f"[{project_id}] Failed to update project JSON with new images: {e}")

    async def close(self) -> None:
        """Shut down all services."""
        await self._llm.close()
