"""
DreamXV AI Studio — Pydantic Output Models
===========================================
Structured output schemas for every agent.
Used with PydanticAI-style structured generation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


# ─── Story Agent ────────────────────────────────────────────────────────────
class StoryOutput(BaseModel):
    """Narrative output produced by the Story Agent."""
    title: str = Field(..., description="Title of the game/story")
    lore: str = Field(..., description="Deep background lore")
    summary: str = Field(..., description="High-level story synopsis")
    acts: list[str] = Field(
        default_factory=list,
        description="Ordered list of major story acts/chapters",
    )
    themes: list[str] = Field(
        default_factory=list,
        description="Core narrative themes",
    )


# ─── Character Agent ───────────────────────────────────────────────────────
class CharacterOutput(BaseModel):
    """Single character definition produced by the Character Agent."""
    name: str = Field(..., description="Character name")
    role: str = Field(..., description="Role in the story (protagonist, antagonist, NPC…)")
    backstory: str = Field(..., description="Character backstory")
    abilities: list[str] = Field(
        default_factory=list,
        description="List of abilities or powers",
    )
    personality_traits: list[str] = Field(
        default_factory=list,
        description="Defining personality traits",
    )
    visual_description: str = Field(
        default="",
        description="Visual appearance for art generation",
    )


class CharacterRoster(BaseModel):
    """Collection of characters for a project."""
    characters: list[CharacterOutput] = Field(
        default_factory=list,
        description="All generated characters",
    )


# ─── World Agent ───────────────────────────────────────────────────────────
class WorldOutput(BaseModel):
    """World-building output produced by the World Agent."""
    name: str = Field(..., description="World / setting name")
    description: str = Field(..., description="Overall world description")
    regions: list[str] = Field(
        default_factory=list,
        description="Named regions or locations",
    )
    lore_elements: list[str] = Field(
        default_factory=list,
        description="Key lore elements, factions, or history points",
    )
    atmosphere: str = Field(
        default="",
        description="Mood and atmospheric description",
    )


# ─── Gameplay Agent ────────────────────────────────────────────────────────
class GameplayOutput(BaseModel):
    """Gameplay systems output produced by the Gameplay Agent."""
    core_loop: str = Field(..., description="Description of the core gameplay loop")
    mechanics: list[str] = Field(
        default_factory=list,
        description="List of gameplay mechanics",
    )
    progression_system: str = Field(
        default="",
        description="Progression / leveling system design",
    )
    difficulty_curve: str = Field(
        default="",
        description="Difficulty scaling approach",
    )


# ─── Art Agent ─────────────────────────────────────────────────────────────
class ArtOutput(BaseModel):
    """Art generation output produced by the Art Agent."""
    prompts: list[str] = Field(
        default_factory=list,
        description="Cinematic image prompts for generation",
    )
    image_paths: list[str] = Field(
        default_factory=list,
        description="File paths of generated images",
    )
    style_guide: str = Field(
        default="",
        description="Visual style guidelines",
    )


# ─── QA Agent ──────────────────────────────────────────────────────────────
class QAOutput(BaseModel):
    """Quality assurance output produced by the QA Agent."""
    consistency_score: float = Field(
        default=0.0,
        ge=0.0,
        le=10.0,
        description="Consistency score out of 10",
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Identified issues or inconsistencies",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Improvement suggestions",
    )
    overall_assessment: str = Field(
        default="",
        description="Summary assessment of the full project",
    )


# ─── Chief Agent / Full Project ────────────────────────────────────────────
class ChiefTaskBreakdown(BaseModel):
    """Sub-task decomposition produced by the Chief Agent."""
    story_directive: str = Field(..., description="Instructions for Story Agent")
    character_directive: str = Field(..., description="Instructions for Character Agent")
    world_directive: str = Field(..., description="Instructions for World Agent")
    gameplay_directive: str = Field(..., description="Instructions for Gameplay Agent")
    art_directive: str = Field(..., description="Instructions for Art Agent")
    qa_directive: str = Field(..., description="Instructions for QA Agent")
    genre: str = Field(default="", description="Identified genre")
    tone: str = Field(default="", description="Identified tone/mood")


class ProjectOutput(BaseModel):
    """Aggregated output of all agents for a complete project."""
    project_id: str = Field(..., description="Unique project identifier")
    title: str = Field(default="Untitled Project", description="Project title")
    story: Optional[StoryOutput] = None
    characters: list[CharacterOutput] = Field(default_factory=list)
    world: Optional[WorldOutput] = None
    gameplay: Optional[GameplayOutput] = None
    art: Optional[ArtOutput] = None
    qa: Optional[QAOutput] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
