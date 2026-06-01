# Kimi Entry

This is the short Kimi project entrypoint. It is only navigation, not the full
workflow manual.

## Read First

1. Read `docs/agent_context/CORE_WORKFLOW.md`.
2. Then read `docs/agent_context/KIMI.md`.
3. To locate scripts, check `docs/SCRIPT_INDEX.md` before opening `scripts/`.
4. Read other files only when the current task type requires them.

## Core Rules

- Do not default to scanning the whole repository.
- Do not bypass `workflow/workflow_guard.py`.
- Do not bypass `workflow/workflow_executor.py`.
- Do not treat model judgment as the workflow source of truth.
- Use `workflow/` Python scripts and JSON registries as deterministic facts.
- For high-risk save, import, repair, preview, or publish actions, require the
  workflow-required explicit fields such as `game_id`.

## Kimi Production Role

Kimi coordinates production work:

- Classify requests with the workflow rules.
- Ask for missing parameters.
- Run router, planner, guard, executor, validators, and audit.
- Explain results in user-facing language.

## Codex Handoff

For complex code changes, do not directly make broad edits. First prepare a
Codex task package with objective, reproduction, relevant files, current
workflow output, expected behavior, and constraints.
