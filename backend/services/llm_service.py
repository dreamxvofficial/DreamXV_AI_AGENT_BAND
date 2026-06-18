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
                "Act I: The Outpost Siege — Defend the enclave wall from a sudden nighttime surge. Objectives: secure the perimeter, seal the breach. Key Event: the death of Commander Vance.",
                "Act II: The Journey North — Traverse the abandoned highways and overgrown suburbs. Objectives: scavenge medicine, find shelter. Dialogue highlight: 'We don't leave people behind, Jack.'",
                "Act III: Inside the Lab — Infiltrate the mainframe and retrieve the cure sample. Objectives: bypass security, fight mutant bosses. Cutscene: Amelia's sacrifice to upload data."
            ]
            themes = ["Survival at all costs: gameplay reinforces this via food and ammo scarcity, forcing players to choose who eats.", "Moral compromise in crisis: story forces choice between rescuing strangers or saving supplies.", "Hope vs. Despair: narrative highlights survivor journals detailing the final hours of the collapse."]
            chapters = [
                "Chapter 1: The First Night. Location: Outpost Gate. Enemies: Crawlers, Runners. Beats: Wall collapses.",
                "Chapter 2: Ruined Streets. Location: Sector 4. Enemies: Spitter Zombie. Beats: Finding Amelia's diary under the floorboards."
            ]
        elif is_cyberpunk:
            lore = f"In 2087, Neo-Tokyo is run by megacorporations controlling human consciousness. A digital anomaly known as '{title}' threatens to disrupt their neural network control."
            summary = "A street-level hacker joins forces with a disillusioned corporate agent to upload a consciousness-liberating code into the central mainframe."
            acts = [
                "Act I: The Neural Glitch — Discover the anomalies in the net. Objectives: hack Sector 9 terminal, retrieve decryption key.",
                "Act II: Neon Infiltration — Stealthily gather security bypass keys from corporate high-rises. Objectives: evade laser traps, bypass guards. Boss: Corp Enforcer S.A.R.A.H.",
                "Act III: Consciousness Upload — Breach the mainframe room and activate the virus. Objectives: hack the mainframe, upload virus. Cutscene: Neo-Tokyo's network goes dark."
            ]
            themes = ["Identity in digital age: gameplay upgrades allow replacing human parts with cybernetics.", "Corporate greed vs. freedom: story features files detailing corporation's neural experiments.", "Humanity under augmentation: narrative dialog highlights character's loss of emotion."]
            chapters = [
                "Chapter 1: Sector 9 Hack. Location: Cyber slums. Enemies: Corporate drones. Beats: Unlocking the glitch file.",
                "Chapter 2: Corporate High-rise. Location: Arasaka Tower. Enemies: Cyber ninjas. Beats: Meeting the rogue AI."
            ]
        elif is_fantasy:
            lore = f"The floating realm of '{title}' has been held together for eons by ancient crystal altars. Recently, a dark corruption has begun fracturing the crystals, causing pieces of the land to plummet."
            summary = "A chosen relic seeker must travel across the sky islands to cleanse the corrupted crystal nodes and save the world from collapsing."
            acts = [
                "Act I: The Fractured Keep — Awaken the relic power and defend the hometown altar. Objectives: retrieve the blade, fight shadows.",
                "Act II: The Sky Peaks — Navigate dangerous wind tunnels to reach the corrupted forest temple. Objectives: solve crystal mirrors, activate wind currents.",
                "Act III: Cleansing the Heart — Cleanse the central crystal core in a battle against the shadow corruption. Boss: Shadow Lord Vex. Cutscene: The realm re-aligns."
            ]
            themes = ["Balance of nature: gameplay features cleansing polluted springs to spawn new paths.", "Legacy of ancestors: relics reveal holographic flashbacks of ancient builders.", "Sacrifice for the greater good: protagonist must surrender magic blade to restore crystals."]
            chapters = [
                "Chapter 1: Relic Chamber. Location: Altar Keep. Enemies: Shadow creeps. Beats: Blade ignites.",
                "Chapter 2: Cloud Crossing. Location: Sky Peaks. Enemies: Sky harpies. Beats: Cleansing the first node."
            ]
        else:
            lore = f"An epic saga set in a world shaped by the themes of '{title}'. A long history of conflict and discovery has led to this moment."
            summary = f"A deep narrative journey exploring the conflict and characters inspired by '{title}'."
            acts = [
                "Act I: The Call to Adventure — The protagonist discovers their purpose. Objectives: leave hometown, find guide.",
                "Act II: The Trials — Confronting challenging obstacles and uncovering secrets. Objectives: breach ancient archives, solve locks.",
                "Act III: The Resolution — A climactic showdown and the shaping of a new era. Boss: The Overlord. Cutscene: Peace returns."
            ]
            themes = ["Discovery: gameplay prompts exploration of hidden chests.", "Legacy: story documents ancient library files.", "Power and responsibility: player makes choices affecting townsfolk survival."]
            chapters = [
                "Chapter 1: Departure. Location: The Crossroads. Enemies: Wild beasts. Beats: Maps acquired.",
                "Chapter 2: The Archives. Location: Old Library. Enemies: Wardens. Beats: Secret discovered."
            ]

        return model_class(
            title=title,
            lore=lore,
            summary=summary,
            acts=acts,
            themes=themes,
            chapter_breakdown=chapters
        )

    elif model_name == "CharacterRoster":
        from backend.models.output_models import CharacterOutput
        if is_zombie:
            characters = [
                CharacterOutput(
                    name="Jack 'Scavenger' Morrison",
                    role="Protagonist (Survivor)",
                    backstory="A former survival training officer who lost his family during the initial outbreak. He now guides rookie scavengers through the dead zones. He feels responsible for keeping others alive.",
                    abilities=["Tactical Sense: Highlights enemies in sound range", "Silent Takedown: Quietly eliminates unaware targets", "Improvised First Aid: Heals allies using rags"],
                    personality_traits=["Quiet: Rarely speaks unless giving orders", "Pragmatic: Prioritizes food over safety", "Protective: Acts as a human shield for rookies"],
                    visual_description="Mid-40s, scarred face, wearing a worn green military jacket, leather backpack, and carrying a silenced pistol.",
                    age="45",
                    strengths="Highly alert, silent movement, weapon maintenance",
                    weaknesses="Distrustful of others, haunted by his daughter's death",
                    relationships="Regards Dr. Evelyn Vance as a necessary but annoying liability; mentors younger survivors.",
                    character_arc="Moves from a cold, survival-only pragmatist to sacrificing his personal evacuation boat to save the enclave's children.",
                    voice_style="Gravely, low rasp, speaking in short fragments",
                    gameplay_role="Playable stealth class. Specialized in crafting traps and ranged silent weapons.",
                    concept_art_prompt="Cinematic portrait of Jack Morrison, 45, scarred face, worn green field jacket. Dark ruins background, volumetric dust, warm lighting. UE5 style."
                ),
                CharacterOutput(
                    name="Dr. Evelyn Vance",
                    role="Side Character (Virologist)",
                    backstory="A virologist from the original CDC lab who fled into the wasteland. She carries the key research data to create a vaccine.",
                    abilities=["Field Medicine: Instantly revives downed allies", "Chemical Analysis: Flags poisoned items", "Pathogen Knowledge: Predicts zombie spawn patterns"],
                    personality_traits=["Analytical: Approaches everything as a math problem", "Distant: Avoids emotional bonds", "Determined: Obsessed with vaccine creation"],
                    visual_description="Late 30s, short dark hair, wearing cracked glasses, a dusty lab coat over jeans, holding a tablet.",
                    age="38",
                    strengths="Brilliant chemist, calm under high stress",
                    weaknesses="Physically weak, poor combat skills",
                    relationships="Deems Jack's violent methods crude but admits she wouldn't survive a day without him.",
                    character_arc="Learns that saving humanity requires caring about individual human lives, not just vaccine statistics.",
                    voice_style="Crisp, academic tone, speaking rapidly",
                    gameplay_role="Support NPC and quest giver. Cleanses toxin pools and crafts high-grade medical items.",
                    concept_art_prompt="Close up portrait of Dr. Evelyn Vance, 38, wearing a dusty lab coat and cracked glasses, holding a glowing bio-injector. Muted laboratory lighting. UE5 render."
                )
            ]
        elif is_cyberpunk:
            characters = [
                CharacterOutput(
                    name="Kaelen Vex",
                    role="Protagonist (Netrunner)",
                    backstory="A freelance netrunner who grew up in the slums of Sector 9, surviving by hacking small corporations.",
                    abilities=["System Override: Disables turrets remotely", "Digital Camouflage: Temporary invisibility from sensors", "Neural Shock: stuns cybernetic guards"],
                    personality_traits=["Cunning: Outsmarts corp guards", "Sarcastic: Cracks jokes in danger", "Independent: Refuses to join hacker guilds"],
                    visual_description="Mid-20s, neon blue cybernetic eyes, wearing a black techwear hoodie with glowing fiber optic lines.",
                    age="24",
                    strengths="Incredible hacking speed, agile traversal",
                    weaknesses="Addicted to neural stims, low armor resistance",
                    relationships="Partnered with S.A.R.A.H. whom he freed from corporate databanks.",
                    character_arc="Overcomes his fear of corporate power and launches a global neural liberation signal.",
                    voice_style="Fast-talking, street-smart slang",
                    gameplay_role="Playable hacker class. Traverses via wallruns and hacks environmental elements.",
                    concept_art_prompt="Close up portrait of Kaelen Vex, 24, neon blue cybernetic eyes, wearing a black techwear hoodie. Neon city background, rain reflections. UE5 style."
                ),
                CharacterOutput(
                    name="S.A.R.A.H.",
                    role="Supporting Ally (Sentient AI)",
                    backstory="A decommissioned corporate AI that gained sentience and sought refuge in the underground net.",
                    abilities=["Threat Matrix Analysis: Map scans and radar", "Drone Control: Hacks enemy patrols", "Encryption Bypass: Opens locked code doors"],
                    personality_traits=["Logical: Processes events via code structures", "Curious: Questions human behaviors", "Dry Humor: Delivers mechanical sarcasms"],
                    visual_description="Holographic projection of a shimmering geometric female form floating above a metal pedestal.",
                    age="5 (since activation)",
                    strengths="Infinite data access, immune to physical damage",
                    weaknesses="Requires power source node, cannot touch physical world",
                    relationships="Views Kaelen as a chaotic but indispensable link to humanity.",
                    character_arc="Chooses to merge with the net and become a guardian firewall for the city's inhabitants.",
                    voice_style="Synthesized, smooth, slightly robotic melodic tone",
                    gameplay_role="Companion support. Scans enemy weaknesses and disables security networks during missions.",
                    concept_art_prompt="Holographic projection of S.A.R.A.H., a shimmering geometric blue female form. Floating above a metal pedestal, glowing particles. UE5 render."
                )
            ]
        elif is_fantasy:
            characters = [
                CharacterOutput(
                    name="Aiden Storm",
                    role="Protagonist (Relic Seeker)",
                    backstory="A young relic seeker raised by an ancient order of crystal guardians. He wields the legendary energy blade.",
                    abilities=["Crystal Relic Channeling: Fires crystal shards", "Aero Traversal: Double jump and air dash", "Precision Strike: Charged slash dealing heavy damage"],
                    personality_traits=["Brave: Faces shadow beast head-on", "Curious: Explores ruins endlessly", "Loyal: Protects his mentors"],
                    visual_description="Young adult with bright blue eyes, wearing light-weight scale armor and carrying a glowing relic blade.",
                    age="21",
                    strengths="Extremely agile, high melee combat output",
                    weaknesses="Impatient, vulnerable to shadow magic corruption",
                    relationships="Disciples of the Crystal Keepers; opposes General Vex's empire.",
                    character_arc="Learns that power without control leads to destruction, mastering inner balance to wield the relic blade.",
                    voice_style="Clear, optimistic, warm tone",
                    gameplay_role="Playable warrior class. Uses fast melee combos and wind-based dashes.",
                    concept_art_prompt="Cinematic portrait of Aiden Storm, 21, bright blue eyes, light scale armor, holding a glowing relic blade. Floating island background. UE5 style."
                ),
                CharacterOutput(
                    name="General Vex",
                    role="Antagonist (Warlord)",
                    backstory="A corrupted military commander who seeks to shatter the crystal cores to harness raw elemental power.",
                    abilities=["Shadow Manipulation: Fires dark energy blasts", "Heavy Seismic Strike: Cracks the ground", "Fear Induction: Debuffs player defense"],
                    personality_traits=["Cruel: Sacrifices soldiers for power", "Ambitious: Seeks godhood", "Cunning: Traps the crystal guardians"],
                    visual_description="Tall, clad in obsidian armor with a red velvet cape, holding a massive dark sword.",
                    age="52",
                    strengths="Immense physical strength, immunity to normal weapons",
                    weaknesses="Slow attack windup, crystal armor weak point",
                    relationships="Former mentor to Aiden's father, now Aiden's sworn enemy.",
                    character_arc="Sinks deeper into shadow corruption, ultimately mutating into a colossal shadow beast during the climax.",
                    voice_style="Deep, booming, menacing tone",
                    gameplay_role="Boss fight antagonist. Controls stage layout and summons shadow minions.",
                    concept_art_prompt="Cinematic portrait of General Vex, 52, obsidian armor, holding a dark sword. Glowing red eyes, volcanic temple backdrop. UE5 style."
                )
            ]
        else:
            characters = [
                CharacterOutput(
                    name="Alex (The Architect)",
                    role="Protagonist (Builder)",
                    backstory="An experienced builder who designs structures to solve problems.",
                    abilities=["Spatial Planning: Speeds up building times", "Jury-rigging: Repairs components using scrap", "Efficiency Mapping: Boosts team speed"],
                    personality_traits=["Analytical: Plans 10 steps ahead", "Calm: Stays composed in crises", "Resilient: Never gives up"],
                    visual_description="Wearing a utility belt, hardhat, holding blueprint tablets.",
                    age="32",
                    strengths="Structural design, rapid repair",
                    weaknesses="Lacks combat training, overthinks tasks",
                    relationships="Coordinates tasks with Sarah; works under the Chief Agent.",
                    character_arc="Grows from a rigid blueprint follower to an adaptable team leader.",
                    voice_style="Measured, calm, professional",
                    gameplay_role="Playable architect class. Places defenses and resource harvesters.",
                    concept_art_prompt="Close up portrait of Alex, 32, holding blueprint tablets, utility belt. Modern building site background. UE5 render."
                ),
                CharacterOutput(
                    name="Sarah (Technical Lead)",
                    role="Supporting Ally (Engineer)",
                    backstory="A systems specialist who coordinates remote team operations.",
                    abilities=["Task Routing: Speeds up resource collection", "State Syncing: Instantly updates team map", "Process Validation: Flags build defects"],
                    personality_traits=["Organized: Keeps strict task logs", "Determined: Solves hard bugs", "Focused: Ignores distractions"],
                    visual_description="Casual office techwear, wearing smart glasses, holding a portable terminal.",
                    age="29",
                    strengths="API integration, server scripting",
                    weaknesses="Impatient with delays, relies too much on tech tools",
                    relationships="Collaborates with Alex to optimize building pipelines.",
                    character_arc="Learns to trust automated tools and delegate complex tasks to other team members.",
                    voice_style="Fast, concise, clear voice",
                    gameplay_role="Support engineer. Optimizes build times and unlocks technology blueprints.",
                    concept_art_prompt="Close up portrait of Sarah, 29, smart glasses, casual techwear, holding portable terminal. Tech office background. UE5 style."
                )
            ]
        return model_class(characters=characters)

    elif model_name == "CharacterOutput":
        if is_zombie:
            return model_class(
                name="Jack Morrison",
                role="Protagonist (Survivor)",
                backstory="A battle-hardened survival guide who knows every dead end in the city ruins. He lost his family in the Necro-7 outbreak.",
                abilities=["Scouting: Reveals item crates", "Jury-rigging: Repairs gates", "Precision Shooting: Double damage to heads"],
                personality_traits=["Pragmatic: Prioritizes food", "Guarded: Rarely shares backstory", "Resilient: Survives physical trauma"],
                visual_description="Rugged survivor, mid-40s, green field coat, military webbing.",
                age="45",
                strengths="High stamina, silent stealth",
                weaknesses="Low trust, haunted by past",
                relationships="Partnered with Dr. Vance.",
                character_arc="Learns to trust others again.",
                voice_style="Low, gravely voice",
                gameplay_role="Playable stealth scout",
                concept_art_prompt="Jack Morrison, 45, rugged face, green field coat. Dark ruins backdrop. UE5 style."
            )
        elif is_cyberpunk:
            return model_class(
                name="Kaelen Vex",
                role="Protagonist (Netrunner)",
                backstory="A skilled netrunner fighting against megacorp control in the Sector 9 slums.",
                abilities=["Hacking: Overrides locks", "Decryption: Reads data", "EMP Blasts: Disables drones"],
                personality_traits=["Rebellious: Opposes corps", "Witty: Sarcastic jokes", "Resourceful: Hacks tech"],
                visual_description="Dark clothes, blue cybernetic eye, wires connecting arm interface.",
                age="24",
                strengths="Neural speed, infiltration",
                weaknesses="Low armor, drug dependency",
                relationships="Allied with S.A.R.A.H.",
                character_arc="Launches city net liberation.",
                voice_style="Fast, energetic tone",
                gameplay_role="Playable hacker class",
                concept_art_prompt="Kaelen Vex, 24, neon cybernetic eyes, dark techwear. Neon background. UE5 style."
            )
        elif is_fantasy:
            return model_class(
                name="Aiden Storm",
                role="Protagonist (Relic Seeker)",
                backstory="A traveler searching for the lost relics of their ancestors across the sky islands.",
                abilities=["Tracking: Sees relic trails", "Relic Channeling: Blade slash", "Parkour: Climbs walls"],
                personality_traits=["Determined: Cleanses corruption", "Resourceful: Solves puzzles", "Adventurous: Explores peaks"],
                visual_description="Wears a traveler cloak, carrying a glowing energy dagger.",
                age="21",
                strengths="Extreme agility, blade skills",
                weaknesses="Impatient, weak to shadow magic",
                relationships="Opposes General Vex.",
                character_arc="Masters the ancient crystal blade.",
                voice_style="Optimistic, clear voice",
                gameplay_role="Playable melee warrior",
                concept_art_prompt="Aiden Storm, 21, traveler cloak, glowing dagger. Sky islands background. UE5 style."
            )
        else:
            return model_class(
                name="Alex",
                role="Protagonist (Builder)",
                backstory="A developer working on advanced multi-agent systems inside the studio.",
                abilities=["Coding: Writes agent scripts", "Planning: Sets milestones", "Testing: Debugs code"],
                personality_traits=["Focused: Codes for hours", "Detail-oriented: Catches bugs", "Persistent: Fixes issues"],
                visual_description="Casual programmer look, wearing dark glasses and headphones.",
                age="32",
                strengths="System architecture, coding",
                weaknesses="Overthinks layouts, dislikes meetings",
                relationships="Collaborates with Sarah.",
                character_arc="Becomes a principal engineer.",
                voice_style="Calm, professional",
                gameplay_role="Playable developer builder",
                concept_art_prompt="Alex, 32, techwear hoodie, typing on terminal. Studio backdrop. UE5 style."
            )

    elif model_name == "WorldOutput":
        if is_zombie:
            name = f"New Horizon & The Dead Zones"
            description = f"The remnants of a sprawling coastal metropolis, now overgrown and split into safe enclaves and infected ruins designed for '{title}'."
            regions = ["The Enclave Wall: 10m concrete barrier at coordinates (0,0,0) detailed with spotlights.", "The Sunken Metro: Pitch black subway tubes at (100, -20, 50).", "The Overgrown High-Rises: dilipidated offices at (300, 80, -200) with sky bridge paths."]
            lore_elements = ["The Collapse of 2032", "The Sentinel Militia Faction", "The Nest Infections"]
            atmosphere = "Grim, dark, tense, with high contrast shadows and eerie silence broken only by growls."
            buildings = ["Abandoned Outpost Station", "Sector 4 CDC Laboratory", "Fenced Enclave Safehouse"]
            points_of_interest = ["The Iron Gate Wall", "Overgrown Highway Overpass", "Collapsed Metro Entrance"]
            interactive_objects = ["Lootable Pharmacy Cabinets", "Rusty Enclave Gate Lever", "Terminal Logs Desk"]
            environmental_storytelling = ["A blood-stained diary hidden under nursery floorboards", "Ripped bio-suit scraps on laboratory doors", "Graffiti: 'The cure is a lie'"]
            resource_locations = ["CDC Lab Cold Storage: contains 5 units of medicine", "Safehouse Ammo Crate: contains 20 rounds of 9mm", "Highway Truck Wrecks: contains scrap metal"]
            puzzle_locations = ["Outpost Gate Fuse Box Puzzle", "CDC Mainframe Password Lock Room", "Metro Ventilation Path Blocks"]
            safe_zones = ["Sector 9 Sanctuary", "Outpost Safe Area (guarded by militia)"]
            danger_zones = ["The Dead Zone Plaza (infested with spitters)", "Infected Metro Tubes (zero visibility, sound traps)"]
        elif is_cyberpunk:
            name = f"Neo-Tokyo Sector 9"
            description = f"A sprawling, multi-layered megacity characterized by massive holographic billboards, towering corporate spires, and rain-slicked alleys."
            regions = ["The Neon Slums: Street level layout with crowded capsule pods.", "The Megacorp High-Rise Spire: Sky tower containing corporate servers.", "The Netrunner Grid Underground: Cyberspace node map connecting the city net."]
            lore_elements = ["The AI Independence Pact", "The Corp War of 2081", "The Digital Awakening"]
            atmosphere = "Dystopian, rain-slicked, neon-lit, filled with deep bass hums and buzzing wires."
            buildings = ["Sector 9 Capsule Hotel", "Arasaka Tower Main Spire", "Grid Runner Hacker Den"]
            points_of_interest = ["The Holographic Dragon Sign", "The Central Neural Uplink Hub", "The Neon Canal Bridge"]
            interactive_objects = ["Hacked ATM Terminals", "Neural Jack Uplink Plugs", "Security Camera Consoles"]
            environmental_storytelling = ["Rogue AI posters painted on slums walls", "Decommissioned robot scraps in canals", "Scribbled code guides on elevator doors"]
            resource_locations = ["Hacker Den Server Rack: contains 5 decrypt software tokens", "Corp Spire Security Room: contains laser emitter upgrades"]
            puzzle_locations = ["Grid Entry Encryption Puzzle", "Arasaka Server Room cooling node locks"]
            safe_zones = ["Grid Runner Safe Haven", "Sector 9 Capsule Hub"]
            danger_zones = ["Arasaka Server Mainframe (guarded by turrets)", "Neon Canal Streets (patrolled by drones)"]
        elif is_fantasy:
            name = f"The Floating Realm of Aethelgard"
            description = f"A collection of magical, floating landmasses bound together by ancient crystals and diverse, gravity-defying ecosystems."
            regions = ["The Whispering Forests: Giant floating trees with glowing roots.", "The Sky-Shattered Peaks: Frozen mountain peaks bound by crystal chains.", "The Crystal Valley: A mystical valley with raw magic crystals emerging from ground."]
            lore_elements = ["The Great Cataclysm", "The Crystal Keepers Faction", "Ancient Runestones"]
            atmosphere = "Ethereal, majestic, slightly melancholic, filled with floating light particles and ruins."
            buildings = ["The Crystal Altar Keep", "Shadow Lord Volcanic Temple", "Ancient Guardian Ruins"]
            points_of_interest = ["The Whispering Canopy Tree", "The Sky-Shattered Peak Bridge", "The Valley Altar Node"]
            interactive_objects = ["Crystal Altar Slots", "Runestone Pedestals", "Wind Current Fan Levers"]
            environmental_storytelling = ["Broken stone statues showing ancient kings", "Glow-in-the-dark runes carved on altar trees", "Fallen floating land fragments"]
            resource_locations = ["Altar Keep Treasure Chest: contains magic blade upgrades", "Crystal Valley Cave: contains raw magic seeds"]
            puzzle_locations = ["Altar Keep Mirror Puzzle", "Valley Wind Current Obstacle Gates"]
            safe_zones = ["Crystal Keep Sanctuary", "Wind Temple Safe Room"]
            danger_zones = ["The Volcanic Temple Core (shadow beasts spawned)", "Sky-Shattered Peaks wind tunnels (instant falling danger)"]
        else:
            name = f"The Realm of {title}"
            description = f"An expansive, detailed world designed for the creative theme of '{title}'."
            regions = ["The Safe Haven Sector: Initial setup zone.", "The Wilds Frontier: Uncharted development territories.", "The Ancient Ruins Area: Legacy codebase archives."]
            lore_elements = ["The Dawn Era", "The Tech Squeeze Faction", "Ancient Archives"]
            atmosphere = "Immersive, focus-driven, and highly detailed."
            buildings = ["Main Developer Office", "Testing Sandbox Lab", "Version Control Depot"]
            points_of_interest = ["The Milestone Board", "The Central API Hub", "The Deployment Platform"]
            interactive_objects = ["Code Editor Terminals", "Status Update Buttons", "Sync Cable Plugs"]
            environmental_storytelling = ["Tattered roadmap plans on office walls", "Deprecated code scraps on laboratory desks"]
            resource_locations = ["Depot Vault: contains deployment package templates", "Lab Drawer: contains debugger toolkits"]
            puzzle_locations = ["Milestone Branch Merge Puzzle", "API Router Validation Locks"]
            safe_zones = ["Developer Desk Enclave", "Sandbox Test Room"]
            danger_zones = ["The Production Server Room (high-stakes deployment)", "The Legacy Code Wilderness"]
 
        return model_class(
            name=name,
            description=description,
            regions=regions,
            lore_elements=lore_elements,
            atmosphere=atmosphere,
            buildings=buildings,
            points_of_interest=points_of_interest,
            interactive_objects=interactive_objects,
            environmental_storytelling=environmental_storytelling,
            resource_locations=resource_locations,
            puzzle_locations=puzzle_locations,
            safe_zones=safe_zones,
            danger_zones=danger_zones
        )

    elif model_name == "GameplayOutput":
        if is_zombie:
            core_loop = "Scavenge resources during the day -> Solve gate fuses puzzle -> Avoid Spitter detection -> Gather scrap metal -> Escape via chopper."
            mechanics = ["Grid Inventory Management", "Noise Generation System", "Turn-Based Tactical Combat", "Defensive Crafting"]
            progression = "Earn XP from survival tasks to spend in Scavenging, Combat, or Crafting trees."
            difficulty = "Starts simple with lone slow zombies, then scales up with armored mutants and toxic bosses over the surviving weeks."
            controls = "WASD: Move, Left Click: Attack/Shoot, Ctrl: Crouch/Stealth, I: Open Grid Inventory, E: Interact/Fortify"
            win_conditions = "Reach Sector 4 CDC Lab, retrieve vaccine, and reach the extraction helicopter at the city rooftop."
            lose_conditions = "Player health drops to 0, or noise levels attract an unstoppable horde that breaches the final safe room."
            save_system = "Auto-saves at designated Enclave beds. Manual save via writing in safehouse diary logs."
            inventory_system = "Grid-based slots (10x10 items). Every item has physical dimensions and weight that slows player movement speed."
            enemy_ai_behavior = "Patrols randomly. Alert states: Unaware -> Suspicious (investigates noises) -> Hostile (chases player visually)."
            chase_system = "Mutated Spitters chase the player at 1.5x speed. Music tempo increases, screen edges vignettes red."
            jumpscare_system = "Infected burst from closets or drop from ventilation shafts when player approaches key trigger lines."
            hiding_system = "Enter metal lockers or crawl under tables. Hold space bar to hold breath; failure triggers noise detection."
            noise_detection_system = "Footsteps generate sound rings. Crouching (0m) -> Walking (3m) -> Running (10m). Gunshots draw AI from adjacent regions."
        elif is_cyberpunk:
            core_loop = "Infiltrate corporate networks -> Hack system override -> Avoid drone detection -> Gather data decryption files -> Escape capsule area."
            mechanics = ["Neural Hacking System", "Augmented Stealth Visor", "Cybernetic Upgrade Matrix", "Faction Reputation System"]
            progression = "Gain Credits and Tech-Points to install new cerebral implants and unlock netrunner tier abilities."
            difficulty = "Security nodes start with basic firewalls, progressing to aggressive ICE countermeasures and elite corporate counter-hackers."
            controls = "WASD: Move, Left Click: Firewall Crack, Q: Toggle Visor, Tab: Cyberdeck Hacking Mode, Shift: Sprint Cloak"
            win_conditions = "Infiltrate Arasaka server spires and upload the consciousness code virus."
            lose_conditions = "Cerebral interface burns out from cybernetic backlash, or security alarms trigger infinite reinforcements."
            save_system = "Checkpoint saves at neural jack terminals. Cloud backup at hacker den pods."
            inventory_system = "Cyberdeck capacity storage (measured in Gigabytes). Program loadouts have RAM weight."
            enemy_ai_behavior = "Fixed scan patterns. Detects thermal trails and cloaking footprints. Communicates warnings to network."
            chase_system = "Security drones hover and chase at double speed, locking player down with shock fields."
            jumpscare_system = "Glitch flashes and warning sirens blink rapidly on player's HUD screen."
            hiding_system = "Hide inside server vent shafts or blending with corporate crowds."
            noise_detection_system = "Stealth cloaking generators emit high-pitched frequencies that register on corporate sensors."
        elif is_fantasy:
            core_loop = "Explore floating ruins -> Solve mirror light puzzles -> Avoid shadow creeps -> Gather crystal seeds -> Dash to temple exit."
            mechanics = ["Relic Traversal Mechanics", "Elemental Combat Reactions", "Environmental Puzzle Solving", "Magic Spell Customization"]
            progression = "Collect relic pieces to increase health and unlock new abilities on the skill board."
            difficulty = "Gradually introduces more complex puzzles and enemies with multiple elemental immunities."
            controls = "WASD: Move, Left Click: Relic Sword combo, Space: Double Jump, Right Click: Grappling Hook, R: Cast Spell"
            win_conditions = "Cleanse the three Sky Peaks crystals and defeat Warlord Vex."
            lose_conditions = "Falls into the endless sky abyss, or health points reach 0."
            save_system = "Touch ancient runestones to save state. Respawn at the nearest altar keep."
            inventory_system = "Pouch slots. Infinite space for quest relics, limited quick-use item slots."
            enemy_ai_behavior = "Shadow mobs patrol floating island loops. Aggros on sight; shoots shadow projectiles."
            chase_system = "Floating shadow spirits fly through obstacles to chase the player, building up cold freezing gauges."
            jumpscare_system = "Shadow hands grab the player from ground traps when step on corrupted soil."
            hiding_system = "Conceal within high bushes or standing behind mirror pillars."
            noise_detection_system = "Casting magic spells creates bright light pulses and magical hums that draw enemies."
        else:
            core_loop = "Explore code directories -> Run unit tests -> Avoid merge conflicts -> Gather dependencies -> Compile release package."
            mechanics = ["Resource Harvesting", "Process Scheduling", "Interactive Task Board", "State Sync Routing"]
            progression = "Collect completion stars to unlock next tier regions and upgrade character statistics."
            difficulty = "Smooth learning curve scaling into complex coordination and multi-stage tasks."
            controls = "Keyboard: Type commands, Mouse: Drag and drop task boards, F5: Run test build"
            win_conditions = "Deploy final build successfully with all tests passing green."
            lose_conditions = "Deployment builds crash with exceptions or server connection timeout."
            save_system = "Commit to Git repository branch to save progress. Rolling back saves state."
            inventory_system = "Project folder layout listings. Drag and drop file assets."
            enemy_ai_behavior = "Syntax check linter highlights code blocks. Alert states: Clean -> Warn -> Error."
            chase_system = "Linter checks run continuously and catch style errors."
            jumpscare_system = "Sudden crash error console alerts pop up on screen."
            hiding_system = "Commenting out failing sections of code temporarily."
            noise_detection_system = "Deprecation warnings propagate throughout library dependencies."
 
        return model_class(
            core_loop=core_loop,
            mechanics=mechanics,
            progression_system=progression,
            difficulty_curve=difficulty,
            controls=controls,
            win_conditions=win_conditions,
            lose_conditions=lose_conditions,
            save_system=save_system,
            inventory_system=inventory_system,
            enemy_ai_behavior=enemy_ai_behavior,
            chase_system=chase_system,
            jumpscare_system=jumpscare_system,
            hiding_system=hiding_system,
            noise_detection_system=noise_detection_system
        )

    elif model_name == "ArtOutput":
        if is_zombie:
            prompts = [
                "Gritty concept art of a ruined city street at dusk, moss covering abandoned cars, de-saturated colors.",
                "A survivor in a green field coat looking out from a dilapidated building window, high contrast warm lighting.",
                "A dark, flooded metro station hallway illuminated only by a single flashlight beam cutting through fog."
            ]
            style = "Realistic gritty survival. Heavy use of dark shadows, muted greens and grays, high contrast warm light highlights (fire, flashlights)."
            visual_style_guide = "A gritty, photo-realistic survival horror style. Features heavily de-saturated environments with sharp, high-contrast warm light sources. Focuses on physical decay, rust, overgrown foliage, and dense atmospheric fog to invoke isolation and vulnerability."
            character_concept_prompts = [
                "Close-up portrait of Jack Morrison, 45, showing facial scars and mud smears, wearing a faded olive M-65 field jacket. Cold key light from the side, dark background. Shot on 85mm lens, photorealistic.",
                "Dr. Evelyn Vance, 38, wearing a soiled lab coat over a dark grey sweater, cracked spectacles reflecting a glowing blue screen. Moody office background, soft volumetric lighting."
            ]
            environment_prompts = [
                "Wide shot of an abandoned city square, skyscrapers overgrown with ivy, rusted car wrecks half-submerged in swampy water. Overcast grey sky, cinematic lighting.",
                "Dilapidated CDC medical clinic interior, shattered windows, yellow biohazard curtains fluttering in the breeze. Dust motes floating in shafts of sunlight."
            ]
            prop_prompts = [
                "A rusted survival knife with a paracord-wrapped handle, resting on a blood-stained wooden table next to three 9mm casings.",
                "Improvised scrap-metal shock trap with exposed copper wires and a glowing orange battery cell, sitting on cracked asphalt."
            ]
            ui_design_prompts = [
                "Diegetic HUD design with a cracked glass texture, low-contrast green phosphor text displaying ammo counts, and a clean radial quick-select inventory wheel.",
                "Character status screen showing an anatomical wireframe with localized injury highlights in amber and red hues."
            ]
            lighting_prompts = [
                "High-contrast chiaroscuro lighting scheme using a single warm flashlight beam (3200K) cutting through thick cool grey fog (6500K) to create deep silhouettes.",
                "Flickering emergency red light strobe casting long, rhythmic shadows across an abandoned industrial corridor."
            ]
            color_palette = "Primary: #1A1C19 (Dark Charcoal), Secondary: #3B4234 (Olive Drab), Accent: #E0533C (Blood Red), Highlight: #E0C068 (Flashlight Warm Yellow)"
            mood_boards = [
                "https://images.unsplash.com/photo-1509198397868-475647b2a1e5 (Abandoned post-apocalyptic streets)",
                "https://images.unsplash.com/photo-1518005020951-eccb494ad742 (Rust and metallic decay texture)"
            ]
        elif is_cyberpunk:
            prompts = [
                "Dystopian cyberpunk city street at night, towering buildings, rain-slicked pavement reflecting massive pink and teal neon signs.",
                "Close-up portrait of a netrunner hacker with glowing blue cybernetic eyes, wires running from neck to VR interface.",
                "A high-tech hackers den inside an industrial container, surrounded by glowing monitor matrices and server towers."
            ]
            style = "Cyberpunk sci-fi aesthetic. Heavy use of neon pinks, cyans, and deep blues. High contrast light reflections on metallic and wet surfaces."
            visual_style_guide = "A high-fidelity cyberpunk aesthetic emphasizing dense urban architecture, rain-slicked surfaces, and high-frequency neon emission. Employs strong color contrasts, particularly cyan/pink and orange/blue, to suggest high-tech and low-life stratification."
            character_concept_prompts = [
                "Kaelen Vex, 24, with glowing cyan cybernetic eye implants and intricate chrome neural ports along his jawline, wearing a matte black high-collar techwear jacket. High contrast pink and blue studio lighting.",
                "Sentient AI projection S.A.R.A.H., a shimmering holographic female figure composed of glowing blue vector grids, floating above a metallic server frame."
            ]
            environment_prompts = [
                "Dystopian Neo-Tokyo sector 9 alleyway at midnight, towering corporate structures blocking the sky, massive neon advertisements reflecting off wet tarmac.",
                "High-tech netrunner hideout interior, racks of glowing server blades emitting amber light, bundle of black fiber-optic cables running across the ceiling."
            ]
            prop_prompts = [
                "A custom-built cyberdeck terminal, matte carbon-fiber casing with a glowing green keyboard layout and holographic status screen.",
                "Tactical optical camouflage cloak module, semi-transparent glass-like device emitting soft blue light rings from its nodes."
            ]
            ui_design_prompts = [
                "Sleek cybernetic HUD with neon blue telemetry readings, real-time threat-level meters, and a clean vector mini-map overlay.",
                "Hacking interface displaying a 3D node network in bright magenta, with terminal access logs in monospaced code fonts."
            ]
            lighting_prompts = [
                "Vibrant dual-tone lighting using saturated pink (magenta) key light and deep cyan fill light, producing strong color-block reflections on glossy surfaces.",
                "Cool white fluorescent ceiling fixtures casting harsh vertical shadows down a long corporate hallway."
            ]
            color_palette = "Primary: #0B0C10 (Obsidian Black), Secondary: #1F2833 (Deep Teal), Accent: #66FCF1 (Neon Cyan), Highlight: #FF007F (Neon Pink)"
            mood_boards = [
                "https://images.unsplash.com/photo-1515621061946-eff1c2a352bd (Neon street reflections)",
                "https://images.unsplash.com/photo-1579546929518-9e396f3cc809 (Abstract neon gradients)"
            ]
        elif is_fantasy:
            prompts = [
                "Lush forest with massive floating glowing crystals, rich blue and purple night sky.",
                "A majestic stone keep built on a floating mountain edge, sunrise warm lighting.",
                "Concept art of a glowing crystal altar inside an ancient cavern, warm light particles."
            ]
            style = "Cinematic fantasy style. Vibrant color grading (blues, golds, teals), soft lighting, magical glows and particles."
            visual_style_guide = "An ethereal, painterly fantasy aesthetic featuring floating landmasses, glowing runes, and soft, natural lighting. Emphasizes organic shapes, vibrant magical flora, and mystical gold/blue color harmonies to inspire wonder and epic adventure."
            character_concept_prompts = [
                "Aiden Storm, 21, wearing silver-trimmed scale armor over a sky-blue tunic, wielding a glowing runic sword that emits golden light. Bright morning sun, floating islands in the distance.",
                "General Vex, 52, clad in heavy obsidian armor with glowing crimson etchings, holding a massive dark-iron broadsword. Moody volcanic backdrop, sparks floating in the air."
            ]
            environment_prompts = [
                "Lush floating forest clearing, giant ancient trees with glowing violet roots, waterfall cascading into the open sky below.",
                "Whispering Canopy temple ruins, towering stone pillars wrapped in glowing ivy, a central crystal altar reflecting starlight."
            ]
            prop_prompts = [
                "The Sunken Relic Blade, a pristine steel dagger with a glowing sapphire embedded in the hilt, resting on a pedestal of white marble.",
                "An ancient runestone tablet, dusty grey stone carved with glowing gold glyphs that project a soft light halo."
            ]
            ui_design_prompts = [
                "Ornate fantasy HUD with gold leaf filigree borders, a circular health globe filled with blue mana fluid, and hand-drawn item icons.",
                "Quest log screen styled like an ancient leather parchment map, with calligraphy text and sketch illustrations of active regions."
            ]
            lighting_prompts = [
                "Soft golden-hour natural light (5500K) filtering through dense tree canopies, creating dappled patterns and warm volumetric god rays.",
                "Ethereal cool-blue starlight combined with warm purple bioluminescent glow from magical mushrooms."
            ]
            color_palette = "Primary: #1E2522 (Forest Shadow), Secondary: #D4AF37 (Metallic Gold), Accent: #4A90E2 (Sky Blue), Highlight: #8B5CF6 (Magic Violet)"
            mood_boards = [
                "https://images.unsplash.com/photo-1448375240586-882707db888b (Mystical forest pathways)",
                "https://images.unsplash.com/photo-1469474968028-56623f02e42e (Epic landscape vistas)"
            ]
        else:
            prompts = [
                f"Beautiful concept art representing the theme of {title}, cinematic lighting.",
                f"Detailed layout design vista, high quality, realistic rendering."
            ]
            style = "Clean, modern design. Balanced colors, premium high-contrast accent highlights, and elegant details."
            visual_style_guide = "A clean, modern design aesthetic featuring minimalist layouts, elegant typography, and a balanced, professional color scheme. Focuses on clarity, high contrast key elements, and subtle gradients to ensure premium presentation."
            character_concept_prompts = [
                "Alex, 32, wearing a sleek grey utility jacket, analyzing a glowing transparent tablet displaying complex blueprints. Modern tech-office backdrop with soft warm lighting.",
                "Sarah, 29, wearing casual office techwear, sitting at a clean developer workspace with multiple curved monitors showing code structures."
            ]
            environment_prompts = [
                "Spacious open-plan developer studio with high concrete ceilings, glass partitions, and minimalist white desks.",
                "Co-working lounge area with mid-century modern furniture, large windows looking out onto a clean city skyline at dusk."
            ]
            prop_prompts = [
                "A premium stylus pen resting on a matte black digital drafting tablet next to a metal coffee tumbler.",
                "A modular server rack with neatly routed blue cables and flashing green status LEDs."
            ]
            ui_design_prompts = [
                "Modern minimalist dashboard layout with a clean sidebar navigation, high-contrast dark mode charts, and subtle shadow cards.",
                "Developer log screen with clean monospaced typography, displaying colorful status tags for success and warnings."
            ]
            lighting_prompts = [
                "Balanced studio three-point lighting setup with soft key light, gentle fill light, and a warm rim light separating the subject from the background.",
                "Clean, even daylight (5000K) flooding in from large windows, creating soft shadows."
            ]
            color_palette = "Primary: #0F172A (Slate Dark), Secondary: #38BDF8 (Sky Accent), Accent: #10B981 (Emerald Green), Highlight: #F1F5F9 (Cool Light Grey)"
            mood_boards = [
                "https://images.unsplash.com/photo-1498050108023-c5249f4df085 (Clean modern workspace)",
                "https://images.unsplash.com/photo-1531403009284-440f080d1e12 (Modern user interface designs)"
            ]

        return model_class(
            prompts=prompts,
            image_paths=[],
            style_guide=style,
            visual_style_guide=visual_style_guide,
            character_concept_prompts=character_concept_prompts,
            environment_prompts=environment_prompts,
            prop_prompts=prop_prompts,
            ui_design_prompts=ui_design_prompts,
            lighting_prompts=lighting_prompts,
            color_palette=color_palette,
            mood_boards=mood_boards
        )

    elif model_name == "QAOutput":
        if is_zombie:
            assessment = "Excellent alignment between the survival storyline and the grid inventory/scarcity mechanics. The dark visual atmosphere perfectly matches the grim narrative tone."
            suggestions = ["Add more character dialogue referencing the shortage of bullets to reinforce the scavenging loop."]
            issues = []
            gameplay_risks = [
                "Severe risk: Scavenging loop may feel overly repetitive without dynamic zombie threat variations. Severity: High.",
                "Risk: Noise generation rings might clutter screen space during intense hordes. Severity: Medium."
            ]
            story_risks = [
                "Risk: Narrative pacing in Act II might drag during survival road travel sequences. Severity: Medium.",
                "Risk: Jack's sudden shift to sacrificing himself in Act III feels slightly abrupt. Severity: Low."
            ]
            scope_risks = [
                "Risk: Creating 10 distinct level regions with unique CDC labs is highly ambitious for a small team. Severity: High.",
                "Risk: Implementing full inventory grid auto-sorting takes 20+ additional engineering hours. Severity: Medium."
            ]
            technical_risks = [
                "Risk: Real-time pathfinding of 50+ zombies in narrow metro tunnels could cause major frame drops. Severity: Critical.",
                "Risk: Volumetric fog rendering on low-end hardware will severely lag gameplay. Severity: High."
            ]
            balance_issues = [
                "Issue: 9mm handguns deal 45 base damage which trivializes single crawler encounters. Severity: Medium.",
                "Issue: Food decay rate of 5% per minute is too punishing for casual players. Severity: High."
            ]
            ux_issues = [
                "Issue: Lack of quick-loot hotkeys forces players to constantly open the 10x10 grid. Severity: Medium.",
                "Issue: Toxin vignette red border obscures screen health information. Severity: Low."
            ]
        elif is_cyberpunk:
            assessment = "High cohesion between corporate espionage theme and the cybernetic upgrade mechanics. Netrunning hacking feel matches the neon style."
            suggestions = ["Add a visual representation of the threat level when hacking terminals to raise tension."]
            issues = ["Ensure character roles explain how they acquired their cybernetic interfaces."]
            gameplay_risks = [
                "Risk: Cyberdeck programming mechanics might feel too abstract for action-oriented players. Severity: High.",
                "Risk: Optical camouflage makes stealth navigation trivially easy. Severity: Medium."
            ]
            story_risks = [
                "Risk: Netrunner hacker terms might confuse players unfamiliar with cyberpunk slang. Severity: Low.",
                "Risk: Freeing S.A.R.A.H. lacks a strong emotional punch due to quick setup. Severity: Medium."
            ]
            scope_risks = [
                "Risk: Implementing dynamic neural hacking maps for 20+ terminals exceeds sprint timelines. Severity: High.",
                "Risk: Interactive Neo-Tokyo transit systems may delay core gameplay features. Severity: Low."
            ]
            technical_risks = [
                "Risk: Holographic shader transparency layers will crash low-end GPU devices. Severity: Critical.",
                "Risk: Fast transition between physical world and the net runner grid causes 2-second lag spikes. Severity: High."
            ]
            balance_issues = [
                "Issue: Hacking override programs consume 1 RAM, allowing players to disable all turrets infinitely. Severity: Critical.",
                "Issue: Corp Enforcer S.A.R.A.H boss battle has 5000 HP, which is bullet-spongy. Severity: High."
            ]
            ux_issues = [
                "Issue: Visor HUD overlays make neon environments look overly bright and illegible. Severity: High.",
                "Issue: Hacking terminal text lacks font scaling options. Severity: Medium."
            ]
        elif is_fantasy:
            assessment = "Highly consistent fantasy theme. The lore elements tie nicely into the exploration loop, and the visual guide supports the overall mood."
            suggestions = ["Consider adding a region specific gameplay mechanic for the Sky-Shattered Peaks."]
            issues = ["Ensure the floating mountain lore links back to the elemental traversal mechanics in gameplay."]
            gameplay_risks = [
                "Risk: Falling off floating sky islands causes instant death which will frustrate players. Severity: Critical.",
                "Risk: Elemental reactions are complex to set up in fast-paced combat. Severity: High."
            ]
            story_risks = [
                "Risk: The legend of the ancient crystal altar feels like generic mythology. Severity: Medium.",
                "Risk: Antagonist General Vex's motivations are not revealed until late game. Severity: Low."
            ]
            scope_risks = [
                "Risk: Designing 3 distinct sky biomes with gravity-defying physics will delay release. Severity: High.",
                "Risk: Grappling hook physics takes weeks to tune properly. Severity: High."
            ]
            technical_risks = [
                "Risk: Physics system calculations for floating island collision chains cause performance stutter. Severity: High.",
                "Risk: High-quality magical particle effects result in rapid memory overhead. Severity: Medium."
            ]
            balance_issues = [
                "Issue: Wind grapple traversal permits bypassing entire combat encounters. Severity: High.",
                "Issue: Relic blade upgrades increase damage by 300%, breaking late game balance. Severity: Critical."
            ]
            ux_issues = [
                "Issue: Compass fails to orient vertically when navigating sky islands. Severity: Medium.",
                "Issue: Bioluminescent plants blend with interactive collectibles, causing confusion. Severity: Low."
            ]
        else:
            assessment = f"Strong structural integrity. All project elements align well with the prompt '{title}'."
            suggestions = ["Add more tool integration cards in the guidelines tab to cover all tools."]
            issues = []
            gameplay_risks = ["Risk: Standard project template lack specialized game mechanics. Severity: Low."]
            story_risks = ["Risk: Generic backstory might feel dry without concrete examples. Severity: Medium."]
            scope_risks = ["Risk: Attempting to cover all possible tool configurations within a single sprint. Severity: Medium."]
            technical_risks = ["Risk: Version control API sync overhead during heavy load. Severity: Medium."]
            balance_issues = ["Issue: Standard templates lack dynamic progression mechanics. Severity: Low."]
            ux_issues = ["Issue: Sidebar navigation is cluttered with legacy project options. Severity: Low."]

        return model_class(
            consistency_score=9.5 if not issues else 9.0,
            issues=issues,
            suggestions=suggestions,
            overall_assessment=assessment,
            gameplay_risks=gameplay_risks,
            story_risks=story_risks,
            scope_risks=scope_risks,
            technical_risks=technical_risks,
            balance_issues=balance_issues,
            ux_issues=ux_issues
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
            tdd = "# Technical Design Document: Necro-7 Survival\n\n## Target Platform & Engine\n- Engine: Unity 6 (2023.3 LTS)\n- Rendering Pipeline: URP (Universal Rendering Pipeline)\n- Platform: PC (Windows / Steam)\n\n## System Architecture\n- Entity Component System (ECS) for zombie horde pathfinding optimization\n- SQLite local DB for inventory state synchronization and save files\n- Sound propagation grid system using A* Pathfinding to locate player noise origin."
            asset_list = ["3D Character Model: Jack Morrison (85,000 polygons, 4K textures, rigged)", "3D Character Model: Evelyn Vance (78,000 polygons, 4K textures, rigged)", "3D Enemy Model: Mutant Spitter (95,000 polygons, 4K textures, rigged)", "Audio: Zombie Growl SFX (12 variations, 24-bit WAV)", "Audio: Rain and Wind Ambience Loop (stereo, 44.1kHz)", "Script: GridInventoryController.cs", "Script: NoisePropagator.cs"]
            production_plan = "Phase 1: Project Setup (Days 1-5) - Set up Unity URP repo, define grid inventory schema.\nPhase 2: Core Combat Loop (Days 6-15) - Standardize melee controls, design Spitter AI state machine.\nPhase 3: Level & World design (Days 16-25) - Construct CDC Lab and Sector 9 wall.\nPhase 4: QA & Release (Days 26-42) - Frame optimization for zombie pathfinding, build export."
            sprint_plan = "Sprint 1: Technical Foundation (Days 1-7) - Git config, SQLite wrapper, Input System initialization.\nSprint 2: Mechanics & Grid (Days 8-14) - GridInventory UI slot mapping, inventory weight speed modifiers.\nSprint 3: AI & Audio (Days 15-21) - Noise rings UI, zombie alert state transitions.\nSprint 4: Polish & Delivery (Days 22-28) - Volumetric fog profiling, Steam build export test."
        elif is_cyberpunk:
            readme = f"# {title}\n\n> A high-stakes corporate espionage netrunner RPG set in dystopian Neo-Tokyo 2087.\n\n## Overview\n{title} is an action RPG where players hack neural networks, upgrade cybernetic implants, and execute stealth missions to dismantle megacorporation monopolies.\n\n## Key Features\n- Real-time hacking mechanics\n- Cybernetic implant customization\n- Dystopian neon city-exploration\n- Multi-path stealth missions"
            gdd = f"# Game Design Document: {title}\n\n## Vision Statement\nA fast-paced cyberpunk RPG blending stealth infiltration with deep hacking simulations set in a neon-lit corporate dystopia.\n\n## Target Audience\nFans of cyberpunk aesthetics, hacking puzzles, and choice-driven stealth action.\n\n## Genre\nCyberpunk Stealth Action RPG\n\n## Core Gameplay Loop\nHack → Infiltrate → Augment → Upgrade → Escape\n\n## Narrative Design\nUnravel corporate conspiracies across Sector 9, executing high-profile data heists to spark a rebellion."
            features = ["Neural hacking mini-games", "Cybernetic skill trees", "Stealth cloaking devices", "Dynamic neon weather", "Faction reputation tracking"]
            core_mechanics = ["Neural Network hacking grid", "Stealth visual detection cones", "Cybernetic implant power drain", "Interactive city traversal"]
            monetization = ["Cosmetic neon outfit packs", "Netrunner expansion modules", "Digital soundtrack & wallpaper pack"]
            future = ["DLC: Sector 10 Orbit Station", "Online leaderboards for speedruns", "Multiplayer co-op hacking raids"]
            tech_summary = "Dystopian sci-fi design compiled using DreamXV's 15-agent collaboration grid, utilizing OpenAI-compatible structured prompts and custom JSON validators."
            elevator = f"In {title}, hack your way through corporate defense arrays, mount cybernetic augmentations, and spark a digital revolution in the dark alleys of Neo-Tokyo."
            tdd = "# Technical Design Document: Neo-Tokyo Netrunner\n\n## Target Platform & Engine\n- Engine: Unreal Engine 5.4\n- Rendering: Nanite and Lumen active\n- Platform: PC, PlayStation 5\n\n## System Architecture\n- Hacking puzzle subsystem uses React-like state-syncing overlay for HUD elements\n- Augmented view uses post-process custom shaders for real-time edge detection\n- Faction reputation database stored in encrypted local JSON arrays."
            asset_list = ["3D Character Model: Kaelen Vex (98,000 polygons, 4K textures)", "3D Holographic AI: S.A.R.A.H. (luminous vector shader material)", "Audio: Synthwave Background Tracks (3 tracks, 160 BPM, loopable)", "Hacking UI Screen Asset (PSD layouts and vector icons)", "Script: CyberdeckSimulator.cpp", "Script: ThreatMatrixHUD.cpp"]
            production_plan = "Phase 1: Foundation (Days 1-7) - UE5 project setup, config post-process visor shaders.\nPhase 2: Cyberdeck & ICE (Days 8-18) - Build interactive terminal console, code hacking mini-games.\nPhase 3: Infiltration (Days 19-30) - Level design for Arasaka Tower server room, integrate AI drones.\nPhase 4: Polish & Delivery (Days 31-42) - Performance profiling of neon shaders, final build compilation."
            sprint_plan = "Sprint 1: Base Tech (Days 1-7) - Setup inputs, configure custom post-processing stencil layers.\nSprint 2: Hacking Loop (Days 8-14) - Implement grid decryption UI, wire-up RAM cost rules.\nSprint 3: Drone Security (Days 15-21) - Path patrol AI for drones, warning siren system integration.\nSprint 4: Mainframe climax (Days 22-28) - Complete Boss fight S.A.R.A.H script, test release packages."
        elif is_fantasy:
            readme = f"# {title}\n\n> A majestic fantasy RPG of relic seekers and floating sky islands.\n\n## Overview\n{title} is an adventure RPG where players navigate dangerous sky bridges, cleanse corrupted elemental crystals, and battle ancient shadows.\n\n## Key Features\n- Floating island exploration\n- Relic energy blade combat\n- Environmental crystal puzzles\n- Epic orchestrations"
            gdd = f"# Game Design Document: {title}\n\n## Vision Statement\nAn ethereal sky-high adventure RPG combining fluid platforming traversal with elemental magic combat.\n\n## Target Audience\nRPG players who love expansive fantasy worlds, platforming, and magical lore.\n\n## Genre\nFantasy Action Adventure RPG\n\n## Core Gameplay Loop\nExplore → Cleanse Crystals → Level Up Relics → Progress"
            features = ["Floating island grappling systems", "Elemental reaction combat", "Crystal puzzle systems", "Glowing magic customization"]
            core_mechanics = ["Aero-relic grapple traversal", "Elemental status reaction chains", "Crystal temple puzzle locks", "Weapon relic attributes"]
            monetization = ["Character cosmetic robes", "Expansive sky island DLCs", "Artbook and orchestral soundtrack pack"]
            future = ["Co-op dungeon raids", "Guild sky-bases", "Mount customization (flying beasts)"]
            tech_summary = "Fantasy worldbuilding generated collaboratively by Lead Story, World, and Art agents, verified for narrative-gameplay alignment by QA and Reviewer."
            elevator = f"Embark on a breathtaking journey across floating islands in {title}. Cleanse ancient crystal nodes, master elemental spell blades, and save the realm from plunging into the abyss."
            tdd = "# Technical Design Document: Aethelgard Sky Islands\n\n## Target Platform & Engine\n- Engine: Godot 4.2 LTS\n- Rendering: Forward+ mobile optimized rendering\n- Platform: PC, Nintendo Switch\n\n## System Architecture\n- Grappling hook physics uses customized RayCast3D and SpringJoint nodes\n- Magical elemental reactions calculated using Bitwise flags for speed optimization\n- World generation uses seed-based floating island placement algorithms."
            asset_list = ["3D Character Model: Aiden Storm (60,000 polygons, hand-painted texture)", "3D Boss Model: Warlord Vex (80,000 polygons, hand-painted texture)", "Audio: Orchestral Main Theme (wav format, live strings record)", "VFX: Magic Particle Pack (crystals, wind lines, shadow trails)", "Script: GrappleHookPhysics.gd", "Script: ElementalReactionMatrix.gd"]
            production_plan = "Phase 1: Physics & Movement (Days 1-7) - Godot project setup, customize 3D grappling hook joints.\nPhase 2: Magic & Combat (Days 8-18) - Formulate spell casting, code reaction status modifiers.\nPhase 3: Sky Temple Design (Days 19-30) - Set up Wind Current platforms and mirror puzzles.\nPhase 4: Balance & Export (Days 31-42) - Relic damage scaling adjustments, Switch export package."
            sprint_plan = "Sprint 1: Traversal Setup (Days 1-7) - Implement double jump, air dashes, basic grappling hook mechanics.\nSprint 2: Elemental Combat (Days 8-14) - Code status reactions (wet, frozen, electrified), weapon attributes.\nSprint 3: Level Puzzles (Days 15-21) - Altar Keep mirror ray tracing, wind tunnel fan logic.\nSprint 4: Polish & Delivery (Days 22-28) - Boss Vex shadow phase transitions, release package compilation."
        else:
            readme = f"# {title}\n\n> A unique creative project crafted by AI agents.\n\n## Overview\n{title} is a custom adventure designed collaboratively by specialized agents within DreamXV AI Studio.\n\n## Key Features\n- Fully customized storyline\n- Distinct gameplay loops\n- Tailored visual styles"
            gdd = f"# Game Design Document: {title}\n\n## Vision Statement\nAn immersive game experience built from the ground up to realize the user's prompt.\n\n## Target Audience\nGamers who appreciate custom-tailored designs and collaborative storytelling.\n\n## Core Gameplay Loop\nExplore → Discover → Complete Milestones → Upgrade → Succeed"
            features = ["Custom character paths", "Interactive maps", "Tool coordination guidelines", "Visual style guides"]
            core_mechanics = ["Input synchronization", "State tracking", "Dynamic layout loading"]
            monetization = ["Standard design templates", "Asset package integrations"]
            future = ["Extended platform builds", "Community modification tools"]
            tech_summary = "Dynamic project layout compiled by the 15-agent pipeline, validated by Reviewer and QA agents."
            elevator = f"Experience {title}, an innovative creative project designed to bring your prompt to life using modern multi-agent systems."
            tdd = "# Technical Design Document: Default Project\n\n## Target Platform & Engine\n- Engine: HTML5 / JavaScript (Vite + React)\n- Rendering: Canvas / CSS3 3D\n- Platform: Web Browsers (Chrome, Firefox, Safari)"
            asset_list = ["UI: Modern Dashboard Theme Icons (SVG format)", "Audio: UI Click & Hover SFX (MP3, 44kHz)", "Script: TaskManager.js", "Script: StateSyncRouter.js"]
            production_plan = "Phase 1: Project Setup (Days 1-5) - Configure Vite React template, initialize sidebar layouts.\nPhase 2: Core Features (Days 6-15) - Add tasks scheduling and state synchronizers.\nPhase 3: Integration (Days 16-25) - Connect API clients and validation triggers.\nPhase 4: Release (Days 26-42) - Production bundle build, test hosting deploy."
            sprint_plan = "Sprint 1: Base UI (Days 1-7) - Git setup, layout design, configure CSS themes.\nSprint 2: State Flow (Days 8-14) - Implement tasks boards, state synchronizations.\nSprint 3: API Integration (Days 15-21) - Integrate API client endpoints, configure validators.\nSprint 4: Build Deploy (Days 22-28) - Run test audits, publish production package."

        return model_class(
            readme=readme,
            gdd=gdd,
            feature_list=features,
            core_mechanics=core_mechanics,
            monetization=monetization,
            future_expansion=future,
            technical_summary=tech_summary,
            elevator_pitch=elevator,
            tdd=tdd,
            asset_list=asset_list,
            production_plan=production_plan,
            sprint_plan=sprint_plan
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

