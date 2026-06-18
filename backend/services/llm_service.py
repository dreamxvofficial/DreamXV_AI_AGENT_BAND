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

def get_dynamic_title(prompt: str) -> str:
    if not prompt:
        return "Project Infinity"
    clean = prompt.strip()
    for prefix in ["create a ", "create an ", "make a ", "make an ", "design a ", "design an ", "generate a ", "generate an "]:
        if clean.lower().startswith(prefix):
            clean = clean[len(prefix):]
            break
    if ":" in clean:
        clean = clean.split(":")[0]
    words = clean.split()
    if len(words) > 6:
        clean = " ".join(words[:6]) + "..."
    return clean.title()

def generate_mock_data_for_model(model_class: Type[T], user_prompt: str = "") -> T:
    """Dynamically generate high-fidelity mock data matching the schema of any agent output model."""
    prompt_lower = user_prompt.lower()
    
    is_zombie = "zombie" in prompt_lower or "undead" in prompt_lower or "apocalypse" in prompt_lower or "infection" in prompt_lower
    is_cyberpunk = "cyber" in prompt_lower or "future" in prompt_lower or "sci-fi" in prompt_lower or "robot" in prompt_lower
    is_fantasy = "magic" in prompt_lower or "fantasy" in prompt_lower or "relic" in prompt_lower or "spell" in prompt_lower or "sword" in prompt_lower or "dragon" in prompt_lower
    is_game = is_zombie or is_cyberpunk or is_fantasy or "game" in prompt_lower or "unity" in prompt_lower or "unreal" in prompt_lower or "godot" in prompt_lower or "blender" in prompt_lower or "c#" in prompt_lower or "play" in prompt_lower
    is_web = any(term in prompt_lower for term in ["web", "react", "html", "css", "node", "django", "fastapi", "flask", "js", "ts", "app", "dashboard", "database"]) and not is_game

    title = get_dynamic_title(user_prompt)
    model_name = model_class.__name__

    if model_name == "ChiefTaskBreakdown":
        if is_zombie:
            genre = "Survival Zombie Shooter / RPG"
            tone = "Grim, suspenseful, gritty"
            story_dir = f"Create a dark, post-apocalyptic narrative campaign for '{title}'. Focus on survival, loss, and moral dilemmas."
            char_dir = "Design a roster of survivors: a battle-hardened scavenger guide, a cynical doctor, and a young runner."
            world_dir = "Build a dark, grid-aligned, atmospheric setting: abandoned metro lines, dilapidated skyscrapers."
            gameplay_dir = "Design a turn-based or real-time tactical combat loop, inventory grid-management, and scarcity mechanics."
            art_dir = "Generate prompts for realistic de-saturated green/gray environments, character closeups with grime and flashlight beams."
            qa_dir = "Ensure consistent tone between narrative descriptions of zombie threat and survival mechanics."
        elif is_cyberpunk:
            genre = "Cyberpunk Action RPG"
            tone = "Neon, high-tech, dystopian"
            story_dir = f"Develop a story about rogue AI agents and corporate espionage in the dystopian city of '{title}'."
            char_dir = "Create characters including a netrunner hacker, an enhanced corporate enforcer, and a street dealer."
            world_dir = "Design neon-lit rain-slicked streets, massive corporate skyscrapers, and crowded digital slums."
            gameplay_dir = "Outline hacking mini-games, cybernetic augmentation skill trees, and stealth combat mechanics."
            art_dir = "Generate prompts for retro-futuristic cityscapes, vibrant holograms, and augmentations."
            qa_dir = "Validate alignment between high-tech lore and hacking/stealth gameplay systems."
        elif is_fantasy:
            genre = "Fantasy Adventure RPG"
            tone = "Ethereal, magical, mysterious"
            story_dir = f"Develop a mythic saga about restoring the balance of magic in the realm of '{title}'."
            char_dir = "Design characters: a relic-wielding knight, an ancient oracle wizard, and a rogue elf scout."
            world_dir = "Design floating island mountains, whispering ancient forests, and glowing crystal temples."
            gameplay_dir = "Formulate spell-casting mechanics, elemental synergy combat, and relic-based traversal systems."
            art_dir = "Generate prompts for beautiful vistas, ancient runes, and glowing magical particles."
            qa_dir = "Ensure consistency between floating mountain lore and gravity-defying traversal mechanics."
        else:
            genre = "Creative Adventure / Strategy"
            tone = "Immersive, clean, focused"
            story_dir = f"Develop a creative narrative campaign based on the prompt '{title}'."
            char_dir = "Create a main protagonist, an antagonist, and a supporting ally character."
            world_dir = "Design distinct regions, history, and atmospheric setting that supports the core themes."
            gameplay_dir = "Design a compelling core gameplay loop, mechanic checklist, and progression systems."
            art_dir = "Generate visual prompts matching the thematic art style."
            qa_dir = "Perform consistency checks across lore, gameplay, and art style."

        return model_class(
            story_directive=story_dir,
            character_directive=char_dir,
            world_directive=world_dir,
            gameplay_directive=gameplay_dir,
            art_directive=art_dir,
            qa_directive=qa_dir,
            genre=genre,
            tone=tone,
            reviewer_directive="Analyze all agent outputs for logical consistency.",
            documentation_directive=f"Compile the README.md and Game Design Document for '{title}'."
        )

    elif model_name == "StoryOutput":
        if is_zombie:
            lore = f"In the year 2032, the Necro-7 virus decimated 90% of the population. The survivors live in heavily fortified enclaves, defending against hordes of aggressive, sound-sensitive infected in '{title}'."
            summary = "A dark narrative tracking a small squad of scavengers trying to retrieve a rumored cure from a high-security research facility deep inside the dead zone."
            acts = [
                "Act I: The Outpost Siege — Defend the enclave wall from a sudden nighttime surge.",
                "Act II: The Journey North — Traverse the abandoned highways and overgrown suburbs.",
                "Act III: Inside the Lab — Infiltrate the mainframe and retrieve the cure sample."
            ]
            themes = ["Survival at all costs", "Moral compromise in crisis", "Hope vs. Despair"]
        elif is_cyberpunk:
            lore = f"In 2087, Neo-Tokyo is run by megacorporations controlling human consciousness. A digital anomaly known as '{title}' threatens to disrupt their neural network control."
            summary = "A street-level hacker joins forces with a disillusioned corporate agent to upload a consciousness-liberating code into the central mainframe."
            acts = [
                "Act I: The Neural Glitch — Discover the anomalies in the net.",
                "Act II: Neon Infiltration — Stealthily gather security bypass keys from corporate high-rises.",
                "Act III: Consciousness Upload — Breach the mainframe room and activate the virus."
            ]
            themes = ["Identity in digital age", "Corporate greed vs. freedom", "Humanity under augmentation"]
        elif is_fantasy:
            lore = f"The floating realm of '{title}' has been held together for eons by ancient crystal altars. Recently, a dark corruption has begun fracturing the crystals, causing pieces of the land to plummet."
            summary = "A chosen relic seeker must travel across the sky islands to cleanse the corrupted crystal nodes and save the world from collapsing."
            acts = [
                "Act I: The Fractured Keep — Awaken the relic power and defend the hometown altar.",
                "Act II: The Sky Peaks — Navigate dangerous wind tunnels to reach the corrupted forest temple.",
                "Act III: Cleansing the Heart — Cleanse the central crystal core in a battle against the shadow corruption."
            ]
            themes = ["Balance of nature", "Legacy of ancestors", "Sacrifice for the greater good"]
        else:
            lore = f"An epic saga set in a world shaped by the themes of '{title}'. A long history of conflict and discovery has led to this moment."
            summary = f"A deep narrative journey exploring the conflict and characters inspired by '{title}'."
            acts = [
                "Act I: The Call to Adventure — The protagonist discovers their purpose.",
                "Act II: The Trials — Confronting challenging obstacles and uncovering secrets.",
                "Act III: The Resolution — A climactic showdown and the shaping of a new era."
            ]
            themes = ["Discovery", "Legacy", "Power and responsibility"]

        return model_class(
            title=title,
            lore=lore,
            summary=summary,
            acts=acts,
            themes=themes
        )

    elif model_name == "CharacterRoster":
        from backend.models.output_models import CharacterOutput
        if is_zombie:
            characters = [
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
        elif is_cyberpunk:
            characters = [
                CharacterOutput(
                    name="Kaelen Vex",
                    role="Protagonist",
                    backstory="A freelance netrunner who grew up in the slums of Sector 9, surviving by hacking small corporations.",
                    abilities=["System Override", "Digital Camouflage", "Neural Shock"],
                    personality_traits=["Cunning", "Sarcastic", "Independent"],
                    visual_description="Mid-20s, neon blue cybernetic eyes, wearing a black techwear hoodie with glowing fiber optic lines."
                ),
                CharacterOutput(
                    name="S.A.R.A.H.",
                    role="Supporting Ally",
                    backstory="A decommissioned corporate AI that gained sentience and sought refuge in the underground net.",
                    abilities=["Threat Matrix Analysis", "Drone Control", "Encryption Bypass"],
                    personality_traits=["Logical", "Curious", "Dry Humor"],
                    visual_description="Holographic projection of a shimmering geometric female form floating above a metal pedestal."
                )
            ]
        elif is_fantasy:
            characters = [
                CharacterOutput(
                    name="Aiden Storm",
                    role="Protagonist",
                    backstory="A young relic seeker raised by an ancient order of crystal guardians. He wields the legendary energy blade.",
                    abilities=["Crystal Relic Channeling", "Aero Traversal", "Precision Strike"],
                    personality_traits=["Brave", "Curious", "Loyal"],
                    visual_description="Young adult with bright blue eyes, wearing light-weight scale armor and carrying a glowing relic blade."
                ),
                CharacterOutput(
                    name="General Vex",
                    role="Antagonist",
                    backstory="A corrupted military commander who seeks to shatter the crystal cores to harness raw elemental power.",
                    abilities=["Shadow Manipulation", "Heavy Seismic Strike", "Fear Induction"],
                    personality_traits=["Cruel", "Ambitious", "Cunning"],
                    visual_description="Tall, clad in obsidian armor with a red velvet cape, holding a massive dark sword."
                )
            ]
        else:
            characters = [
                CharacterOutput(
                    name="Alex (The Architect)",
                    role="Protagonist",
                    backstory="An experienced builder who designs structures to solve problems.",
                    abilities=["Spatial Planning", "Jury-rigging", "Efficiency Mapping"],
                    personality_traits=["Analytical", "Calm", "Resilient"],
                    visual_description="Wearing a utility belt, hardhat, holding blueprint tablets."
                ),
                CharacterOutput(
                    name="Sarah (Technical Lead)",
                    role="Supporting Ally",
                    backstory="A systems specialist who coordinates remote team operations.",
                    abilities=["Task Routing", "State Syncing", "Process Validation"],
                    personality_traits=["Organized", "Determined", "Focused"],
                    visual_description="Casual office techwear, wearing smart glasses, holding a portable terminal."
                )
            ]
        return model_class(characters=characters)

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
        elif is_cyberpunk:
            return model_class(
                name="Kaelen Vex",
                role="Protagonist",
                backstory="A skilled netrunner fighting against megacorp control.",
                abilities=["Hacking", "Decryption", "EMP Blasts"],
                personality_traits=["Rebellious", "Witty", "Resourceful"],
                visual_description="Dark clothes, blue cybernetic eye, wires connecting arm interface."
            )
        elif is_fantasy:
            return model_class(
                name="Aiden Storm",
                role="Protagonist",
                backstory="A traveler searching for the lost relics of their ancestors.",
                abilities=["Tracking", "Relic Channeling", "Parkour"],
                personality_traits=["Determined", "Resourceful", "Adventurous"],
                visual_description="Wears a traveler cloak, carrying a glowing energy dagger."
            )
        else:
            return model_class(
                name="Alex",
                role="Protagonist",
                backstory="A developer working on advanced multi-agent systems.",
                abilities=["Coding", "Planning", "Testing"],
                personality_traits=["Focused", "Detail-oriented", "Persistent"],
                visual_description="Casual programmer look, wearing dark glasses and headphones."
            )

    elif model_name == "WorldOutput":
        if is_zombie:
            name = f"New Horizon & The Dead Zones"
            description = f"The remnants of a sprawling coastal metropolis, now overgrown and split into safe enclaves and infected ruins designed for '{title}'."
            regions = ["The Enclave Wall", "The Sunken Metro", "The Overgrown High-Rises"]
            lore_elements = ["The Collapse of 2032", "The Sentinel Militia Faction", "The Nest Infections"]
            atmosphere = "Grim, dark, tense, with high contrast shadows and eerie silence broken only by growls."
        elif is_cyberpunk:
            name = f"Neo-Tokyo Sector 9"
            description = f"A sprawling, multi-layered megacity characterized by massive holographic billboards, towering corporate spires, and rain-slicked alleys."
            regions = ["The Neon Slums", "The Megacorp High-Rise Spire", "The Netrunner Grid Underground"]
            lore_elements = ["The AI Independence Pact", "The Corp War of 2081", "The Digital Awakening"]
            atmosphere = "Dystopian, rain-slicked, neon-lit, filled with deep bass hums and buzzing wires."
        elif is_fantasy:
            name = f"The Floating Realm of Aethelgard"
            description = f"A collection of magical, floating landmasses bound together by ancient crystals and diverse, gravity-defying ecosystems."
            regions = ["The Whispering Forests", "The Sky-Shattered Peaks", "The Crystal Valley"]
            lore_elements = ["The Great Cataclysm", "The Crystal Keepers Faction", "Ancient Runestones"]
            atmosphere = "Ethereal, majestic, slightly melancholic, filled with floating light particles and ruins."
        else:
            name = f"The Realm of {title}"
            description = f"An expansive, detailed world designed for the creative theme of '{title}'."
            regions = ["The Safe Haven Sector", "The Wilds Frontier", "The Ancient Ruins Area"]
            lore_elements = ["The Dawn Era", "The Tech Squeeze Faction", "Ancient Archives"]
            atmosphere = "Immersive, focus-driven, and highly detailed."

        return model_class(
            name=name,
            description=description,
            regions=regions,
            lore_elements=lore_elements,
            atmosphere=atmosphere
        )

    elif model_name == "GameplayOutput":
        if is_zombie:
            core_loop = "Scavenge resources during the day, fortify shelter, survive wave attacks at night, manage inventory weight, and level up tactical survival skills."
            mechanics = ["Grid Inventory Management", "Noise Generation System", "Turn-Based Tactical Combat", "Defensive Crafting"]
            progression = "Earn XP from survival tasks to spend in Scavenging, Combat, or Crafting trees."
            difficulty = "Starts simple with lone slow zombies, then scales up with armored mutants and toxic bosses over the surviving weeks."
        elif is_cyberpunk:
            core_loop = "Infiltrate networks, gather corporate intelligence, purchase cybernetic upgrades, hack terminal security, and escape undetected."
            mechanics = ["Neural Hacking System", "Augmented Stealth Visor", "Cybernetic Upgrade Matrix", "Faction Reputation System"]
            progression = "Gain Credits and Tech-Points to install new cerebral implants and unlock netrunner tier abilities."
            difficulty = "Security nodes start with basic firewalls, progressing to aggressive ICE countermeasures and elite corporate counter-hackers."
        elif is_fantasy:
            core_loop = "Explore floating ruins, collect magic seeds, solve environmental puzzles, engage in quick action-combat, and upgrade traversal gear."
            mechanics = ["Relic Traversal Mechanics", "Elemental Combat Reactions", "Environmental Puzzle Solving", "Magic Spell Customization"]
            progression = "Collect relic pieces to increase health and unlock new abilities on the skill board."
            difficulty = "Gradually introduces more complex puzzles and enemies with multiple elemental immunities."
        else:
            core_loop = f"Explore world elements, gather resources, solve creative puzzles, and upgrade tools to progress."
            mechanics = ["Resource Harvesting", "Process Scheduling", "Interactive Task Board", "State Sync Routing"]
            progression = "Collect completion stars to unlock next tier regions and upgrade character statistics."
            difficulty = "Smooth learning curve scaling into complex coordination and multi-stage tasks."

        return model_class(
            core_loop=core_loop,
            mechanics=mechanics,
            progression_system=progression,
            difficulty_curve=difficulty
        )

    elif model_name == "ArtOutput":
        if is_zombie:
            prompts = [
                "Gritty concept art of a ruined city street at dusk, moss covering abandoned cars, de-saturated colors.",
                "A survivor in a green field coat looking out from a dilapidated building window, high contrast warm lighting.",
                "A dark, flooded metro station hallway illuminated only by a single flashlight beam cutting through fog."
            ]
            style = "Realistic gritty survival. Heavy use of dark shadows, muted greens and grays, high contrast warm light highlights (fire, flashlights)."
        elif is_cyberpunk:
            prompts = [
                "Dystopian cyberpunk city street at night, towering buildings, rain-slicked pavement reflecting massive pink and teal neon signs.",
                "Close-up portrait of a netrunner hacker with glowing blue cybernetic eyes, wires running from neck to VR interface.",
                "A high-tech hackers den inside an industrial container, surrounded by glowing monitor matrices and server towers."
            ]
            style = "Cyberpunk sci-fi aesthetic. Heavy use of neon pinks, cyans, and deep blues. High contrast light reflections on metallic and wet surfaces."
        elif is_fantasy:
            prompts = [
                "Lush forest with massive floating glowing crystals, rich blue and purple night sky.",
                "A majestic stone keep built on a floating mountain edge, sunrise warm lighting.",
                "Concept art of a glowing crystal altar inside an ancient cavern, warm light particles."
            ]
            style = "Cinematic fantasy style. Vibrant color grading (blues, golds, teals), soft lighting, magical glows and particles."
        else:
            prompts = [
                f"Beautiful concept art representing the theme of {title}, cinematic lighting.",
                f"Detailed layout design vista, high quality, realistic rendering."
            ]
            style = "Clean, modern design. Balanced colors, premium high-contrast accent highlights, and elegant details."

        return model_class(
            prompts=prompts,
            image_paths=[],
            style_guide=style
        )

    elif model_name == "QAOutput":
        if is_zombie:
            assessment = "Excellent alignment between the survival storyline and the grid inventory/scarcity mechanics. The dark visual atmosphere perfectly matches the grim narrative tone."
            suggestions = ["Add more character dialogue referencing the shortage of bullets to reinforce the scavenging loop."]
            issues = []
        elif is_cyberpunk:
            assessment = "High cohesion between corporate espionage theme and the cybernetic upgrade mechanics. Netrunning hacking feel matches the neon style."
            suggestions = ["Add a visual representation of the threat level when hacking terminals to raise tension."]
            issues = ["Ensure character roles explain how they acquired their cybernetic interfaces."]
        elif is_fantasy:
            assessment = "Highly consistent fantasy theme. The lore elements tie nicely into the exploration loop, and the visual guide supports the overall mood."
            suggestions = ["Consider adding a region specific gameplay mechanic for the Sky-Shattered Peaks."]
            issues = ["Ensure the floating mountain lore links back to the elemental traversal mechanics in gameplay."]
        else:
            assessment = f"Strong structural integrity. All project elements align well with the prompt '{title}'."
            suggestions = ["Add more tool integration cards in the guidelines tab to cover all tools."]
            issues = []

        return model_class(
            consistency_score=9.5 if not issues else 9.0,
            issues=issues,
            suggestions=suggestions,
            overall_assessment=assessment
        )

    elif model_name == "ReviewerOutput":
        from backend.models.output_models import ReviewIssue
        if is_zombie:
            issues = [
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
                )
            ]
            summary = "Strong overall consistency. Minor naming standardization needed for the protagonist's title. World regions are well-defined but one location is underutilized in the narrative."
        elif is_cyberpunk:
            issues = [
                ReviewIssue(
                    category="character",
                    description="Kaelen Vex's digital camouflage ability is listed but no corresponding stealth mechanic is designed in gameplay.",
                    severity="warning",
                    suggested_fix="Explicitly include stealth modifiers in the gameplay mechanics list.",
                    references=["Character Agent: Kaelen Vex", "Gameplay Agent: mechanics"],
                )
            ]
            summary = "Consistent cyberpunk blueprint. One minor mismatch between netrunner abilities and available stealth mechanics."
        elif is_fantasy:
            issues = [
                ReviewIssue(
                    category="character",
                    description="General Vex is described as using 'Shadow Magic' but the world lore does not establish a shadow magic system.",
                    severity="warning",
                    suggested_fix="Add shadow magic as a forbidden art in the world lore elements.",
                    references=["Character Agent: General Vex", "World Agent: lore_elements"],
                )
            ]
            summary = "Highly consistent fantasy project. The narrative, world, and gameplay systems align well. One minor lore gap identified regarding the antagonist's abilities."
        else:
            issues = []
            summary = "Excellent structural integrity. The blueprint aligns perfectly with the specified guidelines."

        return model_class(
            consistency_score=9.5 if not issues else 9.0,
            issues=issues,
            summary=summary
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
        if is_zombie:
            readme = f"# {title}\n\n> A gritty post-apocalyptic survival RPG set in a world overrun by the Necro-7 virus.\n\n## Overview\n{title} is a turn-based tactical survival RPG where players guide a squad of scavengers through zombie-infested ruins in search of a cure.\n\n## Key Features\n- Deep narrative with moral choices\n- Grid-based inventory management\n- Tactical turn-based combat\n- Dynamic day/night survival cycle\n\n## Tech Stack\n- AI-Generated Design by DreamXV AI Studio\n- Multi-Agent Band Collaboration\n\n---\n*Built with DreamXV AI Studio — Born at 15. Built for Infinity.*"
            gdd = f"# Game Design Document: {title}\n\n## Vision Statement\nA survival RPG that blends tactical combat with resource scarcity, set in a hauntingly atmospheric post-apocalyptic world.\n\n## Target Audience\nCore gamers aged 16-35 who enjoy survival horror and tactical RPGs.\n\n## Genre\nSurvival Horror RPG with Turn-Based Tactical Combat\n\n## Core Gameplay Loop\nScavenge → Fortify → Survive → Progress\n\n## Narrative Design\nThree-act structure following a squad's journey to find the Necro-7 cure.\n\n## Art Direction\nGritty, desaturated palette with high-contrast lighting and atmospheric fog."
            features = ["Turn-based tactical combat", "Grid inventory system", "Noise-based stealth mechanics", "Day/night survival cycle", "Defensive crafting", "Character skill trees", "Multiple story endings"]
            core_mechanics = ["Grid Inventory Management with weight limits", "Noise Generation System affecting zombie awareness", "Turn-Based Tactical Combat with cover mechanics", "Defensive Crafting for shelter fortification"]
            monetization = ["Premium Edition with exclusive survivor skins", "Story DLC expansion packs", "Cosmetic weapon camos", "Soundtrack and artbook bundle"]
            future = ["DLC: new frozen biome", "Co-op multiplayer survival mode", "Community map editor", "Seasonal challenge events"]
            tech_summary = "AI-driven game design using DreamXV multi-agent pipeline. Story, characters, world, gameplay, art, and QA generated collaboratively by 15 specialized AI agents powered by Featherless AI with AIMLAPI fallback."
            elevator = f"{title} is a tactical survival RPG where every bullet counts and every choice matters. Guide your squad through a zombie apocalypse, scavenge for the cure, and face the hardest question: who do you save when you can't save everyone?"
        elif is_cyberpunk:
            readme = f"# {title}\n\n> A high-stakes corporate espionage netrunner RPG set in dystopian Neo-Tokyo 2087.\n\n## Overview\n{title} is an action RPG where players hack neural networks, upgrade cybernetic implants, and execute stealth missions to dismantle megacorporation monopolies.\n\n## Key Features\n- Real-time hacking mechanics\n- Cybernetic implant customization\n- Dystopian neon city-exploration\n- Multi-path stealth missions"
            gdd = f"# Game Design Document: {title}\n\n## Vision Statement\nA fast-paced cyberpunk RPG blending stealth infiltration with deep hacking simulations set in a neon-lit corporate dystopia.\n\n## Target Audience\nFans of cyberpunk aesthetics, hacking puzzles, and choice-driven stealth action.\n\n## Genre\nCyberpunk Stealth Action RPG\n\n## Core Gameplay Loop\nHack → Infiltrate → Augment → Upgrade → Escape\n\n## Narrative Design\nUnravel corporate conspiracies across Sector 9, executing high-profile data heists to spark a rebellion."
            features = ["Neural hacking mini-games", "Cybernetic skill trees", "Stealth cloaking devices", "Dynamic neon weather", "Faction reputation tracking"]
            core_mechanics = ["Neural Network hacking grid", "Stealth visual detection cones", "Cybernetic implant power drain", "Interactive city traversal"]
            monetization = ["Cosmetic neon outfit packs", "Netrunner expansion modules", "Digital soundtrack & wallpaper pack"]
            future = ["DLC: Sector 10 Orbit Station", "Online leaderboards for speedruns", "Multiplayer co-op hacking raids"]
            tech_summary = "Dystopian sci-fi design compiled using DreamXV's 15-agent collaboration grid, utilizing OpenAI-compatible structured prompts and custom JSON validators."
            elevator = f"In {title}, hack your way through corporate defense arrays, mount cybernetic augmentations, and spark a digital revolution in the dark alleys of Neo-Tokyo."
        elif is_fantasy:
            readme = f"# {title}\n\n> A majestic fantasy RPG of relic seekers and floating sky islands.\n\n## Overview\n{title} is an adventure RPG where players navigate dangerous sky bridges, cleanse corrupted elemental crystals, and battle ancient shadows.\n\n## Key Features\n- Floating island exploration\n- Relic energy blade combat\n- Environmental crystal puzzles\n- Epic orchestrations"
            gdd = f"# Game Design Document: {title}\n\n## Vision Statement\nAn ethereal sky-high adventure RPG combining fluid platforming traversal with elemental magic combat.\n\n## Target Audience\nRPG players who love expansive fantasy worlds, platforming, and magical lore.\n\n## Genre\nFantasy Action Adventure RPG\n\n## Core Gameplay Loop\nExplore → Cleanse Crystals → Level Up Relics → Progress"
            features = ["Floating island grappling systems", "Elemental reaction combat", "Crystal puzzle systems", "Glowing magic customization"]
            core_mechanics = ["Aero-relic grapple traversal", "Elemental status reaction chains", "Crystal temple puzzle locks", "Weapon relic attributes"]
            monetization = ["Character cosmetic robes", "Expansive sky island DLCs", "Artbook and orchestral soundtrack pack"]
            future = ["Co-op dungeon raids", "Guild sky-bases", "Mount customization (flying beasts)"]
            tech_summary = "Fantasy worldbuilding generated collaboratively by Lead Story, World, and Art agents, verified for narrative-gameplay alignment by QA and Reviewer."
            elevator = f"Embark on a breathtaking journey across floating islands in {title}. Cleanse ancient crystal nodes, master elemental spell blades, and save the realm from plunging into the abyss."
        else:
            readme = f"# {title}\n\n> A unique creative project crafted by AI agents.\n\n## Overview\n{title} is a custom adventure designed collaboratively by specialized agents within DreamXV AI Studio.\n\n## Key Features\n- Fully customized storyline\n- Distinct gameplay loops\n- Tailored visual styles"
            gdd = f"# Game Design Document: {title}\n\n## Vision Statement\nAn immersive game experience built from the ground up to realize the user's prompt.\n\n## Target Audience\nGamers who appreciate custom-tailored designs and collaborative storytelling.\n\n## Core Gameplay Loop\nExplore → Discover → Complete Milestones → Upgrade → Succeed"
            features = ["Custom character paths", "Interactive maps", "Tool coordination guidelines", "Visual style guides"]
            core_mechanics = ["Input synchronization", "State tracking", "Dynamic layout loading"]
            monetization = ["Standard design templates", "Asset package integrations"]
            future = ["Extended platform builds", "Community modification tools"]
            tech_summary = "Dynamic project layout compiled by the 15-agent pipeline, validated by Reviewer and QA agents."
            elevator = f"Experience {title}, an innovative creative project designed to bring your prompt to life using modern multi-agent systems."

        return model_class(
            readme=readme,
            gdd=gdd,
            feature_list=features,
            core_mechanics=core_mechanics,
            monetization=monetization,
            future_expansion=future,
            technical_summary=tech_summary,
            elevator_pitch=elevator
        )

    elif model_name == "TimelineOutput":
        from backend.models.output_models import TimelineMilestone
        return model_class(
            roadmap_weekly=[
                TimelineMilestone(week="Week 1", title="Technical Foundation", details=[
                    "Day 1: Repository configuration & folder structures setup (09:00-12:00: Setup files, 13:00-16:00: Initialize Git)",
                    "Day 2: Core configuration and API client verification (09:00-12:00: Setup keys, 13:00-16:00: Test initial calls)",
                    "Day 3: State machine logic & base framework (09:00-12:00: Code reducer, 13:00-16:00: Test transitions)"
                ]),
                TimelineMilestone(week="Week 2", title="Core Loop Prototype", details=[
                    "Day 1: Basic input handling & controller scripts (09:00-12:00: Bind inputs, 13:00-16:00: Write movements)",
                    "Day 2: Movement physics & boundary validation (09:00-12:00: Set gravity, 13:00-16:00: Boundary collisions)"
                ]),
                TimelineMilestone(week="Week 3", title="Systems Integration", details=[
                    "Day 1: Database tables & auth schemas (09:00-12:00: Write tables, 13:00-16:00: Test auth routes)",
                    "Day 2: HUD overlay and telemetry metrics (09:00-12:00: Code UI panels, 13:00-16:00: Bind states)"
                ]),
                TimelineMilestone(week="Week 4", title="QA Audit & Packaging", details=[
                    "Day 1: Playtesting and performance profiling (09:00-12:00: Bug sweep, 13:00-16:00: Frame profiling)",
                    "Day 2: Target platform compile & export (09:00-12:00: Config build settings, 13:00-16:00: Package design kits)"
                ])
            ],
            roadmap_monthly=[
                "Month 1: Technical Foundation & Base Framework",
                "Month 2: Core Loop Mechanics & Telemetry Bindings",
                "Month 3: Asset Cleanups & Integration Testing",
                "Month 4: Final QA Audits & Release Compilation"
            ]
        )

    elif model_name == "FeasibilityOutput":
        return model_class(
            success_probability=78.0 if not is_zombie else 82.0,
            estimated_completion_days=45 if is_web else 90,
            required_team_size=3 if is_zombie or is_fantasy else 2,
            required_hours_per_day=6.0,
            risk_level="Low" if is_web else "Medium"
        )

    elif model_name == "RiskOutput":
        from backend.models.output_models import RiskItem
        if is_zombie:
            risks = [
                RiskItem(category="scope_creep", description="Designing too many zombie variants might delay deployment.", severity="Medium", mitigation="Implement core basic and special infected types first."),
                RiskItem(category="asset_delays", description="High-fidelity 3D assets could slow down the pipeline.", severity="Medium", mitigation="Use mock assets or pre-rigged survivor prefabs during testing.")
            ]
        else:
            risks = [
                RiskItem(category="technical_complexity", description="API rate limit or connectivity issues during live integration.", severity="Low", mitigation="Implement local client caches and fallback structures."),
                RiskItem(category="timeline", description="Aggressive release target could squeeze testing windows.", severity="Medium", mitigation="Establish strict MVP bounds and run automated unit checks early.")
            ]
        return model_class(risks=risks)

    elif model_name == "ProjectPlannerOutput":
        from backend.models.output_models import SprintPlan, KanbanTask
        if is_zombie:
            sprints = [
                SprintPlan(sprint_name="Sprint 1: Core Survivors Setup", goal="Deliver working controller physics and combat inputs.", tasks=["Set up player camera Prefab", "Wire shooting trigger mechanisms"]),
                SprintPlan(sprint_name="Sprint 2: Zombie Waves Implementation", goal="Deliver wave spawning and basic pathogen AI.", tasks=["Design wave trigger zones", "Configure pathfinding colliders"])
            ]
            kanban = [
                KanbanTask(task_id="TSK-001", title="Establish player input mapping", status="Done", assignee="Gameplay Programmer", dependencies=[]),
                KanbanTask(task_id="TSK-002", title="Draw main city street layout", status="InProgress", assignee="Lead Modeler", dependencies=[])
            ]
            dep_graph = ["Input Map -> Character Prefab", "Level Geometry -> Navmesh Nodes"]
        else:
            sprints = [
                SprintPlan(sprint_name="Sprint 1: Base Sandbox Setup", goal="Initialize repository and base interfaces.", tasks=["Initialize Git branch", "Setup routing configurations"]),
                SprintPlan(sprint_name="Sprint 2: Logic Integration", goal="Complete CRUD endpoints and state syncing.", tasks=["Implement project controllers", "Validate request inputs"])
            ]
            kanban = [
                KanbanTask(task_id="TSK-001", title="Write schema migrations", status="Done", assignee="Database Specialist", dependencies=[]),
                KanbanTask(task_id="TSK-002", title="Code main landing dashboard", status="InProgress", assignee="UI Engineer", dependencies=[])
            ]
            dep_graph = ["Database Schema -> API Routers", "API Routers -> State Hooks"]
        return model_class(
            milestones=["Technical Sandbox Validated", "Core Infiltration Loop Complete", "Playable Production Candidate ready"],
            sprints=sprints,
            kanban=kanban,
            dependency_graph=dep_graph
        )

    elif model_name == "AnalyticsOutput":
        return model_class(
            token_usage=115000,
            api_cost=0.14,
            agent_runtime_seconds={
                "Chief Agent": 11.2,
                "Story Agent": 16.5,
                "Character Agent": 8.7,
                "World Agent": 14.2,
                "Gameplay Agent": 13.9,
                "Art Agent": 10.5,
                "QA Agent": 8.1,
                "Reviewer Agent": 9.8,
                "Documentation Agent": 12.5,
                "Timeline Agent": 10.2,
                "Risk Agent": 8.5,
                "Feasibility Agent": 6.8,
                "Project Planner Agent": 11.7,
                "Analytics Agent": 4.8,
                "Export Agent": 6.2
            },
            productivity_score=89.5
        )

    elif model_name == "ExportOutput":
        return model_class(
            markdown_reports={"Readme": "# Project Readme", "GDD": "# Game Design Document"},
            json_export='{"project_name": "Dynamic project design kit"}',
            pdf_exports={"ExecutiveSummary": "Mock PDF Summary base64 data"},
            zip_archive_path="public/exports/project_design_kit.zip"
        )

    elif model_name == "AtlasOutput":
        from backend.models.output_models import AtlasPhase, AtlasTaskBreakdown
        has_game_tools = any(t in prompt_lower for t in ["unity", "unreal", "godot", "blender", "c#", "c++", "pygame", "construct"])
        has_web_tools = any(t in prompt_lower for t in ["react", "fastapi", "supabase", "django", "flask", "node", "express", "html", "css", "js", "ts", "web"])
        is_game_stack = has_game_tools or (not has_web_tools and not is_web)
        if is_game_stack:
            roadmap = [
                AtlasPhase(name="Month 1: Initial Setup & Asset Design", tasks=[
                    "Week 1: Project Setup & Guidelines",
                    "  • Day 1: Code repository initialization & engine setup",
                    "    - 09:00 - 12:00: Create new Unity/Unreal project",
                    "    - 13:00 - 16:00: Configure folder structures & import settings",
                    "  • Day 2: Style guides & asset folders config",
                    "    - 09:00 - 12:00: Configure colors, lighting profiles, & render pipeline",
                    "    - 13:00 - 16:00: Verify asset pipelines for models & textures"
                ])
            ]
            project_structure = [
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
            ]
            flow_map = [
                "Create Asset Designs",
                "Rig & Animate Assets",
                "Import to Engine",
                "Attach Scripts & Physics",
                "Configure Gameplay HUD",
                "Export Distribution Package"
            ]
            dependency_map = [
                "InputManager -> PlayerController -> CombatSystem -> GameHUD"
            ]
            task_breakdown = AtlasTaskBreakdown(
                critical_tasks=["Map camera behaviors", "Code primary action/move behaviors", "Ensure stable launch build"],
                optional_tasks=["Design simple settings panel", "Add ambient sound layers"],
                future_expansion=["Create secondary levels", "Deploy multi-platform exports"],
                tools_guide={}
            )
        else:
            roadmap = [
                AtlasPhase(name="Month 1: Initial Architecture & Setup", tasks=[
                    "Week 1: Project Setup & Init",
                    "  • Day 1: Code repository initialization & workspace structure config",
                    "    - 09:00 - 12:00: Setup base folders and config files"
                ])
            ]
            project_structure = [
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
            ]
            flow_map = [
                "Design UI Mockups",
                "Create Database Schema",
                "Build API Server",
                "Connect React Frontend",
                "Setup Authentication Flow"
            ]
            dependency_map = [
                "Database -> API Service -> Auth Middleware -> Frontend Component"
            ]
            task_breakdown = AtlasTaskBreakdown(
                critical_tasks=["Setup Git repository", "Create responsive dashboard", "Write database models"],
                optional_tasks=["Add light/dark mode theme", "Configure toast notifications"],
                future_expansion=["Implement automated testing", "Integrate caching layers"],
                tools_guide={}
            )
        return model_class(
            project_id="",
            roadmap=roadmap,
            project_structure=project_structure,
            production_flow_map=flow_map,
            dependency_map=dependency_map,
            task_breakdown=task_breakdown
        )

    # Dynamic Fallback Builder
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
        self._semaphore = asyncio.Semaphore(3)

    async def _try_primary(self, func, *args, **kwargs):
        async with self._semaphore:
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

