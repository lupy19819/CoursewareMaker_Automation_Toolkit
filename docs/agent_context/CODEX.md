# Codex Context

Codex must follow `AGENTS.md` first. Treat
`docs/agent_context/CORE_WORKFLOW.md` as the core workflow entrypoint for this
project.

## Entry Rules

- Keep `AGENTS.md` short. It is a signpost, not a long workflow document.
- Start each task by classifying the task type.
- After classifying the task, read only the files listed for that task type in
  `CORE_WORKFLOW.md`.
- Do not scan the whole repository by default.
- Do not use generated outputs, historical scratch scripts, or model memory as
  the workflow source of truth.

## Execution Rules

- Do not bypass `workflow/workflow_executor.py` for executable workflow tasks.
- Do not bypass router, planner, guard, registry, or validator decisions.
- Do not convert a blocked plan into an improvised action.
- If `workflow_planner.py` or `workflow_guard.py` blocks, explain the blocked
  reason and ask for the missing field.
- If a validator fails, explain the concrete failing rule and the file or field
  involved.

## Context Discipline

- Do not default to subagents or multi-agent parallel work unless the user
  explicitly asks for it.
- Avoid broad `find`, full-repo reads, and large JSON reads when a narrower
  registry or named file answers the task.
- Prefer `rg` and targeted file reads.
- For resource tasks, read `resources/latest_resources.json` only when the
  resource list is necessary.
- For standard-component tasks, read `standard_question_toolkit/` only when the
  task explicitly requires it.

## Communication Pattern

Before edits, say:

- Which task type this is.
- Which files will be read.
- Why those files are needed.

After edits, say:

- What changed.
- How it was verified.
- What risk remains, if any.

## Commit Policy

Do not commit unless the user explicitly asks. When asked to commit, stage only
the files relevant to the requested change.
