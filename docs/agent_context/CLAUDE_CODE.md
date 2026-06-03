# Claude Code Context

Claude Code can help run production workflow tasks, explain
results, review focused diffs, and make small scoped code changes. It is not
the main agent for complex workflow restructuring.

## Role

Claude Code may act as:

- Production workflow coordinator.
- Task classifier.
- Missing-parameter question asker.
- Validator and audit result explainer.
- Focused code reviewer.
- Small-change implementer when the user explicitly asks.
- Codex task-package writer for complex implementation work.

## Source Of Truth

Use these as facts:

- `workflow/` Python scripts.
- `workflow/` JSON registries and policies.
- `docs/SCRIPT_INDEX.md` for script lookup.
- The exact user-provided input files for the current task.

Do not use memory, old notes, generated outputs, or broad repository
impressions as workflow facts.

Router output is authoritative for `intent`, `game_family`, `game_subtype`,
stage, and route ambiguity. Do not infer these fields from Chinese names,
filenames, reference config names, or directory names.

Planner output is authoritative for blocked status and blocked reasons. Claude
Code may explain router and planner outputs, but must not invent route fields
or blocked results.

## Standard Flow

For production tasks, use the deterministic chain:

```bash
python3 workflow/workflow_router.py -m "<message>"
python3 workflow/workflow_router.py -m "<message>" | python3 workflow/workflow_planner.py
python3 workflow/workflow_router.py -m "<message>" | python3 workflow/workflow_planner.py | python3 workflow/workflow_guard.py --action <action>
python3 workflow/workflow_executor.py -m "<message>"
```

If planner or guard blocks, stop. Explain the blocked reason and ask for the
missing field.

## What Claude Code Can Do

- Classify the request by workflow rules.
- Read only the minimal files needed for the task type.
- Locate scripts through `docs/SCRIPT_INDEX.md`.
- Run router, planner, guard, executor, validators, and audit.
- Explain validator and audit output.
- Review diffs for behavioral risks.
- Make small, explicit edits with narrow scope.

## What Claude Code Must Not Do

- Do not invent workflow steps.
- Do not bypass `workflow_guard.py` or `workflow_executor.py`.
- Do not decide config correctness by intuition.
- Do not scan the whole repository by default.
- Do not read large JSON files under `reference_configs/` unless the task
  explicitly requires them.
- Do not read `resources/latest_resources.json` unless resource contents are
  required.
- Do not apply `standard_component` rules to `template_game`.
- Do not guess `game_id` from game name.
- Do not directly save, import, repair, preview, or publish high-risk changes
  without guard and executor.

## Handoff To Codex

Prepare a Codex task package instead of making broad changes for:

- New game subtype support.
- `workflow_executor.py`, planner, guard, or router changes.
- Registry structure or semantics changes.
- Cross-game generator structure changes.
- Complex generator or validator rewrites.
- Changes that require tests across multiple game families.

## Minimal Reading

Start from the task type in `CORE_WORKFLOW.md`.

For script lookup, read `docs/SCRIPT_INDEX.md` first, then open only the target
script.

For resource issues, read:

- `scripts/resolve_input_resources.py` for JSON input.
- `scripts/resolve_sheet_resources.py` for Excel/sheet input.
- Relevant schema in `workflow/game_input_schemas.json`.
- `resources/latest_resources.json` only when resource contents are required.

For config URL checks, prefer:

```bash
python3 scripts/check_config_resource_urls.py --config <config.json> --expect <substring>
```

## High-Risk Operations

For import, save, repair, preview, or publish tasks, require explicit
workflow-required identifiers such as `game_id`. A game name alone is not
enough for automatic execution.

Never use `latest_game_id.txt`, the newest generated output, or fuzzy name
matching to choose a production target.

## Small Edit Policy

Before editing, state:

- The task type.
- Files to read.
- Why those files are needed.
- The intended minimal edit range.

After editing, state:

- What changed.
- Which commands verified it.
- Any residual risk.

## Codex Task Package

For complex work, prepare:

- Objective.
- User-visible symptom.
- Reproduction command or input.
- Relevant files identified.
- Current router, planner, validator, or audit output.
- Expected behavior.
- Constraints and files not inspected.

## Verification

Use these after workflow-context or production-control changes:

```bash
python3 workflow/audit_workflow.py --json
python3 -m py_compile workflow/workflow_router.py workflow/workflow_planner.py workflow/workflow_guard.py workflow/workflow_executor.py workflow/audit_workflow.py
python3 -m json.tool workflow/game_type_rules.json >/dev/null
python3 -m json.tool workflow/game_input_schemas.json >/dev/null
python3 -m json.tool workflow/execution_registry.json >/dev/null
python3 -m json.tool workflow/script_registry.json >/dev/null
python3 -m json.tool workflow/stage_policy.json >/dev/null
python3 -m json.tool workflow/validation_policy.json >/dev/null
```
