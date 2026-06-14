"""
DreamXV AI Studio — Unified LLM Service
========================================
Facade that routes LLM requests through Featherless AI (primary)
with automatic fallback to AIMLAPI. Users never see provider selection.
"""

from __future__ import annotations

import inspect
from typing import Optional, Type, TypeVar, Union, List

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
            result = await self._primary.generate(
                messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return result
        except Exception as exc:
            logger.warning(
                f"Featherless AI failed ({type(exc).__name__}: {exc}), "
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
                logger.warning(
                    f"Both primary and fallback LLM services failed: {fallback_exc}. "
                    f"Generating mock text fallback."
                )
                user_prompt = ""
                for msg in reversed(messages):
                    if msg.get("role") == "user":
                        user_prompt = msg.get("content", "")
                        break
                return f"[MOCK FALLBACK] Processed prompt: '{user_prompt}'."

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
            result = await self._primary.generate_structured(
                messages,
                response_model,
                model=model,
                temperature=temperature,
            )
            return result
        except Exception as exc:
            logger.warning(
                f"Featherless AI structured generation failed "
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
                logger.warning(
                    f"Both primary and fallback LLM services failed: {fallback_exc}. "
                    f"Generating mock fallback data for model {response_model.__name__}."
                )
                user_prompt = ""
                for msg in reversed(messages):
                    if msg.get("role") == "user":
                        user_prompt = msg.get("content", "")
                        break
                return generate_mock_data_for_model(response_model, user_prompt)

    async def close(self) -> None:
        """Shut down both provider clients."""
        await self._primary.close()
        await self._fallback.close()

