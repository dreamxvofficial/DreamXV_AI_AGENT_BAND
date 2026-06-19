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
    lore: str = Field(..., description="Full Lore Backstory. Must be highly detailed, covering world history, important events timeline, factions, mythology, technology level, and political systems. Never write generic filler.")
    summary: str = Field(..., description="Narrative Synopsis (1000+ words). Comprehensive synopsis detailing the beginning, middle, ending, plot twists, and character motivations.")
    acts: list[str] = Field(
        default_factory=list,
        description="Ordered list of major story acts/chapters. For each act, write concrete objectives, locations, key events, cutscenes, boss encounters, and dialogue highlights.",
    )
    themes: list[str] = Field(
        default_factory=list,
        description="Core narrative themes. Explain the theme's meaning, how gameplay supports the theme, and how the story supports it.",
    )
    chapter_breakdown: list[str] = Field(
        default_factory=list,
        description="Detailed chapter breakdown (Chapter 1, Chapter 2, etc.) specifying locations, objectives, enemies, and story beats for each.",
    )


# ─── Character Agent ───────────────────────────────────────────────────────
class CharacterOutput(BaseModel):
    """Single character definition produced by the Character Agent."""
    name: str = Field(..., description="Character name")
    role: str = Field(..., description="Role in the story (protagonist, antagonist, NPC, victim, side character, hidden character...)")
    backstory: str = Field(..., description="Character backstory, background details, relationships, and their character developmental arc")
    abilities: list[str] = Field(
        default_factory=list,
        description="List of abilities, strengths, or powers",
    )
    personality_traits: list[str] = Field(
        default_factory=list,
        description="Defining personality traits",
    )
    visual_description: str = Field(
        default="",
        description="Visual appearance, age, clothing/costume, and concept art prompts for image generation",
    )
    age: Optional[str] = Field(default=None, description="Age or age range")
    strengths: Optional[str] = Field(default=None, description="Key character strengths and assets")
    weaknesses: Optional[str] = Field(default=None, description="Key character weaknesses, flaws, or vulnerabilities")
    relationships: Optional[str] = Field(default=None, description="Detailed relationships and dynamics with other characters")
    character_arc: Optional[str] = Field(default=None, description="Detailed character developmental arc throughout the story")
    voice_style: Optional[str] = Field(default=None, description="Voice style, tone, speaking pace, and accents")
    gameplay_role: Optional[str] = Field(default=None, description="Role in the gameplay loop and player mechanics")
    concept_art_prompt: Optional[str] = Field(default=None, description="FLUX/SDXL-ready detailed prompt describing the character's visual design, lighting, and composition")


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
    description: str = Field(..., description="World Overview and environmental storytelling rules")
    regions: list[str] = Field(
        default_factory=list,
        description="Named regions or locations with map descriptions detailed enough for level design",
    )
    lore_elements: list[str] = Field(
        default_factory=list,
        description="Key lore elements, factions, political structures, or history points",
    )
    atmosphere: str = Field(
        default="",
        description="Mood, lighting, and atmospheric description",
    )
    buildings: list[str] = Field(default_factory=list, description="Key buildings, architecture types, and structures")
    points_of_interest: list[str] = Field(default_factory=list, description="Specific points of interest and landmarks within regions")
    interactive_objects: list[str] = Field(default_factory=list, description="Interactive items, props, chest locations, and mechanisms")
    environmental_storytelling: list[str] = Field(default_factory=list, description="Environmental storytelling clues and narrative details embedded in the world layout")
    resource_locations: list[str] = Field(default_factory=list, description="Locations of resources, items, ammo caches, or ingredients")
    puzzle_locations: list[str] = Field(default_factory=list, description="Locations of puzzles, locked gates, keys, and obstacle structures")
    safe_zones: list[str] = Field(default_factory=list, description="Safe zones, sanctuaries, and trader camps")
    danger_zones: list[str] = Field(default_factory=list, description="Danger zones, high-threat areas, and enemy territories")


