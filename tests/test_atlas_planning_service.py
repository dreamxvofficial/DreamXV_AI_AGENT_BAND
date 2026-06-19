import unittest

from backend.services.atlas_planning_service import build_atlas_plan, parse_duration


class AtlasPlanningServiceTests(unittest.TestCase):
    def test_duration_granularity_matches_requested_scale(self):
        self.assertEqual((parse_duration("1 week").period_label, parse_duration("1 week").period_count), ("Day", 7))
        self.assertEqual((parse_duration("3 weeks").period_label, parse_duration("3 weeks").period_count), ("Week", 3))
        self.assertEqual((parse_duration("3 months").period_label, parse_duration("3 months").period_count), ("Month", 3))
        self.assertEqual((parse_duration("1 year").period_label, parse_duration("1 year").period_count), ("Quarter", 4))

    def test_game_plan_uses_capacity_tools_and_game_flow(self):
        output, metadata = build_atlas_plan(
            project_id="atlas-test", project_title="Zombie Horror Game", duration="3 months",
            team_size=1, hours_per_day=3,
            tools="Unity, Blender, Claude Code, Antigravity IDE, ChatGPT Pro",
            project_type="game", user_prompt="A solo zombie horror game", project_data={},
        )
        self.assertEqual(metadata["available_capacity_hours"], 270)
        self.assertEqual(len(output.roadmap), 3)
        self.assertEqual(metadata["roadmap_period_unit"], "month")
        self.assertLessEqual(output.roadmap_simulator.planned_hours, 270)
        self.assertIn("Game Design", output.production_flow_map)
        self.assertIn("Assets/Scripts/", output.project_structure)
        self.assertTrue(all(task.title and task.name == task.title for task in output.task_breakdown.detailed_tasks))
        self.assertIn("Unity", output.task_breakdown.tools_guide)
        self.assertIn("Blender", output.task_breakdown.tools_guide)

    def test_saas_plan_is_not_a_game_plan(self):
        output, metadata = build_atlas_plan(
            project_id="atlas-saas", project_title="Billing SaaS", duration="3 weeks",
            team_size=2, hours_per_day=4, tools="React, FastAPI, Supabase",
            project_type="saas", user_prompt="Subscription billing dashboard", project_data={},
        )
        self.assertEqual(metadata["available_capacity_hours"], 168)
        self.assertEqual(len(output.roadmap), 3)
        self.assertIn("Backend", output.production_flow_map)
        self.assertIn("frontend/", output.project_structure)
        self.assertNotIn("Game Design", output.production_flow_map)


if __name__ == "__main__":
    unittest.main()
