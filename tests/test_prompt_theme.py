import os
import sys
import unittest
import asyncio
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.band_manager import BandManager

class TestPromptTheme(unittest.TestCase):
    def setUp(self):
        # Load environment variables from .env file
        load_dotenv()
        
    def test_zombie_theme_generation(self):
        # We need to run async code inside standard unittest
        project = asyncio.run(self._run_generation())
        
        # Gather all text content from the generated project to assert on
        all_text = []
        if project.title:
            all_text.append(project.title)
        if project.story:
            all_text.append(project.story.lore)
            all_text.append(project.story.summary)
            all_text.extend(project.story.acts)
            all_text.extend(project.story.themes)
        if project.characters:
            for char in project.characters:
                all_text.append(char.name)
                all_text.append(char.role)
                all_text.append(char.backstory)
                all_text.extend(char.abilities)
                all_text.extend(char.personality_traits)
        if project.world:
            all_text.append(project.world.name)
            all_text.append(project.world.description)
            all_text.extend(project.world.regions)
            all_text.extend(project.world.lore_elements)
            all_text.append(project.world.atmosphere)
        if project.gameplay:
            all_text.append(project.gameplay.core_loop)
            all_text.extend(project.gameplay.mechanics)
            all_text.append(project.gameplay.progression_system)
            all_text.append(project.gameplay.difficulty_curve)
        if project.documentation:
            all_text.append(project.documentation.readme)
            all_text.append(project.documentation.gdd)
            all_text.extend(project.documentation.feature_list)
            all_text.extend(project.documentation.core_mechanics)
            all_text.extend(project.documentation.monetization)
            all_text.extend(project.documentation.future_expansion)
            all_text.append(project.documentation.technical_summary)
            all_text.append(project.documentation.elevator_pitch)
            
        full_content = " ".join(all_text).lower()
        
        # Assertions
        zombie_keywords = ["zombie", "survivor", "infected", "undead", "apocalypse"]
        has_zombie_keyword = any(kw in full_content for kw in zombie_keywords)
        self.assertTrue(
            has_zombie_keyword,
            f"Expected output to contain at least one of {zombie_keywords}, but it was: {full_content[:500]}"
        )
        
        dragon_keywords = ["dragon", "egg", "flight", "fire breath", "floating islands"]
        for kw in dragon_keywords:
            self.assertNotIn(
                kw,
                full_content,
                f"Expected output to NOT contain '{kw}'"
            )

    async def _run_generation(self):
        manager = BandManager()
        # Run a real generation with the input prompt
        project = await manager.generate_project("RPG Zombie Shooter", "test_user")
        return project

if __name__ == "__main__":
    unittest.main()
