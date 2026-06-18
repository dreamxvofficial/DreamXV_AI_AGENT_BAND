"""
DreamXV AI Studio — Unified LLM Service
========================================
Facade that routes LLM requests through Featherless AI (primary)
with automatic fallback to AIMLAPI. Users never see provider selection.
"""

from __future__ import annotations

import inspect
import asyncio
from typing import Optional, Type, TypeVar, Union, List, get_origin, get_args

from pydantic import BaseModel

from backend.services.featherless_service import FeatherlessService
from backend.services.aiml_service import AIMLService
from backend.utils.logger import get_logger

logger = get_logger("llm")
T = TypeVar("T", bound=BaseModel)


def generate_mock_data_for_model(model_class: Type[T], user_prompt: str = "") -> T:
    """Dynamically generate high-fidelity mock data matching the schema of any agent output model."""
    prompt_lower = user_prompt.lower()
    is_zombie = "zombie" in prompt_lower or "rpg" in prompt_lower or "undead" in prompt_lower

    model_name = model_class.__name__

    if model_name == "ChiefTaskBreakdown":
        if is_zombie:
            return model_class(
                story_directive="Create a dark, post-apocalyptic narrative set in a city overrun by zombies. Focus on survival, loss, and moral dilemmas.",
                character_directive="Design a roster of survivors: a battle-hardened scavenger guide, a cynical doctor harboring a dark secret, and a young scavenger runner.",
                world_directive="Build a dark, grid-aligned, atmospheric setting: abandoned metro lines, dilapidated skyscrapers, and fortified survivor camps.",
                gameplay_directive="Design a classic RPG turn-based or real-time tactical combat loop, inventory grid-management, and scarcity mechanics for ammo/food.",
                art_directive="Generate prompts for realistic de-saturated green/gray environments, character closeups with grime and flashlight beams.",
                qa_directive="Ensure consistent tone between narrative descriptions of zombie threat and high consistency of survival mechanics.",
                genre="Survival Zombie RPG",
                tone="Grim, suspenseful, gritty",
            )
        else:
            return model_class(
                story_directive=f"Develop a creative narrative campaign based on: '{user_prompt}'.",
                character_directive="Create a main protagonist, an antagonist, and a supporting ally character fit for the narrative.",
                world_directive="Design distinct regions, history, and atmospheric setting that supports the core themes.",
                gameplay_directive="Design a compelling core gameplay loop, mechanic checklist, and progression/leveling systems.",
                art_directive="Generate visual prompts matching the thematic art style.",
                qa_directive="Perform consistency checks across lore, gameplay, and art style.",
                genre="Adventure / Strategy",
                tone="Immersive, mysterious",
            )

    elif model_name == "StoryOutput":
        if is_zombie:
            return model_class(
                title="Undead Rising: Survival RPG",
                lore="In 2032, a mutated virus known as Necro-7 decimated 90% of the population. The survivors live in heavily fortified enclaves, defending against hordes of aggressive, sound-sensitive infected.",
                summary="A dark narrative tracking a small squad of scavengers trying to retrieve a rumored cure from a high-security research facility deep inside the infected zone.",
                acts=[
                    "Act I: The Outpost Siege — Defend the enclave wall from a sudden nighttime surge.",
                    "Act II: The Journey North — Traverse the abandoned highways and overgrown suburbs.",
                    "Act III: Inside the Lab — Infiltrate the mainframe and retrieve the Necro-7 cure sample."
                ],
                themes=["Survival at all costs", "Moral compromise in crisis", "Hope vs. Despair"],
            )
        else:
            return model_class(
                title=f"Project: {user_prompt.title() if user_prompt else 'Untitled Project'}",
                lore=f"An epic saga set in a world shaped by the themes of '{user_prompt or 'exploration'}'. A long history of conflict and discovery has led to this moment.",
                summary=f"A deep narrative journey exploring the conflict and characters inspired by '{user_prompt or 'a mystery'}'.",
                acts=[
                    "Act I: The Call to Adventure — The protagonist discovers their purpose.",
                    "Act II: The Trials — Confronting challenging obstacles and uncovering secrets.",
                    "Act III: The Resolution — A climactic showdown and the shaping of a new era."
                ],
                themes=["Discovery", "Legacy", "Power and responsibility"],
            )

    elif model_name == "CharacterRoster":
        if is_zombie:
            from backend.models.output_models import CharacterOutput
            return model_class(
                characters=[
                    CharacterOutput(
                        name="Jack 'Scavenger' Morrison",
                        role="Protagonist",
                        backstory="A former survival training officer who lost his family during the initial outbreak. He now guides rookie scavengers through the dead zones.",
                        abilities=["Tactical Sense", "Silent Takedowns", "Improvised First Aid"],
                        personality_traits=["Quiet", "Pragmatic", "Protective"],
                        visual_description="Mid-40s, scarred face, wearing a worn green military jacket, leather backpack, and carrying a silenced pistol."
                    ),
                    CharacterOutput(
                        name="Dr. Evelyn Vance",
                        role="Supporting Ally",
                        backstory="A virologist from the original CDC lab who fled into the wasteland. She carries the key research data to create a vaccine.",
                        abilities=["Field Medicine", "Chemical Analysis", "Zombie Behavior Knowledge"],
                        personality_traits=["Analytical", "Distant", "Determined"],
                        visual_description="Late 30s, short dark hair, wearing cracked glasses, a dusty lab coat over jeans, holding a tablet."
                    )
                ]
            )
        else:
            from backend.models.output_models import CharacterOutput
            return model_class(
                characters=[
                    CharacterOutput(
                        name="Aiden Storm",
                        role="Protagonist",
                        backstory="An orphan raised by an ancient order who must now embark on the quest of their lifetime.",
                        abilities=["Elemental Manipulation", "Strategic Combat", "Agility"],
                        personality_traits=["Brave", "Curious", "Loyal"],
                        visual_description="Young adult with bright blue eyes, wearing light-weight blue armor and carrying a glowing relic."
                    ),
                    CharacterOutput(
                        name="General Vex",
                        role="Antagonist",
                        backstory="A ruthless commander who seeks control over the entire region's resources.",
                        abilities=["Shadow Magic", "Heavy Strike", "Fear Induction"],
                        personality_traits=["Cruel", "Cunning", "Ambitious"],
                        visual_description="Tall, clad in obsidian armor with a red velvet cape, holding a massive dark sword."
                    )
                ]
            )

    elif model_name == "CharacterOutput":
        if is_zombie:
            return model_class(
                name="Jack Morrison",
                role="Protagonist",
                backstory="A battle-hardened survival guide who knows every dead end in the city ruins.",
                abilities=["Scouting", "Jury-rigging", "Precision Shooting"],
                personality_traits=["Pragmatic", "Guarded", "Resilient"],
                visual_description="Rugged survivor, mid-40s, green field coat, military webbing."
            )
        else:
            return model_class(
                name="Aiden Storm",
                role="Protagonist",
                backstory="A traveler searching for the lost relics of their ancestors.",
                abilities=["Tracking", "Relic Channeling", "Parkour"],
                personality_traits=["Determined", "Resourceful", "Adventurous"],
                visual_description="Wears a traveler cloak, carrying a glowing energy dagger."
            )

    elif model_name == "WorldOutput":
        if is_zombie:
            return model_class(
                name="New Horizon & The Dead Zones",
                description="The remnants of a sprawling coastal metropolis, now overgrown and split into safe enclaves and infected ruins.",
                regions=["The Enclave Wall", "The Sunken Metro", "The Overgrown High-Rises"],
                lore_elements=["The Collapse of 2032", "The Sentinel Militia Faction", "The Nest Infections"],
                atmosphere="Grim, dark, tense, with high contrast shadows and eerie silence broken only by growls.",
            )
        else:
            return model_class(
                name="The Realm of Aethelgard",
                description="A magical, floating landmass bound together by ancient crystals and diverse ecosystems.",
                regions=["The Whispering Forests", "The Sky-Shattered Peaks", "The Crystal Valley"],
                lore_elements=["The Great Cataclysm", "The Crystal Keepers Faction", "Ancient Runestones"],
                atmosphere="Ethereal, majestic, slightly melancholic, filled with floating light particles and ruins.",
            )

    elif model_name == "GameplayOutput":
        if is_zombie:
            return model_class(
                core_loop="Scavenge resources during the day, fortify shelter, survive wave attacks at night, manage inventory weight, and level up tactical survival skills.",
                mechanics=["Grid Inventory Management", "Noise Generation System", "Turn-Based Tactical Combat", "Defensive Crafting"],
                progression_system="Earn XP from survival tasks to spend in Scavenging, Combat, or Crafting trees.",
                difficulty_curve="Starts simple with lone slow zombies, then scales up with armored mutants and toxic bosses over the surviving weeks.",
            )
        else:
            return model_class(
                core_loop="Explore ruins, collect magic seeds, solve environmental puzzles, engage in quick action-combat, and upgrade traversal gear.",
                mechanics=["Relic Traversal Mechanics", "Elemental Combat Reactions", "Environmental Puzzle Solving"],
                progression_system="Collect relic pieces to increase health and unlock new abilities on the skill board.",
                difficulty_curve="Gradually introduces more complex puzzles and enemies with multiple elemental immunities.",
            )

    elif model_name == "ArtOutput":
        if is_zombie:
            return model_class(
                prompts=[
                    "Gritty concept art of a ruined city street at dusk, moss covering abandoned cars, de-saturated colors.",
                    "A survivor in a green field coat looking out from a dilapidated building window, high contrast warm lighting.",
                    "A dark, flooded metro station hallway illuminated only by a single flashlight beam cutting through fog."
                ],
                image_paths=[],
                style_guide="Realistic gritty survival. Heavy use of dark shadows, muted greens and grays, high contrast warm light highlights (fire, flashlights).",
            )
        else:
            return model_class(
                prompts=[
                    "Lush forest with massive floating glowing crystals, rich blue and purple night sky.",
                    "A majestic stone keep built on a floating mountain edge, sunrise warm lighting.",
                    "Concept art of a glowing crystal altar inside an ancient cavern, warm light particles."
                ],
                image_paths=[],
                style_guide="Cinematic fantasy style. Vibrant color grading (blues, golds, teals), soft lighting, magical glows and particles.",
            )

    elif model_name == "QAOutput":
        if is_zombie:
            return model_class(
                consistency_score=9.5,
                issues=[],
                suggestions=["Add more character dialogue referencing the shortage of bullets to reinforce the scavenging loop."],
                overall_assessment="Excellent alignment between the survival storyline and the grid inventory/scarcity mechanics. The dark visual atmosphere perfectly matches the grim narrative tone.",
            )
        else:
            return model_class(
                consistency_score=9.2,
                issues=["Ensure the floating mountain lore links back to the elemental traversal mechanics in gameplay."],
                suggestions=["Consider adding a region specific gameplay mechanic for the Sky-Shattered Peaks."],
                overall_assessment="Highly consistent fantasy theme. The lore elements tie nicely into the exploration loop, and the visual guide supports the overall mood.",
            )

    elif model_name == "ReviewerOutput":
        from backend.models.output_models import ReviewIssue
        if is_zombie:
            return model_class(
                consistency_score=9.0,
                issues=[
                    ReviewIssue(
                        category="naming",
                        description="Jack 'Scavenger' Morrison is referred to as 'Jack Morrison' in the story acts but 'Jack Scavenger Morrison' in the character roster.",
                        severity="warning",
                        suggested_fix="Standardize to 'Jack Morrison' with 'Scavenger' as a nickname/callsign.",
                        references=["Story Agent: Act I", "Character Agent: Protagonist"],
                    ),
                    ReviewIssue(
                        category="world",
                        description="The Sunken Metro is listed as a world region but not referenced in any story act.",
                        severity="info",
                        suggested_fix="Add a brief reference to the Sunken Metro in Act II's journey sequence.",
                        references=["World Agent: regions", "Story Agent: acts"],
                    ),
                ],
                summary="Strong overall consistency. Minor naming standardization needed for the protagonist's title. World regions are well-defined but one location is underutilized in the narrative.",
            )
        else:
            return model_class(
                consistency_score=9.3,
                issues=[
                    ReviewIssue(
                        category="character",
                        description="General Vex is described as using 'Shadow Magic' but the world lore does not establish a shadow magic system.",
                        severity="warning",
                        suggested_fix="Add shadow magic as a forbidden art in the world lore elements.",
                        references=["Character Agent: General Vex", "World Agent: lore_elements"],
                    ),
                ],
                summary="Highly consistent project. The narrative, world, and gameplay systems align well. One minor lore gap identified regarding the antagonist's abilities.",
            )

    elif model_name == "ReviewIssue":
        return model_class(
            category="general",
            description="Minor inconsistency detected in cross-references.",
            severity="info",
            suggested_fix="Review and align the referenced elements.",
            references=["Agent A", "Agent B"],
        )

    elif model_name == "DocumentationOutput":
        title = user_prompt.title() if user_prompt else "Untitled Project"
        if is_zombie:
            return model_class(
                readme=f"# Undead Rising: Survival RPG\n\n> A gritty post-apocalyptic survival RPG set in a world overrun by the Necro-7 virus.\n\n## Overview\nUndead Rising is a turn-based tactical survival RPG where players guide a squad of scavengers through zombie-infested ruins in search of a cure.\n\n## Key Features\n- Deep narrative with moral choices\n- Grid-based inventory management\n- Tactical turn-based combat\n- Dynamic day/night survival cycle\n\n## Tech Stack\n- AI-Generated Design by DreamXV AI Studio\n- Multi-Agent Band Collaboration\n\n---\n*Built with DreamXV AI Studio — Born at 15. Built for Infinity.*",
                gdd="# Game Design Document: Undead Rising\n\n## Vision Statement\nA survival RPG that blends tactical combat with resource scarcity, set in a hauntingly atmospheric post-apocalyptic world.\n\n## Target Audience\nCore gamers aged 16-35 who enjoy survival horror and tactical RPGs.\n\n## Genre\nSurvival Horror RPG with Turn-Based Tactical Combat\n\n## Core Gameplay Loop\nScavenge → Fortify → Survive → Progress\n\n## Narrative Design\nThree-act structure following a squad's journey to find the Necro-7 cure.\n\n## Art Direction\nGritty, desaturated palette with high-contrast lighting and atmospheric fog.",
                feature_list=["Turn-based tactical combat", "Grid inventory system", "Noise-based stealth mechanics", "Day/night survival cycle", "Defensive crafting", "Character skill trees", "Multiple story endings"],
                core_mechanics=["Grid Inventory Management with weight limits", "Noise Generation System affecting zombie awareness", "Turn-Based Tactical Combat with cover mechanics", "Defensive Crafting for shelter fortification"],
                monetization=["Premium Edition with exclusive survivor skins", "Story DLC expansion packs", "Cosmetic weapon camos", "Soundtrack and artbook bundle"],
                future_expansion=["DLC: The Northern Frontier — new frozen biome", "Co-op multiplayer survival mode", "Community map editor", "Seasonal challenge events"],
                technical_summary="AI-driven game design using DreamXV multi-agent pipeline. Story, characters, world, gameplay, art, and QA generated collaboratively by 9 specialized AI agents powered by Featherless AI with AIMLAPI fallback.",
                elevator_pitch="Undead Rising is a tactical survival RPG where every bullet counts and every choice matters. Guide your squad through a zombie apocalypse, scavenge for the cure, and face the hardest question: who do you save when you can't save everyone?",
            )
        else:
            return model_class(
                readme=f"# {title}\n\n> An epic adventure crafted by AI agents.\n\n## Overview\n{title} is an immersive game experience generated by DreamXV AI Studio's multi-agent collaboration system.\n\n## Key Features\n- Rich narrative with multiple acts\n- Unique character roster\n- Expansive world design\n- Deep gameplay mechanics\n\n---\n*Built with DreamXV AI Studio — Born at 15. Built for Infinity.*",
                gdd=f"# Game Design Document: {title}\n\n## Vision Statement\nAn immersive game experience that combines rich storytelling with engaging gameplay mechanics.\n\n## Target Audience\nGamers who enjoy story-driven adventures with strategic depth.\n\n## Core Gameplay Loop\nExplore → Discover → Battle → Upgrade → Progress",
                feature_list=["Dynamic combat system", "Open world exploration", "Character progression", "Environmental puzzles", "Rich lore and backstory", "Multiple endings"],
                core_mechanics=["Elemental combat reactions", "Relic traversal system", "Environmental puzzle solving", "Skill board progression"],
                monetization=["Cosmetic character skins", "Story expansion packs", "Premium edition with soundtrack", "Seasonal battle passes"],
                future_expansion=["New regions and biomes", "Multiplayer arena mode", "Community content creation tools", "Annual story expansions"],
                technical_summary="AI-driven game design using DreamXV multi-agent pipeline with 9 specialized agents. Powered by Featherless AI (primary) with AIMLAPI fallback.",
                elevator_pitch=f"{title} is an AI-crafted adventure where every element — from story to gameplay — was designed by a collaborative team of intelligent agents. Experience a game that was dreamed into existence.",
            )

    elif model_name == "TimelineOutput":
        from backend.models.output_models import TimelineMilestone
        return model_class(
            roadmap_weekly=[
                TimelineMilestone(week="Week 1", title="Story & Characters", details=[
                    "Day 1: Outline core narrative and backstory (09:00-12:00: Setup base lore, 13:00-16:00: Character traits)",
                    "Day 2: Rigging and character prototyping (09:00-12:00: Setup meshes, 13:00-16:00: Skeleton binds)",
                    "Day 3: World structure configuration (09:00-12:00: Layout tiles, 13:00-16:00: Lighting nodes)"
                ]),
                TimelineMilestone(week="Week 2", title="Gameplay Prototype", details=[
                    "Day 1: Player controller scripting (09:00-12:00: Setup movement, 13:00-16:00: Input system)",
                    "Day 2: Physics validation and collisions (09:00-12:00: Gravity adjustments, 13:00-16:00: Boundaries testing)"
                ]),
                TimelineMilestone(week="Week 3", title="Art & Audio Production", details=[
                    "Day 1: Texture mapping and asset import (09:00-12:00: UV mapping, 13:00-16:00: Materials)",
                    "Day 2: Ambient audio configuration (09:00-12:00: Placing sources, 13:00-16:00: Trigger mixing)"
                ]),
                TimelineMilestone(week="Week 4", title="QA Audit & Package", details=[
                    "Day 1: Playtesting and bug sweep (09:00-12:00: Core spawn verification, 13:00-16:00: FPS profiling)",
                    "Day 2: Target platform compile (09:00-12:00: Setup flags, 13:00-16:00: Check release packages)"
                ])
            ],
            roadmap_monthly=[
                "Month 1: Technical Foundation & Alpha Sandbox",
                "Month 2: Core Gameplay Iteration & Visual Integration",
                "Month 3: Audio Design & Faction Systems",
                "Month 4: Final QA Audits & Multi-platform Export Packages"
            ]
        )

    elif model_name == "FeasibilityOutput":
        return model_class(
            success_probability=78.0,
            estimated_completion_days=42,
            required_team_size=3,
            required_hours_per_day=6.0,
            risk_level="Medium"
        )

    elif model_name == "RiskOutput":
        from backend.models.output_models import RiskItem
        return model_class(
            risks=[
                RiskItem(category="scope_creep", description="Adding too many biomes could cause delays", severity="Medium", mitigation="Focus on core MVP biomes first"),
                RiskItem(category="unrealistic_deadlines", description="42 days requires high commitment", severity="High", mitigation="Set up strict sprint goals")
            ]
        )

    elif model_name == "ProjectPlannerOutput":
        from backend.models.output_models import SprintPlan, KanbanTask
        return model_class(
            milestones=["Core Mechanics Prototype Complete", "Visual Art Style Finalized", "Playable Beta Release"],
            sprints=[
                SprintPlan(sprint_name="Sprint 1: Mechanics Setup", goal="Deliver working protagonist controls", tasks=["Set up gravity script", "Wire jump mechanic"]),
                SprintPlan(sprint_name="Sprint 2: Art Integration", goal="Implement environment tiles", tasks=["Design level ruins", "Place lighting nodes"])
            ],
            kanban=[
                KanbanTask(task_id="TSK-001", title="Define movement parameters", status="Done", assignee="Gameplay Engineer", dependencies=[]),
                KanbanTask(task_id="TSK-002", title="Draw ruined street concept", status="InProgress", assignee="Art Director", dependencies=[])
            ],
            dependency_graph=["Movement Script -> Level Geometry", "Character Sprites -> Animation Rig"]
        )

    elif model_name == "AnalyticsOutput":
        return model_class(
            token_usage=125000,
            api_cost=0.15,
            agent_runtime_seconds={
                "Chief Agent": 12.5,
                "Story Agent": 18.2,
                "Character Agent": 9.4,
                "World Agent": 15.1,
                "Gameplay Agent": 14.6,
                "Art Agent": 11.2,
                "QA Agent": 8.9,
                "Reviewer Agent": 10.5,
                "Documentation Agent": 13.8,
                "Timeline Agent": 11.5,
                "Risk Agent": 9.2,
                "Feasibility Agent": 7.4,
                "Project Planner Agent": 12.8,
                "Analytics Agent": 5.2,
                "Export Agent": 6.8
            },
            productivity_score=88.5
        )

    elif model_name == "ExportOutput":
        return model_class(
            markdown_reports={"Readme": "# Project Readme", "GDD": "# Game Design Document"},
            json_export='{"project_name": "Test project"}',
            pdf_exports={"ExecutiveSummary": "Mock PDF Summary base64 data"},
            zip_archive_path="public/exports/project_design_kit.zip"
        )

    elif model_name == "AtlasOutput":
        from backend.models.output_models import AtlasPhase, AtlasTaskBreakdown
        tools_line = user_prompt.lower()
        for line in user_prompt.splitlines():
            if "user specified tools & technologies:" in line.lower():
                tools_line = line.lower()
                break
        is_web = any(term in tools_line for term in ["react", "fastapi", "supabase", "django", "flask", "node", "html", "css", "web", "js", "ts", "javascript", "typescript"])
        
        tools_str = "React, FastAPI, Supabase" if is_web else "Unity 6, Blender, C#"
        
        import re
        tools_list = [t.strip() for t in re.split(r'[,;/]', tools_str) if t.strip()]
        guide = {}
        for tool in tools_list:
            lower_tool = tool.lower()
            if "react" in lower_tool:
                guide[tool] = "**React Frontend Integration:**\n1. **Boilerplate Setup:** Bootstrapped via Vite with React-Router.\n2. **Component Architecture:** Build responsive dashboard views.\n3. **API Hooks:** Encapsulate fetch requests inside custom state hooks."
            elif "fastapi" in lower_tool:
                guide[tool] = "**FastAPI Backend Architecture:**\n1. **App Routing:** Define modular APIRouters.\n2. **Pydantic Validation:** Formulate robust input/output schemas.\n3. **CORS:** Configure global middleware."
            elif "supabase" in lower_tool:
                guide[tool] = "**Supabase Database & Auth Service:**\n1. **Database Schema:** Create relational tables.\n2. **Auth Mechanisms:** Implement SignUp/LogIn flows.\n3. **RLS Policies:** Apply Row Level Security."
            elif "unity" in lower_tool:
                guide[tool] = "**Unity Configuration & Integration:**\n1. **Project Setup:** Initialize the project using URP.\n2. **Package Management:** Install Input System.\n3. **Scene Layout:** Configure the main camera."
            elif "blender" in lower_tool:
                guide[tool] = "**Blender Asset Creation & Export Pipeline:**\n1. **Modeling & Scale:** Design models with metric scale.\n2. **Export Settings:** Export assets to FBX.\n3. **Texturing:** Generate UV maps."
            else:
                guide[tool] = f"**{tool} Guide:**\n1. **Setup:** Configure tool environment.\n2. **Workflow:** Integrate with main project compile."

        if is_web:
            return model_class(
                project_id=user_prompt or "mock-project",
                roadmap=[
                    AtlasPhase(name="Month 1: Initial Architecture & Setup", tasks=[
                        "Week 1: Project Setup & Init",
                        "  • Day 1: Code repository initialization & workspace structure config",
                        "    - 09:00 - 12:00: Setup base folders and config files",
                        "    - 13:00 - 16:00: Add project boilerplate & readme documentation",
                        "  • Day 2: Basic database configuration and client initialization",
                        "    - 09:00 - 12:00: Configure database credentials & security protocols",
                        "    - 13:00 - 16:00: Test initial read/write database connections",
                        "  • Day 3: Pipeline verification & basic unit test setups",
                        "    - 09:00 - 12:00: Setup testing packages & mocks",
                        "    - 13:00 - 16:00: Run verify commands and check CI integration",
                        "Week 2: Core State Engine",
                        "  • Day 1: Design global state schema",
                        "    - 09:00 - 12:00: Map state transitions and events",
                        "    - 13:00 - 16:00: Code initial state reducer logic",
                        "  • Day 2: State synchronization layer",
                        "    - 09:00 - 12:00: Setup client-server messaging sockets",
                        "    - 13:00 - 16:00: Verify real-time message payloads"
                    ]),
                    AtlasPhase(name="Month 2: Database & Auth Setup", tasks=[
                        "Week 3: Database & Auth Integration",
                        "  • Day 1: Define Supabase/PostgreSQL schema",
                        "    - 09:00 - 12:00: Create tables for users, projects and tasks",
                        "    - 13:00 - 16:00: Verify foreign keys & trigger constraints",
                        "  • Day 2: Implement signup/login routes",
                        "    - 09:00 - 12:00: Build password hashing & JWT token generators",
                        "    - 13:00 - 16:00: Setup endpoint tests for authentication flow",
                        "  • Day 3: Frontend Auth Session Link",
                        "    - 09:00 - 12:00: Create client auth provider state",
                        "    - 13:00 - 16:00: Configure redirection guards for private routes"
                    ]),
                    AtlasPhase(name="Month 3: Core API Features", tasks=[
                        "Week 4: API Handlers & Dashboards",
                        "  • Day 1: Create endpoints for project storage",
                        "    - 09:00 - 12:00: Implement project list/GET and insert/POST routes",
                        "    - 13:00 - 16:00: Verify API validations for project schemas",
                        "  • Day 2: Build user dashboards",
                        "    - 09:00 - 12:00: Code frontend workspace navigation & tables",
                        "    - 13:00 - 16:00: Bind API fetching state hooks",
                        "  • Day 3: State integration tests",
                        "    - 09:00 - 12:00: Write integration tests for dashboard components",
                        "    - 13:00 - 16:00: Resolve any API response mapping issues"
                    ]),
                    AtlasPhase(name="Month 4: Polish & Deployment", tasks=[
                        "Week 5: QA, Styling & Production Launch",
                        "  • Day 1: Add error boundaries & responsive styling",
                        "    - 09:00 - 12:00: Test screen size responsiveness on mobile & desktop",
                        "    - 13:00 - 16:00: Add global try-catch handlers & toast notifications",
                        "  • Day 2: Deploy to Vercel/Netlify",
                        "    - 09:00 - 12:00: Configure build commands & production environment vars",
                        "    - 13:00 - 16:00: Verify live endpoints & perform final sanity tests"
                    ])
                ],
                project_structure=[
                    "frontend/",
                    "frontend/src/",
                    "frontend/src/components/",
                    "frontend/src/App.jsx",
                    "backend/",
                    "backend/api/",
                    "backend/main.py",
                    "database/",
                    "database/schema.sql",
                    "docs/",
                    "docs/Roadmap.md",
                    "README.md"
                ],
                production_flow_map=[
                    "Design UI Mockups",
                    "Create Database Schema",
                    "Build API Server",
                    "Connect React Frontend",
                    "Setup Authentication Flow",
                    "Deploy Application"
                ],
                dependency_map=[
                    "Database -> API Service -> Auth Middleware -> Frontend Component"
                ],
                task_breakdown=AtlasTaskBreakdown(
                    critical_tasks=["Setup Git repository", "Create responsive dashboard", "Write database models"],
                    optional_tasks=["Add light/dark mode theme", "Configure toast notifications"],
                    future_expansion=["Implement automated testing", "Integrate caching layers"],
                    tools_guide=guide
                )
            )
        else:
            return model_class(
                project_id=user_prompt or "mock-project",
                roadmap=[
                    AtlasPhase(name="Month 1: Initial Setup & Asset Design", tasks=[
                        "Week 1: Project Setup & Guidelines",
                        "  • Day 1: Code repository initialization & engine setup",
                        "    - 09:00 - 12:00: Create new Unity/Unreal project",
                        "    - 13:00 - 16:00: Configure folder structures & import settings",
                        "  • Day 2: Style guides & asset folders config",
                        "    - 09:00 - 12:00: Configure colors, lighting profiles, & render pipeline",
                        "    - 13:00 - 16:00: Verify asset pipelines for models & textures",
                        "Week 2: Core Movement Controllers",
                        "  • Day 1: Input handling setup",
                        "    - 09:00 - 12:00: Setup Input System bindings",
                        "    - 13:00 - 16:00: Code player movement & camera control scripts",
                        "  • Day 2: Physics validation",
                        "    - 09:00 - 12:00: Adjust collision volumes & character controller gravity",
                        "    - 13:00 - 16:00: Verify smooth movement over obstacles"
                    ]),
                    AtlasPhase(name="Month 2: Core Gameplay Mechanics", tasks=[
                        "Week 3: Spawning & Core Loops",
                        "  • Day 1: Enemy Spawning system",
                        "    - 09:00 - 12:00: Code enemy spawn points & wave logic",
                        "    - 13:00 - 16:00: Hook up wave progression settings",
                        "  • Day 2: Attack & damage systems",
                        "    - 09:00 - 12:00: Implement weapon firing & hit registration",
                        "    - 13:00 - 16:00: Code health tracking & damage calculations"
                    ]),
                    AtlasPhase(name="Month 3: Environment Design & Audio", tasks=[
                        "Week 4: Level Layout & Atmosphere",
                        "  • Day 1: Construct level segments",
                        "    - 09:00 - 12:00: Place terrain, walls, & structural elements",
                        "    - 13:00 - 16:00: Setup lighting maps & ambient environmental effects",
                        "  • Day 2: Sound layers config",
                        "    - 09:00 - 12:00: Place spatialized sound sources",
                        "    - 13:00 - 16:00: Configure ambient background music mixing trigger zones"
                    ]),
                    AtlasPhase(name="Month 4: Game Polish & Builds", tasks=[
                        "Week 5: Performance & Final Export",
                        "  • Day 1: Playtesting & debugging",
                        "    - 09:00 - 12:00: Conduct bug sweep on core spawning & gameplay mechanics",
                        "    - 13:00 - 16:00: Profile frames per second & memory allocations",
                        "  • Day 2: Generate release packages",
                        "    - 09:00 - 12:00: Configure target platform build settings",
                        "    - 13:00 - 16:00: Generate final executable packages & check logs"
                    ])
                ],
                project_structure=[
                    "Assets/",
                    "Assets/Scripts/",
                    "Assets/Prefabs/",
                    "Assets/Materials/",
                    "Assets/Animations/",
                    "Assets/Scenes/",
                    "Docs/",
                    "Docs/GDD.md",
                    "Docs/Roadmap.md",
                    "Docs/Tasks.md",
                    "README.md"
                ],
                production_flow_map=[
                    "Create Asset Designs",
                    "Rig & Animate Assets",
                    "Import to Engine",
                    "Attach Scripts & Physics",
                    "Configure Gameplay HUD",
                    "Export Distribution Package"
                ],
                dependency_map=[
                    "InputManager -> PlayerController -> CombatSystem -> GameHUD"
                ],
                task_breakdown=AtlasTaskBreakdown(
                    critical_tasks=["Map camera behaviors", "Code primary action/move behaviors", "Ensure stable launch build"],
                    optional_tasks=["Design simple settings panel", "Add ambient sound layers"],
                    future_expansion=["Create secondary levels", "Deploy multi-platform exports"],
                    tools_guide=guide
                )
            )

    # 2. Dynamic Fallback Builder if any other class is added later
    mock_values = {}
    for field_name, field_info in model_class.model_fields.items():
        field_type = field_info.annotation
        
        # Handle Optional/Union
        origin = get_origin(field_type)
        args = get_args(field_type)
        if origin is Union:
            non_none_types = [t for t in args if t is not type(None)]
            if non_none_types:
                field_type = non_none_types[0]
                origin = get_origin(field_type)
                args = get_args(field_type)
                
        # Check List
        if origin is list or origin is List:
            item_type = args[0] if args else str
            if inspect.isclass(item_type) and issubclass(item_type, BaseModel):
                mock_values[field_name] = [generate_mock_data_for_model(item_type, user_prompt) for _ in range(2)]
            else:
                mock_values[field_name] = [f"Mock list item {i + 1}" for i in range(3)]
        # Check nested BaseModel
        elif inspect.isclass(field_type) and issubclass(field_type, BaseModel):
            mock_values[field_name] = generate_mock_data_for_model(field_type, user_prompt)
        # Primitives
        elif field_type is str:
            mock_values[field_name] = f"Mock {field_name} text."
        elif field_type is float:
            mock_values[field_name] = 1.0
        elif field_type is int:
            mock_values[field_name] = 1
        elif field_type is bool:
            mock_values[field_name] = True
        else:
            mock_values[field_name] = None
            
    return model_class(**mock_values)


