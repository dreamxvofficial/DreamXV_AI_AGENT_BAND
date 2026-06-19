from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import os
import sys
import traceback
import uuid
import zipfile
import io
import json
import base64

# Ensure backend package can be imported by adding the root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.supabase_service import SupabaseService
from backend.models.output_models import (
    AtlasArtConcept, AtlasDetailedTask, AtlasOutput, AtlasPhase, AtlasRisk,
    AtlasSimulation, AtlasTaskBreakdown,
)
from backend.services.atlas_planning_service import build_atlas_plan, parse_duration

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = SupabaseService()

ATLAS_STAGES = [
    "roadmap", "tasks", "structure", "flow_map", "risk_dashboard",
    "simulation", "tools_integration", "export",
]

class AtlasRequest(BaseModel):
    project_id: str
    project_title: Optional[str] = None
    duration: str
    tools: str
    team_size: Optional[int] = 1
    hours_per_day: Optional[float] = 8.0
    project_type: Optional[str] = None
    user_prompt: Optional[str] = None
    atlas_id: Optional[str] = None  # Optional parameter to allow regeneration in-place

class DuplicateRequest(BaseModel):
    atlas_id: str

def generate_tools_guide(tools_str: str) -> dict[str, str]:
    import re
    tools_list = [t.strip() for t in re.split(r'[,;/]', tools_str) if t.strip()]
    if not tools_list:
        tools_list = [t.strip() for t in tools_str.split() if t.strip()]
        
    guide = {}
    for tool in tools_list:
        lower_tool = tool.lower()
        if "unity" in lower_tool:
            guide[tool] = (
                "**Unity Configuration & Integration:**\n"
                "1. **Project Setup:** Initialize the project using the 3D Core or Universal Render Pipeline (URP) template.\n"
                "2. **Package Management:** Install Input System and Cinemachine via Package Manager.\n"
                "3. **Scene Layout:** Configure the core scene layout with a main character Prefab, virtual camera, and basic level colliders.\n"
                "4. **Script Integration:** Bind C# controllers to character physics components and trigger events."
            )
        elif "blender" in lower_tool:
            guide[tool] = (
                "**Blender Asset Creation & Export Pipeline:**\n"
                "1. **Modeling & Scale:** Design game models and rigs ensuring the unit scale is set to metric (1 unit = 1 meter) for perfect compatibility.\n"
                "2. **Export Settings:** Export assets to FBX format with default forward/up axis configurations.\n"
                "3. **Texturing:** Generate UV maps and pack textures for material baking before importing files into the engine's assets directory."
            )
        elif "claude code" in lower_tool:
            guide[tool] = (
                "**Claude Code AI Agent Assistant Workflows:**\n"
                "1. **CLI Integration:** Execute code analysis and refactoring tasks directly from your CLI terminal.\n"
                "2. **Gameplay Scripts:** Generate narrowly scoped C# controllers and ScriptableObject definitions from approved mechanic specifications.\n"
                "3. **Engine Validation:** Review generated code in Unity, attach it to test prefabs, and verify behavior in Play Mode before integration."
            )
        elif "antigravity" in lower_tool:
            guide[tool] = (
                "**Antigravity IDE Development Suite:**\n"
                "1. **Multi-Agent Orchestration:** Use built-in agent orchestrators to parallelize design and code validation workflows.\n"
                "2. **Sandbox Execution:** Run local debug commands and verify file generation steps securely.\n"
                "3. **Production Tracking:** Keep task IDs, Unity asset paths, scene ownership, and milestone checklists aligned with the Atlas plan."
            )
        elif "chatgpt" in lower_tool:
            guide[tool] = (
                "**ChatGPT Pro Design Assistant:**\n"
                "1. **Design Documenting:** Draft the Game Design Document (GDD) and expand narrative lore, dialogue logs, and level descriptions.\n"
                "2. **Content Design:** Draft compact quests, encounters, item descriptions, and tutorial text that fit the MVP scope.\n"
                "3. **Review:** Critique balance tables, playtest notes, store copy, and trailer/marketing concepts without expanding committed scope."
            )
        elif "react" in lower_tool:
            guide[tool] = (
                "**React Frontend Integration:**\n"
                "1. **Boilerplate Setup:** Bootstrapped via Vite with React-Router and global state provider mechanisms.\n"
                "2. **Component Architecture:** Build highly responsive dashboard views with clean modular layout containers.\n"
                "3. **API Hooks:** Implement Axios or Fetch clients encapsulated inside custom React hooks for real-time dashboard data sync."
            )
        elif "fastapi" in lower_tool:
            guide[tool] = (
                "**FastAPI Backend Architecture:**\n"
                "1. **App Routing:** Define modular APIRouters for authentication, projects, and plans endpoints.\n"
                "2. **Pydantic Validation:** Formulate robust input/output schemas matching SQL models to prevent runtime exceptions.\n"
                "3. **CORS & Middleware:** Configure global CORS middleware and logging intercepts to support cross-origin frontend requests."
            )
        elif "supabase" in lower_tool:
            guide[tool] = (
                "**Supabase Database & Auth Service:**\n"
                "1. **Database Schema:** Create relational tables, foreign key constraints, and dynamic triggers for live status updates.\n"
                "2. **Auth Mechanisms:** Implement SignUp/LogIn flows utilizing Supabase's native JWT validation and session persistence.\n"
                "3. **RLS Policies:** Apply Row Level Security (RLS) policies to protect user-specific project data from unauthorized reads/writes."
            )
        else:
            guide[tool] = (
                f"**{tool} Utilization Guide:**\n"
                "1. **Configuration:** Configure project units, naming, export paths, and target-platform settings to match the selected game engine.\n"
                "2. **Production Use:** Assign it only the game assets or gameplay work it directly supports in the roadmap.\n"
                "3. **Handoff & Validation:** Document import/export settings and verify every output inside the playable engine scene before acceptance."
            )
    return guide