# ─── Gameplay Agent ────────────────────────────────────────────────────────
class GameplayOutput(BaseModel):
    """Gameplay systems output produced by the Gameplay Agent."""
    core_loop: str = Field(..., description="Description of the core gameplay loop (e.g., Explore -> Solve Puzzle -> Avoid Enemy -> Gather Resources -> Escape)")
    mechanics: list[str] = Field(
        default_factory=list,
        description="List of gameplay mechanics and mechanics rules",
    )
    progression_system: str = Field(
        default="",
        description="Progression / leveling system design",
    )
    difficulty_curve: str = Field(
        default="",
        description="Difficulty scaling approach",
    )
    controls: Optional[str] = Field(default=None, description="Controls mapping and input scheme")
    win_conditions: Optional[str] = Field(default=None, description="Win conditions and victory criteria")
    lose_conditions: Optional[str] = Field(default=None, description="Lose conditions and defeat triggers")
    save_system: Optional[str] = Field(default=None, description="Save system and checkpoint mechanics")
    inventory_system: Optional[str] = Field(default=None, description="Inventory system, grid details, and item management rules")
    enemy_ai_behavior: Optional[str] = Field(default=None, description="Enemy AI behavior, search states, patrolling pathing rules")
    chase_system: Optional[str] = Field(default=None, description="For horror: Chase system, threat levels, and music cues")
    jumpscare_system: Optional[str] = Field(default=None, description="For horror: Jumpscare triggers, visual flashes, and audio stinger rules")
    hiding_system: Optional[str] = Field(default=None, description="For horror: Hiding system, locker/under-bed interactions, breath holding mechanics")
    noise_detection_system: Optional[str] = Field(default=None, description="For horror: Noise detection system, sound propagation, distraction throws")


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
    visual_style_guide: Optional[str] = Field(default=None, description="Detailed visual style guide and references")
    character_concept_prompts: list[str] = Field(default_factory=list, description="FLUX/SDXL prompts for main characters")
    environment_prompts: list[str] = Field(default_factory=list, description="FLUX/SDXL prompts for levels, rooms, and vistas")
    prop_prompts: list[str] = Field(default_factory=list, description="FLUX/SDXL prompts for items, weapons, keys, and interactive objects")
    ui_design_prompts: list[str] = Field(default_factory=list, description="FLUX/SDXL prompts for health bar, HUD, inventory screens")
    lighting_prompts: list[str] = Field(default_factory=list, description="FLUX/SDXL prompts representing exact lighting setups")
    color_palette: Optional[str] = Field(default=None, description="Specific hexadecimal color palette codes and accent definitions")
    mood_boards: list[str] = Field(default_factory=list, description="Mood boards and aesthetic references detailed enough for image models")


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
    gameplay_risks: list[str] = Field(default_factory=list, description="Gameplay risks with severity scores")
    story_risks: list[str] = Field(default_factory=list, description="Story/narrative risks with severity scores")
    scope_risks: list[str] = Field(default_factory=list, description="Scope creep and planning timeline risks with severity scores")
    technical_risks: list[str] = Field(default_factory=list, description="Performance and target engine risks with severity scores")
    balance_issues: list[str] = Field(default_factory=list, description="System balance issues with severity scores")
    ux_issues: list[str] = Field(default_factory=list, description="User experience and friction issues with severity scores")


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
    tdd: Optional[str] = Field(default=None, description="Technical Design Document (TDD)")
    asset_list: list[str] = Field(default_factory=list, description="Detailed 2D/3D audio and code asset inventory list")
    production_plan: Optional[str] = Field(default=None, description="Production roadmap and milestones plan")
    sprint_plan: Optional[str] = Field(default=None, description="Sprint schedules and task backlog mappings")


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


# ─── Timeline Agent ──────────────────────────────────────────────────────────
class TimelineMilestone(BaseModel):
    week: str = Field(..., description="E.g., Week 1")
    title: str = Field(..., description="E.g., Story & Characters")
    details: list[str] = Field(default_factory=list, description="Milestone tasks/details")

class TimelineOutput(BaseModel):
    roadmap_weekly: list[TimelineMilestone] = Field(default_factory=list)
    roadmap_monthly: list[str] = Field(default_factory=list)


# ─── Feasibility Agent ───────────────────────────────────────────────────────
class FeasibilityOutput(BaseModel):
    success_probability: float = Field(..., description="Success probability percentage (e.g. 78.0)")
    estimated_completion_days: int = Field(..., description="Estimated completion days (e.g. 42)")
    required_team_size: int = Field(..., description="Estimated required team size")
    required_hours_per_day: float = Field(..., description="Required hours per day per person")
    risk_level: str = Field(..., description="Low, Medium, or High")


# ─── Risk Agent ──────────────────────────────────────────────────────────────
class RiskItem(BaseModel):
    category: str = Field(..., description="scope_creep, missing_assets, unrealistic_deadlines, budget_issues")
    description: str = Field(..., description="Details of the risk")
    severity: str = Field(..., description="Low, Medium, High, Critical")
    mitigation: str = Field(..., description="Mitigation suggestion")

class RiskOutput(BaseModel):
    risks: list[RiskItem] = Field(default_factory=list)


# ─── Project Planner Agent ───────────────────────────────────────────────────
class SprintPlan(BaseModel):
    sprint_name: str = Field(..., description="Sprint name, e.g., Sprint 1")
    goal: str = Field(..., description="Sprint goal")
    tasks: list[str] = Field(default_factory=list)

class KanbanTask(BaseModel):
    task_id: str
    title: str
    status: str = Field(default="Todo", description="Todo, InProgress, InQA, Done")
    assignee: str
    dependencies: list[str] = Field(default_factory=list)

class ProjectPlannerOutput(BaseModel):
    milestones: list[str] = Field(default_factory=list)
    sprints: list[SprintPlan] = Field(default_factory=list)
    kanban: list[KanbanTask] = Field(default_factory=list)
    dependency_graph: list[str] = Field(default_factory=list, description="Format: Task A -> Task B")