class LLMService:
    """
    Unified LLM interface with transparent failover.

    Primary:  Featherless AI
    Fallback: AIMLAPI
    """

    def __init__(self) -> None:
        self._primary = FeatherlessService()
        self._fallback = AIMLService()

    async def _try_primary(self, func, *args, **kwargs):
        delays = [1.0, 3.0, 5.0]
        for attempt in range(1, 4):
            try:
                logger.info(f"Featherless AI primary call: Attempt {attempt}")
                return await func(*args, **kwargs)
            except Exception as exc:
                logger.warning(
                    f"Featherless AI primary call failed on Attempt {attempt} "
                    f"({type(exc).__name__}: {exc})"
                )
                if attempt < 3:
                    delay = delays[attempt - 1]
                    logger.info(f"Waiting {delay} sec before next attempt...")
                    await asyncio.sleep(delay)
                else:
                    delay = delays[2]
                    logger.info(f"Attempt 3 failed. Waiting {delay} sec before fallback to AIMLAPI...")
                    await asyncio.sleep(delay)
                    raise exc

    async def generate(
        self,
        messages: list[dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text using the primary provider, falling back on failure.

        Args:
            messages: OpenAI-compatible chat messages.
            model: Override model (applies to whichever provider handles it).
            temperature: Override temperature.
            max_tokens: Override max tokens.

        Returns:
            Generated text from whichever provider succeeds.
        """
        try:
            result = await self._try_primary(
                self._primary.generate,
                messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return result
        except Exception as exc:
            logger.warning(
                f"Featherless AI failed after retries ({type(exc).__name__}: {exc}), "
                f"falling back to AIMLAPI"
            )
            try:
                result = await self._fallback.generate(
                    messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return result
            except Exception as fallback_exc:
                logger.error(
                    f"Both primary and fallback LLM services failed: {fallback_exc}."
                )
                raise fallback_exc

    async def generate_structured(
        self,
        messages: list[dict[str, str]],
        response_model: Type[T],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> T:
        """
        Generate structured Pydantic output with automatic failover.

        Args:
            messages: Chat messages.
            response_model: Target Pydantic model class.
            model: Override model identifier.
            temperature: Override temperature.

        Returns:
            Validated Pydantic model instance.
        """
        try:
            result = await self._try_primary(
                self._primary.generate_structured,
                messages,
                response_model,
                model=model,
                temperature=temperature,
            )
            return result
        except Exception as exc:
            logger.warning(
                f"Featherless AI structured generation failed after retries "
                f"({type(exc).__name__}: {exc}), falling back to AIMLAPI"
            )
            try:
                result = await self._fallback.generate_structured(
                    messages,
                    response_model,
                    model=model,
                    temperature=temperature,
                )
                return result
            except Exception as fallback_exc:
                logger.error(
                    f"Both primary and fallback LLM services failed: {fallback_exc}."
                )
                raise fallback_exc

    async def close(self) -> None:
        """Shut down both provider clients."""
        await self._primary.close()
        await self._fallback.close()