def get_atlas_fallback(project_id: str, duration: str, tools: str) -> AtlasOutput:
    # Handle environment styling check for fallback
    is_web = any(term in tools.lower() for term in ["web", "react", "html", "css", "node", "django", "fastapi", "flask", "js", "ts", "supabase"])
    
    if is_web:
        return AtlasOutput(
            project_id=project_id,
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
                tools_guide=generate_tools_guide(tools)
            )
        )
    else:
        return AtlasOutput(
            project_id=project_id,
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
                tools_guide=generate_tools_guide(tools)
            )
        )

def compile_markdown_files(title: str, atlas_out: AtlasOutput) -> dict:
    # 1. README.md
    readme = f"# {title} — Production Plan\n\n"
    readme += "Generated by DreamXV Atlas AI Planner.\n\n"
    readme += "This archive contains the complete production layout, development roadmap, workflow maps, and source directories.\n"
    
    # 2. Roadmap.md
    roadmap_md = "# Development Roadmap\n\n"
    for phase in (atlas_out.roadmap or []):
        roadmap_md += f"## {phase.name}\n"
        for task in (phase.tasks or []):
            roadmap_md += f"- [ ] {task}\n"
        roadmap_md += "\n"
        
    # 3. Tasks.md
    tasks_md = "# Project Tasks\n\n"
    tb = atlas_out.task_breakdown
    crit = tb.critical_tasks or []
    opt = tb.optional_tasks or []
    exp = tb.future_expansion or []
    
    tasks_md += "## Critical Path Tasks (MVP)\n"
    for t in crit:
        tasks_md += f"- [ ] {t}\n"
    tasks_md += "\n## Optional Tasks\n"
    for t in opt:
        tasks_md += f"- [ ] {t}\n"
    tasks_md += "\n## Future Expansion\n"
    for t in exp:
        tasks_md += f"- [ ] {t}\n"
    if tb.detailed_tasks:
        tasks_md += "\n## Estimated Task Register\n"
        for task in tb.detailed_tasks:
            deps = ", ".join(task.dependencies) or "None"
            tasks_md += (
                f"- [ ] {task.id} — {task.name} | {task.hours}h | {task.priority} | "
                f"Owner: {task.owner} | Dependencies: {deps} | Critical: {task.critical_path}\n"
            )
        
    # 4. FlowMap.md
    flow_md = "# Production Workflow & Dependencies\n\n"
    flow_md += "## Step-by-Step Workflow\n"
    flow_steps = atlas_out.production_flow_map or []
    for idx, step in enumerate(flow_steps):
        flow_md += f"{idx + 1}. {step}\n"
    flow_md += "\n## Core Dependency Graph\n"
    dep_map = atlas_out.dependency_map or []
    for dep in dep_map:
        flow_md += f"- {dep}\n"
        
    # 5. Structure.md
    struct_md = "# Project Directory Structure\n\n"
    struct_md += "Below is the folder and file layout designed for this project:\n\n```\n"
    struct_list = atlas_out.project_structure or []
    struct_md += "\n".join(struct_list)
    struct_md += "\n```\n"
    
    return {
        "README.md": readme,
        "Roadmap.md": roadmap_md,
        "FlowMap.md": flow_md,
        "Tasks.md": tasks_md,
        "Structure.md": struct_md
    }

def create_atlas_zip_on_disk(atlas_id: str, atlas_data: dict, images: list[dict]) -> str:
    # Try writing to public/exports/atlas/ first, fallback to /tmp/ if read-only
    zip_dir = "public/exports/atlas"
    try:
        os.makedirs(zip_dir, exist_ok=True)
        zip_path = f"{zip_dir}/{atlas_id}.zip"
        # Test write capability
        with open(zip_path, "wb") as f:
            f.write(b"")
    except Exception:
        zip_dir = "/tmp"
        os.makedirs(zip_dir, exist_ok=True)
        zip_path = f"{zip_dir}/{atlas_id}.zip"

    with open(zip_path, "wb") as f_out:
        with zipfile.ZipFile(f_out, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # 1. /docs/ README, Roadmap, FlowMap, Tasks, Structure
            gen_files = atlas_data.get("generated_files") or {}
            for name, content in gen_files.items():
                zip_file.writestr(f"docs/{name}", content or "")
                
            # 2. /art/ AI images
            for idx, img in enumerate(images):
                img_url = img.get("image_url", "")
                if not img_url:
                    continue
                img_bytes = None
                if img_url.startswith("data:image/"):
                    try:
                        header, encoded = img_url.split(",", 1)
                        img_bytes = base64.b64decode(encoded)
                    except Exception as e:
                        print(f"Error decoding base64 image {idx}: {e}")
                elif img_url.startswith("http://") or img_url.startswith("https://"):
                    try:
                        import urllib.request
                        with urllib.request.urlopen(img_url, timeout=10) as response:
                            img_bytes = response.read()
                    except Exception as e:
                        print(f"Error downloading image {idx} from URL: {e}")
                else:
                    try:
                        if os.path.exists(img_url):
                            with open(img_url, "rb") as img_f:
                                img_bytes = img_f.read()
                    except Exception as e:
                        print(f"Error reading image {idx} from path: {e}")
                
                if img_bytes:
                    zip_file.writestr(f"art/concept_{idx+1}.png", img_bytes)
                        
            # 3. /project_structure/ Generated empty folders
            project_structure = atlas_data.get("structure") or []
            for path in project_structure:
                cleaned_path = path.strip()
                if cleaned_path.endswith("/"):
                    zip_file.writestr(f"project_structure/{cleaned_path}", "")
                # Planned files are documented in Structure.md; do not create fake source/assets.
                    
            # 4. metadata.json
            metadata = {
                "atlas_id": atlas_id,
                "source_project_id": atlas_data.get("source_project_id"),
                "title": atlas_data.get("title"),
                "duration": atlas_data.get("duration"),
                "tools": atlas_data.get("tools"),
                "created_at": str(atlas_data.get("created_at") or "")
            }
            zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))
            
    return zip_path