# ─── Analytics Agent ─────────────────────────────────────────────────────────
class AnalyticsOutput(BaseModel):
    token_usage: int = Field(default=0)
    api_cost: float = Field(default=0.0)
    agent_runtime_seconds: dict[str, float] = Field(default_factory=dict)
    productivity_score: float = Field(default=0.0, description="Productivity score out of 100")


# ─── Export Agent ────────────────────────────────────────────────────────────
class ExportOutput(BaseModel):
    markdown_reports: dict[str, str] = Field(default_factory=dict, description="Key is report name, value is MD text")
    json_export: str = Field(..., description="Master JSON string export")
    pdf_exports: dict[str, str] = Field(default_factory=dict, description="Base64 mock PDF files or content summaries")
    zip_archive_path: str = Field(default="", description="Path to project export ZIP")


class ProjectOutput(BaseModel):
    """Aggregated output of all agents for a complete project."""
    project_id: str = Field(..., description="Unique project identifier")
    title: str = Field(default="Untitled Project", description="Project title")
    story: Optional[StoryOutput] = None
    characters: list[CharacterOutput] = Field(default_factory=list)
    world: Optional[WorldOutput] = None
    gameplay: Optional[GameplayOutput] = None
    art: Optional[Union[ArtOutput, dict]] = None
    art_gallery: list[str] = Field(default_factory=list)
    qa: Optional[QAOutput] = None
    review: Optional[ReviewerOutput] = None
    documentation: Optional[DocumentationOutput] = None
    timeline: Optional[TimelineOutput] = None
    feasibility: Optional[FeasibilityOutput] = None
    risk: Optional[RiskOutput] = None
    planner: Optional[ProjectPlannerOutput] = None
    analytics: Optional[AnalyticsOutput] = None
    exports: Optional[ExportOutput] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─── Atlas Agent ─────────────────────────────────────────────────────────────
class AtlasPhase(BaseModel):
    """A single roadmap phase containing a name and a list of tasks."""
    name: str = Field(..., description="Phase name (e.g., Phase 1: Project Setup)")
    tasks: list[str] = Field(..., description="Tasks associated with this phase")
    objectives: list[str] = Field(default_factory=list)
    hours: float = Field(default=0, ge=0)
    deliverables: list[str] = Field(default_factory=list)
    milestones: list[str] = Field(default_factory=list)
    period: int = 0
    period_unit: str = ""
    phase: str = ""


class AtlasDetailedTask(BaseModel):
    id: str
    title: str = ""
    name: str
    hours: float = Field(..., gt=0)
    priority: str
    dependencies: list[str] = Field(default_factory=list)
    dependency: str = ""
    status: str = "Not Started"
    owner: str
    critical_path: bool = False


class AtlasRisk(BaseModel):
    id: str
    title: str
    blocked_task: str
    blocked_by: list[str] = Field(default_factory=list)
    risk: str
    impact: str
    probability: str
    mitigation: str
    category: str = ""
    description: str = ""
    severity: str = ""


class AtlasArtConcept(BaseModel):
    title: str
    prompt: str
    category: str
    purpose: str


class AtlasSimulation(BaseModel):
    available_hours: float = Field(..., ge=0)
    planned_hours: float = Field(..., ge=0)
    status: str
    explanation: str
    completion_probability: float = Field(default=0, ge=0, le=100)


class AtlasTaskBreakdown(BaseModel):
    """Production tasks broken down by priority/timeline status."""
    critical_tasks: list[str] = Field(..., description="High-priority critical path tasks")
    optional_tasks: list[str] = Field(..., description="Optional features or nice-to-haves")
    future_expansion: list[str] = Field(..., description="Long-term expansion or DLC ideas")
    detailed_tasks: list[AtlasDetailedTask] = Field(default_factory=list)
    tools_guide: Optional[dict[str, str]] = Field(
        default=None,
        description="A dictionary mapping each tool/technology (from the user's tools list) to a detailed guide on how to integrate and use it in this project."
    )


class AtlasOutput(BaseModel):
    """Structured production blueprint produced by the Atlas Agent."""
    project_id: str = Field(..., description="Associated project identifier")
    roadmap: list[AtlasPhase] = Field(..., description="Ordered milestones of the roadmap")
    project_structure: list[str] = Field(..., description="List of folders and files relative to project root")
    production_flow_map: list[str] = Field(..., description="Ordered steps of production flow workflow")
    dependency_map: list[str] = Field(..., description="Code/asset dependency mapping")
    task_breakdown: AtlasTaskBreakdown = Field(..., description="Categorized tasks breakdown")
    risks: list[AtlasRisk] = Field(default_factory=list)
    art_gallery: list[AtlasArtConcept] = Field(default_factory=list)
    roadmap_simulator: Optional[AtlasSimulation] = None

