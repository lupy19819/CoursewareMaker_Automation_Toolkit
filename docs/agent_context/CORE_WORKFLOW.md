# Core Workflow Context

This is the model-neutral context entry for CoursewareMaker_Automation_Toolkit.
It keeps agents focused on the deterministic workflow and avoids unnecessary
repository reads.

When locating scripts, check `docs/SCRIPT_INDEX.md` first, then open only the
target script.

## 1. Project Positioning

CoursewareMaker_Automation_Toolkit automates CoursewareMaker game production:
routing user requests, checking resources, generating configs, validating
configs, creating games, importing/saving configs, previewing, and publishing.

The supported top-level families are:

- `yundong_pk`: run, swim, racecar
- `template_game`: monster, road_adventure, bridge, amusement_park, spelling,
  magic_spelling, fanboat, train
- `standard_component`: standard_component

## 2. Source Of Truth

The workflow source of truth is the deterministic control layer under
`workflow/`:

- `workflow/workflow_router.py`
- `workflow/workflow_planner.py`
- `workflow/workflow_guard.py`
- `workflow/workflow_executor.py`
- `workflow/execution_registry.json`
- `workflow/game_type_rules.json`
- `workflow/game_input_schemas.json`
- `workflow/stage_policy.json`
- `workflow/validation_policy.json`
- `workflow/script_registry.json`

Do not treat README text, old notes, generated output, or model memory as the
workflow source of truth when these files disagree.

## 3. Correct Execution Chain

The standard chain is:

```bash
python3 workflow/workflow_router.py -m "<user message>"
python3 workflow/workflow_router.py -m "<user message>" | python3 workflow/workflow_planner.py
python3 workflow/workflow_router.py -m "<user message>" | python3 workflow/workflow_planner.py | python3 workflow/workflow_guard.py --action <action>
python3 workflow/workflow_executor.py -m "<user message>"
```

`workflow_executor.py` is the single deterministic execution entrypoint. It
must call router, planner, guard, and fixed adapters from
`workflow/execution_registry.json`.

## 4. Model Responsibility Boundary

The model may:

- Run commands.
- Explain blocked reasons.
- Ask for missing fields.
- Explain validator errors.
- Summarize deterministic workflow decisions.
- Edit scripts or docs when explicitly asked.

The model must not:

- Invent workflow steps at runtime.
- Bypass `workflow_guard.py` or `workflow_executor.py`.
- Use model judgment as a substitute for registry entries.
- Decide a config is correct by visual impression or memory.
- Save, publish, or create games when planner or guard blocks.
- Reuse prior task state when the current route lacks required fields.

## 5. Minimal Read Scope By Task Type

### Workflow Routing Questions

Read:

- `workflow/intent_rules.json`
- `workflow/game_type_rules.json`
- `workflow/stage_policy.json`
- `workflow/workflow_router.py`
- `workflow/workflow_planner.py`

Avoid reading generators, resources, and reference configs unless the route
depends on them.

### Add Or Fix A Game Generator

Read:

- Relevant adapter in `workflow/execution_registry.json`
- Relevant schema in `workflow/game_input_schemas.json`
- Relevant validation policy in `workflow/validation_policy.json`
- The specific generator script
- The specific validator script
- The smallest relevant reference config or fixture

Avoid reading all template references or unrelated generators.

### Resource Resolution Problems

Read:

- `scripts/resolve_sheet_resources.py`
- `scripts/resolve_input_resources.py`
- Relevant schema in `workflow/game_input_schemas.json`
- `resources/latest_resources.json` only when resource data is required

Avoid reading `resources/latest_resources.json` for non-resource tasks.

### Save, Preview, Or Publish Problems

Read:

- `workflow/stage_policy.json`
- `workflow/workflow_guard.py`
- `workflow/workflow_executor.py`
- `scripts/save_game_config_via_cdp.js`
- `scripts/roundtrip_compare_config.js`
- `scripts/create_preview_url.js`
- `scripts/publish_game_auto.js` only for publish tasks

Avoid generator and reference-config reads unless config content is part of the
failure.

### Standard Component Questions

Read:

- `workflow/execution_registry.json`
- `workflow/game_input_schemas.json`
- `workflow/validation_policy.json`
- `standard_question_toolkit/scripts/validate_standard_component_config.py`
- Other `standard_question_toolkit/` files only when the task explicitly needs
  standard-component internals

Avoid `standard_question_toolkit/` for non-standard-component tasks.

### Documentation Organization

Read:

- `AGENTS.md`
- `docs/agent_context/CORE_WORKFLOW.md`
- `docs/agent_context/CODEX.md`
- The exact doc files named by the user
- Workflow registries only when verifying doc claims

Avoid reading generated outputs and large reference configs.

## 6. Default Do-Not-Read List

Do not read these by default:

- `output/`
- `generated_configs/`
- `chrome_monitoring_logs/`
- Large JSON files under `reference_configs/`
- `resources/latest_resources.json`, unless the task involves resources
- `standard_question_toolkit/`, unless the task is explicitly standard
  component related
- Historical `fix_*`, `gen_batch_*`, or `update_*` scripts, unless the user
  names them

## 7. Unified Verification Commands

Run these after workflow-context or control-layer changes:

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
