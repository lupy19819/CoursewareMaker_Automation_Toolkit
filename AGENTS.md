# CoursewareMaker Automation Toolkit

This file is the short Codex entrypoint. It is only a map, not the full
workflow documentation.

## Read First

1. Read `docs/agent_context/CORE_WORKFLOW.md`.
2. Then read `docs/agent_context/CODEX.md`.
3. Read other files only when the current task type requires them.
4. To locate scripts, check `docs/SCRIPT_INDEX.md` before opening `scripts/`.

## Core Rules

- Do not default to scanning the whole repository.
- Do not bypass `workflow/workflow_executor.py`.
- Do not treat model judgment as a workflow source of truth.
- Use `workflow/` Python scripts and JSON registries as the deterministic
  workflow facts.
- If router, planner, guard, executor, or validators block, report the reason
  and ask for missing fields instead of inventing a path.

## Default Execution Chain

Use the deterministic chain:

```bash
python3 workflow/workflow_router.py -m "<message>"
python3 workflow/workflow_planner.py
python3 workflow/workflow_guard.py
python3 workflow/workflow_executor.py -m "<message>"
```

For implementation or documentation tasks, first identify the task type, then
follow the minimal read scope in `docs/agent_context/CORE_WORKFLOW.md`.

Kimi users should see `.kimi/AGENTS.md` and `docs/agent_context/KIMI.md`.
