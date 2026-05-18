#!/usr/bin/env python3
"""Audit deterministic CoursewareMaker workflow wiring.

This script is intentionally static and cross-platform: it checks registry
paths, schemas, validators, and fixtures before a weak model or a different
machine can drift into an unsupported branch.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = Path(__file__).resolve().parent


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel_exists(path: str | None) -> bool:
    return bool(path) and (ROOT / path).exists()


def add_issue(issues: list[dict[str, str]], severity: str, code: str, message: str) -> None:
    issues.append({"severity": severity, "code": code, "message": message})


def audit_registry(issues: list[dict[str, str]]) -> None:
    registry = load_json(WORKFLOW / "execution_registry.json")
    schemas = load_json(WORKFLOW / "game_input_schemas.json")
    adapters = registry.get("generation_adapters", {})

    for family, subtypes in adapters.items():
        for subtype, adapter in subtypes.items():
            label = f"{family}/{subtype}"
            schema = schemas.get(family, {}).get(subtype)
            if not schema:
                add_issue(issues, "error", "missing_schema", f"{label} has no game_input_schemas entry")

            command = adapter.get("command") or []
            script = command[1] if len(command) > 1 and command[0] == "python" else (command[0] if command else "")
            if script and not rel_exists(script):
                add_issue(issues, "error", "missing_generator", f"{label} generator not found: {script}")

            template = adapter.get("default_template")
            if template and not rel_exists(template):
                add_issue(issues, "error", "missing_template", f"{label} default_template not found: {template}")

            validator = adapter.get("validator")
            if not validator:
                add_issue(issues, "error", "missing_validator", f"{label} has no validator command")
            elif len(validator) > 1 and validator[0] in {"python", "node"} and not rel_exists(validator[1]):
                add_issue(issues, "error", "missing_validator_script", f"{label} validator not found: {validator[1]}")

            fixture_dir = ROOT / "validation_fixtures" / family / subtype
            if not fixture_dir.exists():
                add_issue(issues, "warning", "missing_fixture_dir", f"{label} fixture directory missing: {fixture_dir.relative_to(ROOT)}")
            elif not any(p.is_file() and p.name != ".gitkeep" for p in fixture_dir.rglob("*")):
                add_issue(issues, "warning", "empty_fixture_dir", f"{label} has no concrete regression fixture")


def audit_required_files(issues: list[dict[str, str]]) -> None:
    for rel in [
        "workflow/intent_rules.json",
        "workflow/game_type_rules.json",
        "workflow/stage_policy.json",
        "workflow/validation_policy.json",
        "workflow/execution_registry.json",
        "workflow/game_input_schemas.json",
        "resources/latest_resources.json",
        "scripts/save_game_config_via_cdp.js",
        "scripts/roundtrip_compare_config.js",
        "scripts/create_preview_url.js",
    ]:
        if not rel_exists(rel):
            add_issue(issues, "error", "missing_required_file", f"Required workflow file missing: {rel}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only")
    parser.add_argument("--allow-warnings", action="store_true", help="Exit 0 when only warnings are found")
    args = parser.parse_args()

    issues: list[dict[str, str]] = []
    audit_required_files(issues)
    audit_registry(issues)

    error_count = sum(1 for item in issues if item["severity"] == "error")
    warning_count = sum(1 for item in issues if item["severity"] == "warning")
    report = {
        "schema": "coursewaremaker.workflow_audit.v1",
        "root": str(ROOT),
        "error_count": error_count,
        "warning_count": warning_count,
        "issues": issues,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if error_count:
        return 2
    if warning_count and not args.allow_warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
