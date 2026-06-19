"""Deterministic, input-driven Atlas production planning engine."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from backend.models.output_models import (
    AtlasDetailedTask,
    AtlasOutput,
    AtlasPhase,
    AtlasRisk,
    AtlasSimulation,
    AtlasTaskBreakdown,
)


@dataclass(frozen=True)
class DurationSpec:
    value: int
    unit: str
    total_days: int
    period_label: str
    period_count: int


PROJECT_PROFILES = {
    "game": {
        "phases": [
            "Preproduction", "Gameplay Systems", "Art Production",
            "Level Design", "Testing", "Release",
        ],
        "flow": [
            "Idea", "Game Design", "Core Systems", "Art Production",
            "Level Design", "QA", "Release",
        ],
        "tasks": [
            "Define the playable MVP and acceptance criteria",
            "Document the core loop, controls, win state, and fail state",
            "Create the project and configure target-platform settings",
            "Build player input, movement, and camera",
            "Implement the primary interaction or combat loop",
            "Implement game state, health, failure, and restart",
            "Prototype enemy, hazard, or challenge behaviour",
            "Block out the main playable level",
            "Create character and equipment production assets",
            "Create environment props and materials",
            "Integrate animation, feedback, and visual effects",
            "Implement HUD, menus, and interaction prompts",
            "Add audio cues, ambience, and mix",
            "Assemble a start-to-finish playable build",
            "Run gameplay, balance, and usability testing",
            "Fix blockers and profile performance",
            "Configure release build and export",
        ],
        "folders": [
            "Assets/", "Assets/Scripts/", "Assets/Prefabs/", "Assets/Scenes/",
            "Assets/Characters/", "Assets/Environment/", "Assets/Animations/",
            "Assets/Audio/", "Assets/UI/", "Builds/", "Docs/",
        ],
        "risks": [
            ("Asset Production Delays", "Art assets arrive after integration begins"),
            ("AI Behaviour Bugs", "Enemy or challenge states become unreliable"),
            ("Performance Problems", "The playable scene misses the target frame rate"),
            ("Core Loop Instability", "The main interaction is not fun or reliable"),
            ("Level Scope Growth", "The level expands beyond available production hours"),
            ("Build Regression", "The exported build differs from editor behaviour"),
        ],
    },
    "saas": {
        "phases": ["Research", "Architecture", "Backend", "Frontend", "Testing", "Launch"],
        "flow": ["Idea", "Requirements", "Architecture", "Backend", "Frontend", "Testing", "Launch"],
        "tasks": [
            "Define users, problem statement, and measurable MVP outcome",
            "Document functional requirements and scope exclusions",
            "Design domain model and service boundaries",
            "Create application workspace and environment configuration",
            "Design database schema and migration strategy",
            "Implement authentication and authorization rules",
            "Implement core backend services and API contracts",
            "Implement validation, error handling, and observability",
            "Build the frontend shell and navigation",
            "Implement the primary user workflow",
            "Connect frontend state to backend APIs",
            "Implement responsive states, loading, and recovery UX",
            "Test API contracts and critical user journeys",
            "Review security, privacy, and data access controls",
            "Prepare production configuration and deployment",
            "Run launch verification and monitoring checks",
        ],
        "folders": [
            "frontend/", "frontend/src/", "frontend/src/components/",
            "frontend/src/pages/", "backend/", "backend/api/", "backend/services/",
            "database/", "database/migrations/", "tests/", "docs/",
        ],
        "risks": [
            ("API Failures", "Critical frontend workflows cannot complete"),
            ("Database Scaling", "Queries or schema choices degrade under growth"),
            ("Security Issues", "Authentication or authorization exposes protected data"),
            ("Integration Drift", "Frontend and backend contracts diverge"),
            ("Deployment Configuration", "Production variables differ from tested settings"),
            ("Scope Creep", "Secondary workflows displace the MVP outcome"),
        ],
    },
    "mobile": {
        "phases": ["Research", "UX", "Development", "Testing", "Store Release"],
        "flow": ["Idea", "User Research", "UX Design", "App Development", "Device Testing", "Store Release"],
        "tasks": [
            "Define target users, devices, and MVP outcome",
            "Map the primary mobile journey and scope exclusions",
            "Create wireframes and interaction states",
            "Define navigation and application architecture",
            "Create the mobile project and build configurations",
            "Implement the design system and reusable components",
            "Implement the primary user workflow",
            "Implement local state, persistence, and recovery",
            "Integrate required services and APIs",
            "Handle permissions, offline states, and device constraints",
            "Test accessibility and responsive device layouts",
            "Test on target devices and OS versions",
            "Profile startup, memory, battery, and network use",
            "Prepare store assets, privacy details, and release build",
            "Complete store submission and release verification",
        ],
        "folders": [
            "app/", "app/screens/", "app/components/", "app/navigation/",
            "app/services/", "app/state/", "app/assets/", "app/tests/",
            "android/", "ios/", "store-assets/", "docs/",
        ],
        "risks": [
            ("Device Fragmentation", "Layouts or features fail on target devices"),
            ("Store Rejection", "Submission metadata or policies block release"),
            ("Permission Failures", "Required device capabilities are unavailable"),
            ("Offline Data Loss", "Interrupted sessions lose user state"),
            ("Performance Problems", "Startup, memory, or battery use is excessive"),
            ("API Reliability", "Mobile workflows fail on unstable networks"),
        ],
    },
    "web": {
        "phases": ["Research", "UX", "Architecture", "Development", "Testing", "Launch"],
        "flow": ["Idea", "Requirements", "UX Design", "Architecture", "Development", "Testing", "Launch"],
        "tasks": [
            "Define audience, goals, and success criteria",
            "Map pages, content, and primary user journey",
            "Create responsive wireframes and component inventory",
            "Choose application architecture and data boundaries",
            "Create the project and environment configuration",
            "Build layout, navigation, and design tokens",
            "Implement primary pages and components",
            "Implement data access and application state",
            "Add forms, validation, and error recovery",
            "Test responsive, accessibility, and browser behaviour",
            "Optimize loading, assets, and runtime performance",
            "Configure deployment, analytics, and monitoring",
            "Run production smoke tests and launch",
        ],
        "folders": [
            "frontend/", "frontend/src/", "frontend/src/components/",
            "frontend/src/pages/", "frontend/src/services/", "api/",
            "database/", "public/", "tests/", "docs/",
        ],
        "risks": [
            ("Browser Compatibility", "Critical interactions differ across browsers"),
            ("API Failures", "Dynamic content or forms cannot complete"),
            ("Accessibility Gaps", "The primary journey excludes users"),
            ("Performance Problems", "Slow loading damages conversion or usability"),
            ("Security Issues", "Forms or sessions expose application data"),
            ("Deployment Regression", "Production behaviour differs from local testing"),
        ],
    },
    "general": {
        "phases": ["Research", "Planning", "Production", "Integration", "Validation", "Release"],
        "flow": ["Idea", "Requirements", "Plan", "Production", "Integration", "Validation", "Release"],
        "tasks": [
            "Define the project outcome and acceptance criteria",
            "Document scope, constraints, and exclusions",
            "Design the production workflow and deliverable structure",
            "Create the project workspace and conventions",
            "Produce the first critical deliverable",
            "Produce supporting project components",
            "Integrate components into a complete working result",
            "Review quality against acceptance criteria",
            "Resolve blockers and production defects",
            "Prepare final documentation and handoff",
            "Package and release the completed project",
        ],
        "folders": ["src/", "assets/", "deliverables/", "tests/", "docs/", "releases/"],
        "risks": [
            ("Scope Creep", "Unplanned work consumes delivery capacity"),
            ("Integration Failure", "Components do not form a complete result"),
            ("Quality Regression", "Late changes break accepted work"),
            ("Dependency Delay", "Required inputs arrive after scheduled production"),
            ("Capacity Overrun", "Planned work exceeds available hours"),
            ("Release Readiness", "Documentation or packaging blocks delivery"),
        ],
    },
}


TOOL_RULES = {
    "unity": {
        "tasks": ["Configure Unity project, Input System, scenes, and build target", "Implement Unity gameplay scripts, UI, and build export"],
        "folders": ["Assets/Scripts/", "Assets/Prefabs/", "Assets/Scenes/", "Assets/Audio/", "Assets/Animations/", "Assets/UI/"],
    },
    "blender": {
        "tasks": ["Create Blender characters, equipment, props, and environment assets", "Export optimized Blender assets and validate engine imports"],
        "folders": ["Art/Blender/", "Art/Exports/", "Assets/Models/", "Assets/Textures/"],
    },
    "claude code": {
        "tasks": ["Use Claude Code for scoped architecture, implementation, debugging, and documentation reviews"],
        "folders": ["docs/architecture/", "docs/debugging/"],
    },
    "antigravity": {
        "tasks": ["Use Antigravity IDE to organize the codebase, workflow, task execution, and validation"],
        "folders": [".agents/", "docs/workflows/"],
    },
    "chatgpt": {
        "tasks": ["Use ChatGPT for design exploration, planning, documentation, and launch messaging"],
        "folders": ["docs/design/", "docs/marketing/"],
    },
    "react": {
        "tasks": ["Create React component architecture and application state", "Implement responsive React pages and API integration"],
        "folders": ["frontend/src/components/", "frontend/src/pages/", "frontend/src/hooks/"],
    },
    "fastapi": {
        "tasks": ["Define FastAPI contracts, validation models, and service routes", "Test FastAPI error handling and production configuration"],
        "folders": ["backend/api/", "backend/models/", "backend/services/"],
    },
    "supabase": {
        "tasks": ["Design Supabase schema, migrations, authentication, and row-level security"],
        "folders": ["supabase/migrations/", "supabase/policies/"],
    },
    "flutter": {
        "tasks": ["Create Flutter navigation, widgets, state, and platform builds"],
        "folders": ["lib/screens/", "lib/widgets/", "lib/services/", "test/"],
    },
    "react native": {
        "tasks": ["Create React Native navigation, screens, native integrations, and builds"],
        "folders": ["src/screens/", "src/components/", "src/native/"],
    },
}


def parse_duration(duration: str) -> DurationSpec:
    match = re.fullmatch(r"\s*(\d+)\s*(day|week|month|year)s?\s*", duration.lower())
    if not match:
        raise ValueError("Duration must use the format '<number> days|weeks|months|years'.")
    value = int(match.group(1))
    if value < 1:
        raise ValueError("Duration must be at least one day.")
    unit = match.group(2)
    total_days = value * {"day": 1, "week": 7, "month": 30, "year": 365}[unit]
    if unit == "day":
        return DurationSpec(value, unit, total_days, "Day", value)
    if unit == "week" and value == 1:
        return DurationSpec(value, unit, total_days, "Day", 7)
    if unit == "week":
        return DurationSpec(value, unit, total_days, "Week", value)
    if unit == "month":
        return DurationSpec(value, unit, total_days, "Month", value)
    quarters = max(1, value * 4)
    return DurationSpec(value, unit, total_days, "Quarter", quarters)


def split_tools(tools: str) -> list[str]:
    values = [item.strip() for item in re.split(r"[,;\n/]+", tools) if item.strip()]
    if not values:
        raise ValueError("At least one tool or technology is required.")
    return list(dict.fromkeys(values))


def infer_project_type(explicit_type: str, title: str, prompt: str, tools: str, project_data: dict) -> str:
    explicit = (explicit_type or "").strip().lower()
    aliases = {
        "game": "game", "video game": "game", "saas": "saas",
        "mobile": "mobile", "mobile app": "mobile", "web": "web",
        "web app": "web", "website": "web", "general": "general",
    }
    if explicit in aliases:
        return aliases[explicit]
    haystack = " ".join([
        title, prompt, tools, str(project_data.get("gameplay") or ""),
        str(project_data.get("documentation") or ""),
    ]).lower()
    if any(word in haystack for word in ("unity", "unreal", "godot", "game", "gameplay", "horror", "rpg")):
        return "game"
    if any(word in haystack for word in ("flutter", "react native", "android", "ios", "mobile app")):
        return "mobile"
    if any(word in haystack for word in ("saas", "subscription", "dashboard", "multi-tenant")):
        return "saas"
    if any(word in haystack for word in ("react", "website", "web app", "frontend", "fastapi")):
        return "web"
    return "general"


def _owner(index: int, team_size: int, project_type: str) -> str:
    if team_size == 1:
        return "Solo Developer"
    roles = {
        "game": ["Producer", "Gameplay Developer", "Technical Artist", "QA"],
        "saas": ["Product Lead", "Backend Developer", "Frontend Developer", "QA"],
        "mobile": ["Product Lead", "Mobile Developer", "UX Designer", "QA"],
        "web": ["Product Lead", "Web Developer", "UX Designer", "QA"],
        "general": ["Project Lead", "Producer", "Specialist", "QA"],
    }[project_type]
    return roles[index % min(team_size, len(roles))]


def _tool_rule(tool: str) -> dict:
    lower = tool.lower()
    for key, rule in TOOL_RULES.items():
        if key in lower:
            return rule
    return {
        "tasks": [f"Configure {tool} and use it for its assigned production deliverables"],
        "folders": [f"tools/{re.sub(r'[^a-z0-9]+', '-', lower).strip('-')}/"],
    }


def _tools_guide(tools: list[str], project_type: str) -> dict[str, str]:
    guide = {}
    for tool in tools:
        rule = _tool_rule(tool)
        work = "; ".join(rule["tasks"])
        guide[tool] = (
            f"**Setup:** Configure {tool} for the selected {project_type} project and target release environment.\n"
            f"**Production work:** {work}.\n"
            "**Handoff:** Record naming, paths, versions, import/export settings, and acceptance checks.\n"
            "**Validation:** Review generated or assisted work in the actual production runtime before marking its task complete."
        )
    return guide


def _allocate_hours(count: int, capacity: float) -> list[float]:
    planned = round(capacity * 0.9, 2)
    weights = [1 + (index % 4) * 0.35 for index in range(count)]
    unit = planned / sum(weights)
    hours = [round(max(0.01, unit * weight), 2) for weight in weights]
    hours[-1] = round(max(0.01, hours[-1] + planned - sum(hours)), 2)
    return hours


def _phase_name(spec: DurationSpec, index: int, phase: str) -> str:
    return f"{spec.period_label} {index}: {phase}"


def _completion_probability(planned: float, available: float, risk_count: int) -> float:
    utilization = planned / available if available else 10
    base = 96 - max(0, utilization - 0.75) * 80 - risk_count * 0.6
    return round(max(5, min(98, base)), 1)


def build_atlas_plan(
    *,
    project_id: str,
    project_title: str,
    duration: str,
    team_size: int,
    hours_per_day: float,
    tools: str,
    project_type: str,
    user_prompt: str,
    project_data: dict,
) -> tuple[AtlasOutput, dict]:
    if team_size < 1:
        raise ValueError("Team size must be at least 1.")
    if hours_per_day <= 0 or hours_per_day > 24:
        raise ValueError("Hours per day must be greater than 0 and no more than 24.")

    spec = parse_duration(duration)
    tool_list = split_tools(tools)
    normalized_type = infer_project_type(
        project_type, project_title, user_prompt, tools, project_data
    )
    profile = PROJECT_PROFILES[normalized_type]
    available = round(spec.total_days * team_size * hours_per_day, 2)

    task_names = list(profile["tasks"])
    tool_task_names: list[str] = []
    folders = list(profile["folders"])
    for tool in tool_list:
        rule = _tool_rule(tool)
        tool_task_names.extend(rule["tasks"])
        folders.extend(rule["folders"])
    task_names.extend(tool_task_names)

    # More capacity permits finer decomposition; small projects remain compact.
    target_count = max(8, min(len(task_names), int(math.sqrt(available)) + 6))
    if target_count < len(task_names):
        core_count = max(5, target_count - len(tool_task_names))
        task_names = task_names[:core_count] + tool_task_names
    task_names = list(dict.fromkeys(task_names))
    hours = _allocate_hours(len(task_names), available)

    detailed_tasks = []
    for index, (name, task_hours) in enumerate(zip(task_names, hours), 1):
        task_id = f"TSK-{index:03d}"
        dependencies = [] if index == 1 else [f"TSK-{index - 1:03d}"]
        detailed_tasks.append(AtlasDetailedTask(
            id=task_id,
            title=name,
            name=name,
            hours=task_hours,
            priority="Critical" if index <= max(3, len(task_names) // 2) or index == len(task_names) else "High",
            dependencies=dependencies,
            dependency=dependencies[0] if dependencies else "",
            status="Not Started",
            owner=_owner(index - 1, team_size, normalized_type),
            critical_path=index <= max(3, len(task_names) // 2) or index == len(task_names),
        ))

    buckets: list[list[AtlasDetailedTask]] = [[] for _ in range(spec.period_count)]
    for index, task in enumerate(detailed_tasks):
        bucket_index = min(spec.period_count - 1, index * spec.period_count // len(detailed_tasks))
        buckets[bucket_index].append(task)

    roadmap = []
    for index, bucket in enumerate(buckets, 1):
        profile_index = min(
            len(profile["phases"]) - 1,
            (index - 1) * len(profile["phases"]) // spec.period_count,
        )
        phase = profile["phases"][profile_index]
        roadmap.append(AtlasPhase(
            name=_phase_name(spec, index, phase),
            period=index,
            period_unit=spec.period_label.lower(),
            phase=phase,
            objectives=[task.title for task in bucket[:2]],
            tasks=[f"{task.id} — {task.title} ({task.hours}h)" for task in bucket],
            hours=round(sum(task.hours for task in bucket), 2),
            deliverables=[f"{phase} deliverables accepted for {project_title}"],
            milestones=[f"{spec.period_label} {index} review completed"],
        ))

    planned = round(sum(task.hours for task in detailed_tasks), 2)
    probability = _completion_probability(planned, available, len(profile["risks"]))
    utilization = planned / available if available else 1
    status = "ON TRACK" if utilization <= 0.9 else "AT RISK" if utilization <= 1 else "HIGH RISK"

    risks = []
    risk_specs = profile["risks"] + [
        ("Technology Learning Curve", f"Selected tools slow production: {', '.join(tool_list)}"),
        ("Capacity Margin", "Unexpected rework consumes the planned capacity buffer"),
    ]
    for index, (title, risk) in enumerate(risk_specs, 1):
        blocked_index = min(len(detailed_tasks), max(1, math.ceil(index * len(detailed_tasks) / len(risk_specs))))
        blocked_task = detailed_tasks[blocked_index - 1]
        risks.append(AtlasRisk(
            id=f"RSK-{index:03d}",
            title=title,
            category=normalized_type,
            blocked_task=blocked_task.id,
            blocked_by=blocked_task.dependencies,
            risk=risk,
            description=risk,
            impact="High" if index <= 3 else "Medium",
            severity="High" if index <= 3 else "Medium",
            probability="Medium",
            mitigation=f"Review {blocked_task.id} at the preceding milestone, time-box rework, and protect the capacity buffer.",
        ))

    structure = list(dict.fromkeys([f"{project_title}/"] + folders + ["README.md"]))
    output = AtlasOutput(
        project_id=project_id,
        roadmap=roadmap,
        project_structure=structure,
        production_flow_map=list(profile["flow"]),
        dependency_map=[
            f"{dependency} -> {task.id}"
            for task in detailed_tasks for dependency in task.dependencies
        ],
        task_breakdown=AtlasTaskBreakdown(
            critical_tasks=[f"{task.id} — {task.title}" for task in detailed_tasks if task.critical_path],
            optional_tasks=[],
            future_expansion=[],
            detailed_tasks=detailed_tasks,
            tools_guide=_tools_guide(tool_list, normalized_type),
        ),
        risks=risks,
        roadmap_simulator=AtlasSimulation(
            available_hours=available,
            planned_hours=planned,
            completion_probability=probability,
            status=status,
            explanation=(
                f"{planned} planned hours use {round(utilization * 100, 1)}% of "
                f"{available} available hours, leaving {round(available - planned, 2)} hours."
            ),
        ),
    )
    metadata = {
        "project_type": normalized_type,
        "user_prompt": user_prompt,
        "tools_list": tool_list,
        "duration_value": spec.value,
        "duration_unit": spec.unit,
        "roadmap_period_unit": spec.period_label.lower(),
        "roadmap_period_count": spec.period_count,
        "total_days": spec.total_days,
        "working_hours": round(spec.total_days * hours_per_day, 2),
        "available_capacity_hours": available,
        "planned_hours": planned,
        "completion_probability": probability,
        "status": status,
    }
    validate_atlas_plan(output, metadata)
    return output, metadata


def validate_atlas_plan(output: AtlasOutput, metadata: dict) -> None:
    errors: list[str] = []
    tasks = output.task_breakdown.detailed_tasks
    task_ids = {task.id for task in tasks}
    planned = round(sum(task.hours for task in tasks), 2)
    available = metadata["available_capacity_hours"]

    if len(output.roadmap) != metadata["roadmap_period_count"]:
        errors.append("roadmap period count does not match duration")
    if planned > available + 0.01:
        errors.append("planned task hours exceed available capacity")
    if abs(planned - output.roadmap_simulator.planned_hours) > 0.01:
        errors.append("simulator planned hours do not equal task hours")
    if abs(available - output.roadmap_simulator.available_hours) > 0.01:
        errors.append("simulator available hours do not equal calculated capacity")
    if any(not task.title or task.name != task.title for task in tasks):
        errors.append("task titles are missing or inconsistent")
    for index, task in enumerate(tasks):
        earlier = {item.id for item in tasks[:index]}
        if any(dep not in task_ids or dep not in earlier for dep in task.dependencies):
            errors.append(f"{task.id} contains an invalid dependency")
    guide_keys = {key.lower() for key in (output.task_breakdown.tools_guide or {})}
    if any(tool.lower() not in guide_keys for tool in metadata["tools_list"]):
        errors.append("one or more selected technologies are missing from the plan")
    if not output.production_flow_map or not output.project_structure:
        errors.append("flow map or project structure is empty")
    roadmap_text = " ".join(task for phase in output.roadmap for task in phase.tasks)
    if any(task.id not in roadmap_text for task in tasks):
        errors.append("one or more tasks are not scheduled in the roadmap")
    if errors:
        raise ValueError("Atlas validation failed: " + "; ".join(errors))