def parse_duration_to_days(duration: str) -> int:
    """Parse a supported duration into approximate calendar days."""
    try:
        return parse_duration(duration).total_days
    except Exception:
        return 0


def build_dynamic_game_fallback(
    project_data: dict, duration: str, tools: str, team_size: int, hours_per_day: float
) -> AtlasOutput:
    """Capacity-safe game-production plan used when structured generation is unavailable."""
    title = project_data.get("title") or "Untitled Game"
    gameplay = project_data.get("gameplay") or {}
    mechanics = gameplay.get("mechanics") or []
    if isinstance(mechanics, str):
        mechanics = [m.strip() for m in mechanics.split(",") if m.strip()]
    mechanic = mechanics[0] if mechanics else (gameplay.get("core_loop") or "core gameplay loop")
    days = max(1, parse_duration_to_days(duration))
    capacity = round(max(0.1, team_size * hours_per_day * days), 2)

    task_names = [
        "Lock MVP player fantasy and success condition", "Define playable loop and scope cuts",
        "Create engine project and render settings", "Establish input actions and test scene",
        "Implement player locomotion", "Implement gameplay camera", f"Prototype {mechanic}",
        "Implement health, damage, and fail state", "Create primary equipment interaction",
        "Add feedback for hits and interactions", "Block out the playable level",
        "Set navigation and collision boundaries", "Create enemy or challenge behavior",
        "Implement detection and engagement states", "Create encounter spawn and reset flow",
        "Implement pickups and rewards", "Implement lightweight inventory or loadout",
        "Add MVP progression reward", "Model primary character silhouette", "Create gameplay equipment assets",
        "Create modular environment props", "UV and texture MVP assets", "Import and configure game assets",
        "Assemble environment composition", "Configure lighting and atmosphere", "Create HUD information hierarchy",
        "Implement HUD and interaction prompts", "Create pause, restart, and completion screens",
        "Add movement, action, and impact audio", "Add ambient audio and mix", "Integrate complete start-to-finish session",
        "Conduct focused gameplay playtest", "Fix blockers and tune difficulty", "Profile and optimize MVP scene",
        "Configure target build and export playable MVP",
    ]
    weights = [1,1,1,1,3,2,4,2,2,2,3,1,3,2,1,1,2,1,2,2,2,2,2,3,2,2,2,1,2,1,3,2,3,2,1]
    planned_target = round(capacity * 0.9, 2)
    unit = planned_target / sum(weights)
    task_hours = [max(0.01, round(w * unit, 2)) for w in weights]
    drift = round(sum(task_hours) - planned_target, 2)
    if drift:
        task_hours[6] = round(max(0.01, task_hours[6] - drift), 2)

    owner = "Solo Developer" if team_size == 1 else "Game Development Team"
    detailed = []
    for i, (name, hours) in enumerate(zip(task_names, task_hours), 1):
        deps = [] if i <= 2 else [f"TSK-{max(1, i - 1):03d}"]
        detailed.append(AtlasDetailedTask(
            id=f"TSK-{i:03d}", name=name, hours=hours,
            priority="Critical" if i <= 18 or i >= 31 else "High",
            dependencies=deps, status="Not Started", owner=owner,
            critical_path=i <= 18 or i >= 31,
        ))

    import re
    match = re.search(r"(\d+)\s*(day|week|month|year)s?", duration.lower())
    count, unit_name = (int(match.group(1)), match.group(2)) if match else (1, "week")
    phase_count = count if unit_name in ("week", "month", "year") else max(1, (count + 6) // 7)
    label = {"week": "Week", "month": "Month", "year": "Year"}.get(unit_name, "Week")
    buckets = [[] for _ in range(phase_count)]
    for i, task in enumerate(detailed):
        buckets[min(phase_count - 1, i * phase_count // len(detailed))].append(task)
    roadmap = []
    for i, bucket in enumerate(buckets, 1):
        roadmap.append(AtlasPhase(
            name=f"{label} {i}",
            objectives=[bucket[0].name, bucket[-1].name] if bucket else [],
            tasks=[f"{t.id} — {t.name} ({t.hours}h)" for t in bucket],
            hours=round(sum(t.hours for t in bucket), 2),
            deliverables=[f"Integrated {label.lower()} {i} gameplay increment"],
            milestones=[f"{title}: {label} {i} build verified in engine"],
        ))

    risks = []
    risk_specs = [
        ("Core loop integration", 7, [5, 6]), ("Level blocked by controller", 11, [5, 6]),
        ("Challenge behavior instability", 13, [8, 12]), ("Encounter reset failure", 15, [13, 14]),
        ("Reward loop disconnect", 18, [16, 17]), ("Asset import mismatch", 23, [19, 20, 21, 22]),
        ("Environment readability", 24, [11, 23]), ("HUD lacks gameplay state", 27, [8, 16, 26]),
        ("Audio feedback arrives late", 30, [29]), ("Playable build regression", 35, [31, 32, 33, 34]),
    ]
    for i, (risk_title, blocked, blockers) in enumerate(risk_specs, 1):
        risks.append(AtlasRisk(
            id=f"RSK-{i:03d}", title=risk_title, blocked_task=f"TSK-{blocked:03d}",
            blocked_by=[f"TSK-{x:03d}" for x in blockers],
            risk=f"{task_names[blocked-1]} cannot be validated until its gameplay prerequisites are stable.",
            impact="High" if blocked in (7, 15, 35) else "Medium",
            probability="Medium", mitigation=f"Time-box and verify {task_names[blockers[0]-1].lower()} before starting the blocked work.",
        ))

    gallery = []
    category_subjects = {
        "Character": ["playable hero", "primary adversary", "supporting encounter character"],
        "Weapon/Equipment": ["primary gameplay equipment", "secondary equipment", "reward pickup equipment"],
        "Environment": ["main playable arena", "high-risk encounter zone", "safe start and extraction zone"],
        "UI": ["gameplay HUD", "inventory or loadout panel", "pause and completion screen"],
    }
    for category, subjects in category_subjects.items():
        for subject in subjects:
            gallery.append(AtlasArtConcept(
                title=f"{title} — {subject.title()}", category=category,
                prompt=f"Production concept art for {title}, {subject}, readable game silhouette, cohesive project art direction, practical MVP detail, no text watermark",
                purpose=f"Guide production decisions for the {subject}."))

    planned = round(sum(t.hours for t in detailed), 2)
    tools_guide = generate_tools_guide(tools)
    tools_lower = tools.lower()
    if "unreal" in tools_lower:
        project_structure = [
            f"{title}/", "Config/", "Content/Maps/Bootstrap.umap", "Content/Maps/Gameplay.umap",
            "Content/Blueprints/Player/", "Content/Blueprints/Gameplay/", "Content/Blueprints/AI/",
            "Content/Characters/", "Content/Equipment/", "Content/Environment/", "Content/UI/",
            "Content/Audio/", "Content/Materials/", "Source/", "Builds/", "Docs/MVP-Scope.md",
        ]
    elif "godot" in tools_lower:
        project_structure = [
            f"{title}/", "project.godot", "scenes/bootstrap.tscn", "scenes/gameplay.tscn",
            "scripts/player/", "scripts/gameplay/", "scripts/ai/", "scripts/ui/", "assets/characters/",
            "assets/equipment/", "assets/environment/", "assets/materials/", "assets/audio/", "ui/",
            "builds/", "docs/MVP-Scope.md",
        ]
    else:
        project_structure = [
            f"{title}/", "Assets/Scenes/", "Assets/Scenes/Bootstrap.unity", "Assets/Scenes/Gameplay.unity",
            "Assets/Scripts/Player/", "Assets/Scripts/Gameplay/", "Assets/Scripts/AI/", "Assets/Scripts/UI/",
            "Assets/Prefabs/Characters/", "Assets/Prefabs/Equipment/", "Assets/Prefabs/Environment/",
            "Assets/Art/Models/", "Assets/Art/Materials/", "Assets/Art/Textures/", "Assets/Audio/",
            "Assets/UI/", "Assets/Settings/", "Builds/", "Docs/MVP-Scope.md",
        ]
    return AtlasOutput(
        project_id=project_data.get("project_id", ""), roadmap=roadmap,
        project_structure=project_structure,
        production_flow_map=[
            "Game concept and MVP constraint lock", "Core gameplay design", "Input, player controller, and camera",
            f"{mechanic} prototype", "Damage, challenge, and fail-state integration", "Enemy/challenge behavior",
            "Level blockout and encounter flow", "Rewards and lightweight progression", "Character and equipment asset pass",
            "Environment art, lighting, and readability", "UI and HUD integration", "Audio feedback and mix",
            "End-to-end playtest", "Blocker fixes and performance pass", "Build export", "Playable MVP",
        ],
        dependency_map=[f"{t.dependencies[0]} -> {t.id}" for t in detailed if t.dependencies],
        task_breakdown=AtlasTaskBreakdown(
            critical_tasks=[f"{t.id} — {t.name}" for t in detailed if t.critical_path],
            optional_tasks=[], future_expansion=["Additional level", "Expanded progression", "More playable content"],
            detailed_tasks=detailed, tools_guide=tools_guide,
        ), risks=risks, art_gallery=gallery,
        roadmap_simulator=AtlasSimulation(
            available_hours=capacity, planned_hours=planned, status="ON TRACK" if planned <= capacity else "AT RISK",
            explanation=f"Plan uses {planned} of {capacity} available hours, leaving {round(capacity-planned, 2)} hours of buffer.",
        ),
    )


def _atlas_view(atlas: dict) -> dict:
    """Expose persisted Atlas fields in the shape consumed by the UI."""
    result = dict(atlas)
    result["project_structure"] = result.get("structure") or []
    result["production_flow_map"] = result.get("flow_map") or []
    result["task_breakdown"] = result.get("tasks") or {}
    sections = result["task_breakdown"].get("atlas_sections") or {}
    result["risks"] = sections.get("risk_dashboard", result.get("risks") or [])
    result["roadmap_simulator"] = sections.get("simulation", result.get("roadmap_simulator"))
    result["feasibility"] = sections.get("feasibility", result.get("feasibility"))
    return result


def _job_state(atlas: dict) -> dict:
    tasks = atlas.get("tasks") or {}
    return tasks.get("atlas_job") or {}


def _persist_atlas(atlas: dict) -> None:
    db.save_atlas_project(
        atlas_id=atlas["id"], user_id=atlas.get("user_id"),
        source_project_id=atlas.get("source_project_id") or "", title=atlas.get("title") or "Untitled Project",
        duration=atlas.get("duration") or "", tools=atlas.get("tools") or "",
        roadmap=atlas.get("roadmap") or [], structure=atlas.get("structure") or [],
        flow_map=atlas.get("flow_map") or [], dependency_map=atlas.get("dependency_map") or [],
        tasks=atlas.get("tasks") or {}, generated_files=atlas.get("generated_files") or {},
        zip_path=atlas.get("zip_path"), feasibility_score=atlas.get("feasibility_score") or 0,
        success_probability=atlas.get("success_probability") or 0,
        estimated_completion_days=atlas.get("estimated_completion_days") or 0,
        required_hours_per_day=atlas.get("required_hours_per_day") or 0,
    )


def _run_atlas_stage(atlas: dict) -> dict:
    """Run exactly one durable Atlas stage. Polling invokes this short operation."""
    state = _job_state(atlas)
    if not state:
        raise ValueError("Atlas job state is missing.")
    if state.get("status") in {"completed", "failed"}:
        return atlas

    stage_index = state.get("stage_index", 0)
    if stage_index >= len(ATLAS_STAGES):
        state["status"] = "completed"
        atlas["tasks"]["atlas_job"] = state
        _persist_atlas(atlas)
        return atlas

    try:
        source = db.get_project(state["project_id"])
        project_data = (source or {}).get("project_json") or {}
        if not isinstance(project_data, dict):
            project_data = {}
        project_data["project_id"] = state["project_id"]
        project_data["title"] = state["project_title"]
        plan, metadata = build_atlas_plan(
            project_id=state["project_id"], project_title=state["project_title"],
            duration=state["duration"], team_size=state["team_size"],
            hours_per_day=state["hours_per_day"], tools=state["tools"],
            project_type=state.get("project_type", ""), user_prompt=state.get("user_prompt", ""),
            project_data=project_data,
        )
        stage = ATLAS_STAGES[stage_index]
        if stage == "roadmap":
            atlas["roadmap"] = [item.model_dump() for item in plan.roadmap]
        elif stage == "tasks":
            task_data = plan.task_breakdown.model_dump()
            task_data["team_size"] = state["team_size"]
            task_data["hours_per_day"] = state["hours_per_day"]
            task_data["atlas_job"] = state
            atlas["tasks"] = task_data
            db.save_atlas_tasks(atlas["id"], [{
                "task_id": task.id, "title": task.title, "hours": task.hours,
                "priority": task.priority, "status": task.status, "assignee": task.owner,
                "dependencies": task.dependencies, "critical_path": task.critical_path,
            } for task in plan.task_breakdown.detailed_tasks])
        elif stage == "structure":
            atlas["structure"] = plan.project_structure
        elif stage == "flow_map":
            atlas["flow_map"] = plan.production_flow_map
            atlas["dependency_map"] = plan.dependency_map
            db.save_atlas_flow(atlas["id"], plan.production_flow_map)
        elif stage == "risk_dashboard":
            risks = [item.model_dump() for item in plan.risks]
            atlas.setdefault("tasks", {}).setdefault("atlas_sections", {})["risk_dashboard"] = risks
            db.save_atlas_risks(atlas["id"], risks)
        elif stage == "simulation":
            simulation = plan.roadmap_simulator.model_dump()
            atlas.setdefault("tasks", {}).setdefault("atlas_sections", {})["simulation"] = simulation
            atlas["feasibility_score"] = metadata["completion_probability"]
            atlas["success_probability"] = metadata["completion_probability"]
            atlas["estimated_completion_days"] = metadata["total_days"]
            atlas["required_hours_per_day"] = state["hours_per_day"]
            atlas.setdefault("tasks", {}).setdefault("atlas_sections", {})["feasibility"] = {
                "required_team_size": state["team_size"], "required_hours_per_day": state["hours_per_day"],
                "estimated_completion_days": metadata["total_days"],
                "available_capacity_hours": metadata["available_capacity_hours"],
                "planned_hours": metadata["planned_hours"],
                "success_probability": metadata["completion_probability"],
                "risk_level": "Low" if metadata["status"] == "ON TRACK" else "Medium" if metadata["status"] == "AT RISK" else "High",
            }
        elif stage == "tools_integration":
            atlas.setdefault("tasks", {}).setdefault("tools_guide", plan.task_breakdown.tools_guide)
        elif stage == "export":
            atlas["generated_files"] = compile_markdown_files(atlas["title"], plan)
            atlas["zip_path"] = create_atlas_zip_on_disk(atlas["id"], atlas, [])

        state["stage_index"] = stage_index + 1
        state["completed_sections"] = ATLAS_STAGES[: stage_index + 1]
        state["status"] = "completed" if stage_index + 1 == len(ATLAS_STAGES) else "processing"
        atlas.setdefault("tasks", {})["atlas_job"] = state
        _persist_atlas(atlas)
    except Exception as exc:
        state["status"] = "failed"
        state["error"] = str(exc)
        atlas.setdefault("tasks", {})["atlas_job"] = state
        _persist_atlas(atlas)
    return atlas


@app.post("/api/atlas/generate")
@app.post("/api/atlas")
@app.post("/")
async def generate_atlas(req: AtlasRequest):
    try:
        # Queue only. Every section is generated and persisted by a later poll,
        # keeping this request safely below Vercel's function runtime limit.
        duration_spec = parse_duration(req.duration)
        atlas_id = req.atlas_id or str(uuid.uuid4())
        title = req.project_title or "Untitled Project"
        state = {
            "status": "queued", "stage_index": 0, "completed_sections": [],
            "project_id": req.project_id, "project_title": title,
            "duration": req.duration, "team_size": req.team_size,
            "hours_per_day": req.hours_per_day, "tools": req.tools,
            "project_type": req.project_type or "", "user_prompt": req.user_prompt or "",
        }
        atlas_data = {
            "id": atlas_id, "user_id": "spotifysahir007@gmail.com", "source_project_id": req.project_id,
            "title": title, "duration": req.duration, "tools": req.tools,
            "roadmap": [], "structure": [], "flow_map": [], "dependency_map": [],
            "tasks": {"atlas_job": state}, "generated_files": {}, "zip_path": None,
            "estimated_completion_days": duration_spec.total_days,
            "required_hours_per_day": req.hours_per_day,
        }
        _persist_atlas(atlas_data)
        return JSONResponse(status_code=202, content={
            "success": True,
            "job": {"id": atlas_id, **state, "total_sections": len(ATLAS_STAGES)},
        })

        # Legacy synchronous implementation retained temporarily below for
        # reference while existing persisted Atlas records are migrated.
        # Fetch project details from database
        project_record = db.get_project(req.project_id)
        if not project_record:
            project_data = {
                "project_id": req.project_id,
                "title": req.project_title or "Untitled Project",
                "prompt": req.user_prompt or "",
            }
        else:
            project_data = project_record.get("project_json", {})
            if not isinstance(project_data, dict):
                project_data = {}
            project_data["project_id"] = req.project_id
            project_data["title"] = req.project_title or project_record.get("title") or "Untitled Project"

        title = req.project_title or project_data.get("title") or "Untitled Project"
        user_prompt = (
            req.user_prompt
            or project_data.get("prompt")
            or (project_record.get("prompt") if project_record else "")
            or ""
        )
        atlas_out, planning = build_atlas_plan(
            project_id=req.project_id,
            project_title=title,
            duration=req.duration,
            team_size=req.team_size,
            hours_per_day=req.hours_per_day,
            tools=req.tools,
            project_type=req.project_type or "",
            user_prompt=user_prompt,
            project_data=project_data,
        )

        # 1. Compile production-plan markdown files
        generated_files = compile_markdown_files(title, atlas_out)
        generated_files["Risks.md"] = "# Production Risks\n\n" + "\n\n".join(
            f"## {r.id} — {r.title}\nBlocked task: {r.blocked_task}\n\nRisk: {r.risk}\n\n"
            f"Impact: {r.impact} | Probability: {r.probability}\n\nMitigation: {r.mitigation}"
            for r in atlas_out.risks
        )
        generated_files["ArtConcepts.md"] = "# Art Concepts\n\n" + "\n\n".join(
            f"## {a.title}\nCategory: {a.category}\n\nPrompt: {a.prompt}\n\nPurpose: {a.purpose}"
            for a in atlas_out.art_gallery
        )

        # 2. Determine Atlas ID
        atlas_id = req.atlas_id if req.atlas_id else str(uuid.uuid4())

        # 3. Create the Atlas data dictionary for saving & ZIP generation
        user_id = project_record.get("user_id") if project_record else "spotifysahir007@gmail.com"
        
        # Save team_size and hours_per_day inside the tasks JSON
        tasks_dict = atlas_out.task_breakdown.model_dump() if hasattr(atlas_out.task_breakdown, "model_dump") else atlas_out.task_breakdown
        tasks_dict["team_size"] = req.team_size
        tasks_dict["hours_per_day"] = req.hours_per_day
        tasks_dict["project_type"] = planning["project_type"]

        atlas_data = {
            "title": title,
            "duration": req.duration,
            "tools": req.tools,
            "project_type": planning["project_type"],
            "user_prompt": user_prompt,
            "source_project_id": req.project_id,
            "roadmap": [phase.model_dump() if hasattr(phase, "model_dump") else phase for phase in atlas_out.roadmap],
            "structure": atlas_out.project_structure,
            "flow_map": atlas_out.production_flow_map,
            "dependency_map": atlas_out.dependency_map,
            "tasks": tasks_dict,
            "risks": [r.model_dump() for r in atlas_out.risks],
            "art_gallery": [a.model_dump() for a in atlas_out.art_gallery],
            "roadmap_simulator": atlas_out.roadmap_simulator.model_dump() if atlas_out.roadmap_simulator else None,
            "total_days": planning["total_days"],
            "working_hours": planning["working_hours"],
            "available_capacity_hours": planning["available_capacity_hours"],
            "planned_hours": planning["planned_hours"],
            "completion_probability": planning["completion_probability"],
            "plan_status": planning["status"],
            "roadmap_period_unit": planning["roadmap_period_unit"],
            "roadmap_period_count": planning["roadmap_period_count"],
            "generated_files": generated_files
        }

        # Extract feasibility metrics
        feasibility_score = planning["completion_probability"]
        success_probability = planning["completion_probability"]
        estimated_completion_days = planning["total_days"]
        required_hours_per_day = float(req.hours_per_day or 8.0)
        
        atlas_data["feasibility"] = {
            "required_team_size": req.team_size,
            "required_hours_per_day": req.hours_per_day,
            "estimated_completion_days": estimated_completion_days,
            "available_hours": planning["available_capacity_hours"],
            "available_capacity_hours": planning["available_capacity_hours"],
            "planned_hours": planning["planned_hours"],
            "success_probability": planning["completion_probability"],
            "risk_level": (
                "Low" if planning["status"] == "ON TRACK"
                else "Medium" if planning["status"] == "AT RISK"
                else "High"
            ),
        }

        # 4. Fetch source project images (if available)
        images = []
        if project_record:
            images = db.get_project_images(req.project_id)

        # 5. Build ZIP file on backend
        zip_path = create_atlas_zip_on_disk(atlas_id, atlas_data, images)

        # 6. Save in Supabase
        db.save_atlas_project(
            atlas_id=atlas_id,
            user_id=user_id,
            source_project_id=req.project_id,
            title=title,
            duration=req.duration,
            tools=req.tools,
            roadmap=atlas_data["roadmap"],
            structure=atlas_data["structure"],
            flow_map=atlas_data["flow_map"],
            dependency_map=atlas_data["dependency_map"],
            tasks=atlas_data["tasks"],
            generated_files=generated_files,
            zip_path=zip_path,
            feasibility_score=feasibility_score,
            success_probability=success_probability,
            estimated_completion_days=estimated_completion_days,
            required_hours_per_day=required_hours_per_day
        )

        # Save to granular atlas tables
        # Tasks
        tasks_list = [
            {
                "task_id": task.id,
                "title": task.title,
                "hours": task.hours,
                "priority": task.priority,
                "status": task.status,
                "assignee": task.owner,
                "dependencies": task.dependencies,
                "critical_path": task.critical_path,
            }
            for task in atlas_out.task_breakdown.detailed_tasks
        ]
        db.save_atlas_tasks(atlas_id, tasks_list)

        # Milestones
        milestones_list = []
        if "planner" in project_data and project_data["planner"] and "milestones" in project_data["planner"]:
            milestones_list = [{"title": m, "description": "", "due_date": None} for m in project_data["planner"]["milestones"]]
        else:
            for phase in atlas_out.roadmap:
                name = phase.name if hasattr(phase, "name") else phase.get("name", "")
                tasks_desc = ", ".join(phase.tasks if hasattr(phase, "tasks") else phase.get("tasks", []))
                milestones_list.append({
                    "title": name,
                    "description": tasks_desc,
                    "due_date": None
                })
        db.save_atlas_milestones(atlas_id, milestones_list)

        # Flow
        db.save_atlas_flow(atlas_id, atlas_out.production_flow_map)

        # Risks
        risks_list = []
        if atlas_out.risks:
            risks_list = [r.model_dump() for r in atlas_out.risks]
        elif "risk" in project_data and project_data["risk"] and "risks" in project_data["risk"]:
            risks_list = project_data["risk"]["risks"]
        db.save_atlas_risks(atlas_id, risks_list)

        # Images
        images_list = []
        for img in images:
            images_list.append({
                "image_url": img.get("image_url", ""),
                "category": img.get("category", "")
            })
        db.save_atlas_images(atlas_id, images_list)

        # Exports
        exports_list = []
        if zip_path:
            exports_list.append({
                "file_name": os.path.basename(zip_path),
                "file_type": "zip",
                "file_url": f"/api/atlas/download?atlas_id={atlas_id}"
            })
        db.save_atlas_exports(atlas_id, exports_list)

        return {
            "success": True,
            "atlas": {
                "id": atlas_id,
                **atlas_data,
                "project_structure": atlas_data["structure"],
                "production_flow_map": atlas_data["flow_map"],
                "task_breakdown": atlas_data["tasks"]
            }
        }
    except Exception as e:
        tb = traceback.format_exc()
        return {
            "success": False,
            "error": str(e),
            "traceback": tb
        }

@app.get("/api/atlas/download")
async def download_atlas(atlas_id: str):
    atlas = db.get_atlas_project(atlas_id)
    if not atlas:
        raise HTTPException(status_code=404, detail="Atlas project not found")
        
    zip_path = atlas.get("zip_path")
    if zip_path and os.path.exists(zip_path):
        return FileResponse(zip_path, media_type="application/zip", filename=f"{atlas_id}_atlas_production_kit.zip")
        
    # If file missing on disk (Stateless deployment), regenerate it on the fly!
    images = []
    source_project_id = atlas.get("source_project_id")
    if source_project_id:
        images = db.get_project_images(source_project_id)
        
    new_zip_path = create_atlas_zip_on_disk(atlas_id, atlas, images)
    
    # Save the updated path in Supabase
    db.save_atlas_project(
        atlas_id=atlas_id,
        user_id=atlas.get("user_id"),
        source_project_id=source_project_id,
        title=atlas.get("title"),
        duration=atlas.get("duration"),
        tools=atlas.get("tools"),
        roadmap=atlas.get("roadmap"),
        structure=atlas.get("structure"),
        flow_map=atlas.get("flow_map"),
        dependency_map=atlas.get("dependency_map"),
        tasks=atlas.get("tasks"),
        generated_files=atlas.get("generated_files"),
        zip_path=new_zip_path
    )
    
    return FileResponse(new_zip_path, media_type="application/zip", filename=f"{atlas_id}_atlas_production_kit.zip")

@app.post("/api/atlas/duplicate")
async def duplicate_atlas(req: DuplicateRequest):
    try:
        atlas = db.get_atlas_project(req.atlas_id)
        if not atlas:
            return {"success": False, "error": "Original Atlas project not found"}
            
        new_id = str(uuid.uuid4())
        new_title = f"{atlas.get('title') or 'Untitled'} - Copy"
        
        # Save a duplicate record
        db.save_atlas_project(
            atlas_id=new_id,
            user_id=atlas.get("user_id"),
            source_project_id=atlas.get("source_project_id"),
            title=new_title,
            duration=atlas.get("duration"),
            tools=atlas.get("tools"),
            roadmap=atlas.get("roadmap"),
            structure=atlas.get("structure"),
            flow_map=atlas.get("flow_map"),
            dependency_map=atlas.get("dependency_map"),
            tasks=atlas.get("tasks"),
            generated_files=atlas.get("generated_files"),
            zip_path=atlas.get("zip_path")  # Point to same ZIP initially
        )
        
        return {
            "success": True,
            "atlas_id": new_id
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/atlas")
@app.delete("/")
async def delete_atlas(atlas_id: str = Query(...)):
    try:
        atlas = db.get_atlas_project(atlas_id)
        if not atlas:
            return {"success": False, "error": "Atlas project not found"}
            
        # Optional: delete zip file from disk if present
        zip_path = atlas.get("zip_path")
        if zip_path and os.path.exists(zip_path):
            try:
                os.unlink(zip_path)
            except Exception:
                pass
                
        success = db.delete_atlas_project(atlas_id)
        return {"success": success}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/atlas")
@app.get("/")
async def get_atlas(
    atlas_id: Optional[str] = Query(None),
    job_id: Optional[str] = Query(None),
    source_project_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None)
):
    if job_id:
        atlas = db.get_atlas_project(job_id)
        if not atlas:
            return {"success": False, "error": "Atlas job not found"}
        atlas = _run_atlas_stage(atlas)
        state = _job_state(atlas)
        return {
            "success": state.get("status") != "failed",
            "job": {
                "id": job_id,
                "status": state.get("status", "queued"),
                "completed_sections": state.get("completed_sections", []),
                "total_sections": len(ATLAS_STAGES),
                "error": state.get("error"),
            },
            "atlas": _atlas_view(atlas),
        }

    # If requesting details of specific Atlas
    if atlas_id:
        atlas = db.get_atlas_project(atlas_id)
        if not atlas:
            return {"success": False, "error": "Atlas project not found"}
        if isinstance(atlas, dict):
            atlas["project_structure"] = atlas.get("structure") or []
            atlas["production_flow_map"] = atlas.get("flow_map") or []
            atlas["task_breakdown"] = atlas.get("tasks") or {}
            
            # Inject feasibility object for simulator auto-population
            tasks_data = atlas.get("tasks") or {}
            team_size = tasks_data.get("team_size") or 1
            hours_per_day = tasks_data.get("hours_per_day") or 8.0
            completion_days = atlas.get("estimated_completion_days") or parse_duration_to_days(atlas.get("duration") or "")
            atlas["feasibility"] = {
                "required_team_size": team_size,
                "required_hours_per_day": hours_per_day,
                "estimated_completion_days": completion_days
            }
        atlas = _atlas_view(atlas)
        return {
            "success": True,
            "atlas": atlas
        }
        
    # If requesting all Atlas plans linked to a source project
    if source_project_id:
        plans = db.get_atlas_projects_by_source(source_project_id)
        for p in plans:
            if isinstance(p, dict):
                p["project_structure"] = p.get("structure") or []
                p["production_flow_map"] = p.get("flow_map") or []
                p["task_breakdown"] = p.get("tasks") or {}
                
                # Inject feasibility object
                tasks_data = p.get("tasks") or {}
                team_size = tasks_data.get("team_size") or 1
                hours_per_day = tasks_data.get("hours_per_day") or 8.0
                completion_days = p.get("estimated_completion_days") or parse_duration_to_days(p.get("duration") or "")
                p["feasibility"] = {
                    "required_team_size": team_size,
                    "required_hours_per_day": hours_per_day,
                    "estimated_completion_days": completion_days
                }
        return {
            "success": True,
            "plans": plans
        }
        
    # If requesting all Atlas plans for a user
    if user_id:
        plans = db.list_atlas_projects(user_id=user_id)
        for p in plans:
            if isinstance(p, dict):
                p["project_structure"] = p.get("structure") or []
                p["production_flow_map"] = p.get("flow_map") or []
                p["task_breakdown"] = p.get("tasks") or {}
                
                # Inject feasibility object
                tasks_data = p.get("tasks") or {}
                team_size = tasks_data.get("team_size") or 1
                hours_per_day = tasks_data.get("hours_per_day") or 8.0
                completion_days = p.get("estimated_completion_days") or parse_duration_to_days(p.get("duration") or "")
                p["feasibility"] = {
                    "required_team_size": team_size,
                    "required_hours_per_day": hours_per_day,
                    "estimated_completion_days": completion_days
                }
        return {
            "success": True,
            "plans": plans
        }

    return {
        "status": "ready",
        "platform": "DreamXV AI Studio",
        "feature": "DreamXV Atlas",
        "description": "Generate AI-powered development roadmaps, project structures, and production workflows for your projects."
    }
