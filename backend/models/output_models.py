"""
DreamXV AI Studio — Pydantic Output Models
===========================================
Structured output schemas for every agent.
Used with PydanticAI-style structured generation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Union
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


class ImagePromptItem(BaseModel):
    """A single dynamically generated prompt for AI Art."""
    prompt: str = Field(..., description="Cinematic image prompt including composition, lighting, subject, and style detail.")
    category: str = Field(..., description="Category: character, environment, scene, landmark, or gameplay.")


class ImagePromptsList(BaseModel):
    """List of exactly 6 dynamically generated art prompts."""
    prompts: list[ImagePromptItem] = Field(..., description="Exactly 6 image prompts representing different aspects of the project.")


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


# ─── Reviewer Agent ────────────────────────────────────────────────────────
class ReviewIssue(BaseModel):
    """A single inconsistency detected by the Reviewer Agent."""
    category: str = Field(
        default="general",
        description="Category: story, character, world, gameplay, naming",
    )
    description: str = Field(..., description="Description of the inconsistency")
    severity: str = Field(
        default="warning",
        description="Severity: critical, warning, info",
    )
    suggested_fix: str = Field(
        default="",
        description="Suggested resolution",
    )
    references: list[str] = Field(
        default_factory=list,
        description="References to conflicting elements",
    )


class ReviewerOutput(BaseModel):
    """Cross-agent consistency review produced by the Reviewer Agent."""
    consistency_score: float = Field(
        default=0.0,
        ge=0.0,
        le=10.0,
        description="Overall consistency score out of 10",
    )
    issues: list[ReviewIssue] = Field(
        default_factory=list,
        description="List of detected inconsistencies",
    )
    summary: str = Field(
        default="",
        description="Overall review summary",
    )


# ─── Documentation Agent ──────────────────────────────────────────────────
class DocumentationOutput(BaseModel):
    """Project documentation produced by the Documentation Agent."""
    readme: str = Field(
        default="",
        description="README.md content",
    )
    gdd: str = Field(
        default="",
        description="Game Design Document content",
    )
    feature_list: list[str] = Field(
        default_factory=list,
        description="List of game features",
    )
    core_mechanics: list[str] = Field(
        default_factory=list,
        description="Core gameplay mechanics",
    )
    monetization: list[str] = Field(
        default_factory=list,
        description="Monetization strategies and ideas",
    )
    future_expansion: list[str] = Field(
        default_factory=list,
        description="Future expansion and DLC ideas",
    )
    technical_summary: str = Field(
        default="",
        description="Technical architecture summary",
    )
    elevator_pitch: str = Field(
        default="",
        description="30-second elevator pitch",
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
    reviewer_directive: str = Field(
        default="Review all agent outputs for cross-domain consistency.",
        description="Instructions for Reviewer Agent",
    )
    documentation_directive: str = Field(
        default="Generate comprehensive project documentation from all agent outputs.",
        description="Instructions for Documentation Agent",
    )
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
    art: Optional[Union[ArtOutput, dict]] = None
    qa: Optional[QAOutput] = None
    review: Optional[ReviewerOutput] = None
    documentation: Optional[DocumentationOutput] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─── Atlas Agent ─────────────────────────────────────────────────────────────
class AtlasPhase(BaseModel):
    """A single roadmap phase containing a name and a list of tasks."""
    name: str = Field(..., description="Phase name (e.g., Phase 1: Project Setup)")
    tasks: list[str] = Field(..., description="Tasks associated with this phase")


class AtlasTaskBreakdown(BaseModel):
    """Production tasks broken down by priority/timeline status."""
    critical_tasks: list[str] = Field(..., description="High-priority critical path tasks")
    optional_tasks: list[str] = Field(..., description="Optional features or nice-to-haves")
    future_expansion: list[str] = Field(..., description="Long-term expansion or DLC ideas")


class AtlasOutput(BaseModel):
    """Structured production blueprint produced by the Atlas Agent."""
    project_id: str = Field(..., description="Associated project identifier")
    roadmap: list[AtlasPhase] = Field(..., description="Ordered milestones of the roadmap")
    project_structure: list[str] = Field(..., description="List of folders and files relative to project root")
    production_flow_map: list[str] = Field(..., description="Ordered steps of production flow workflow")
    dependency_map: list[str] = Field(..., description="Code/asset dependency mapping")
    task_breakdown: AtlasTaskBreakdown = Field(..., description="Categorized tasks breakdown")

