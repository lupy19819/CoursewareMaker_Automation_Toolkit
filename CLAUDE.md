# Claude Code Entry

This is the short Claude Code entrypoint for Claude Code workflows. Keep it low
token: read detailed docs only when the task requires them.

## First Decisions

1. Classify the task type before reading extra files.
2. Choose the minimal read scope for that task.
3. To locate scripts, check `docs/SCRIPT_INDEX.md` before opening `scripts/`.
4. For detailed rules, read `docs/agent_context/CORE_WORKFLOW.md` and
   `docs/agent_context/CLAUDE_CODE.md` when the task requires them.

## Core Rules

- Do not default to scanning the whole repository.
- Do not bypass `workflow/workflow_executor.py`.
- Do not bypass `workflow/workflow_guard.py`.
- Do not treat model judgment as a substitute for workflow registry facts.
- Use `workflow/` Python scripts and JSON registries as deterministic facts.
- Use validators and audit results to judge config correctness.
- If router, planner, guard, executor, or validators block, explain the reason
  and ask for missing fields instead of inventing a path.

## High-Risk Actions

For import, save, repair, preview, and publish tasks:

- Follow `workflow/stage_policy.json`.
- Require workflow-required explicit fields such as `game_id`.
- Block when `game_id` is missing and the workflow requires it.
- Do not guess `game_id` from game name.
- Do not directly save or publish without guard and executor.

## Claude Code Role

Claude Code may handle production orchestration, result explanation, review,
and small scoped edits.

For complex workflow, registry, generator, validator, planner, guard, router,
or executor changes, prepare a Codex task package instead of doing a broad
rewrite.
