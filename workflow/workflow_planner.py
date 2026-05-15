#!/usr/bin/env python3
"""Build a deterministic CoursewareMaker workflow plan from router output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


WORKFLOW_DIR = Path(__file__).resolve().parent


def load_json(name: str) -> Any:
    with (WORKFLOW_DIR / name).open(encoding="utf-8") as f:
        return json.load(f)


def read_route(path: str | None) -> dict[str, Any]:
    if path:
        with Path(path).open(encoding="utf-8") as f:
            return json.load(f)
    return json.load(sys.stdin)


def has_any(route: dict[str, Any], groups: list[list[str]]) -> bool:
    if not groups:
        return True
    for group in groups:
        if not group:
            return True
        if any(route.get(field) for field in group):
            return True
    return False


def missing_fields(route: dict[str, Any], required: list[str]) -> list[str]:
    return [field for field in required if not route.get(field)]


def script_for_generation(route: dict[str, Any], registry: dict[str, Any]) -> str | None:
    family = route.get("game_family")
    subtype = route.get("game_subtype")
    generation = registry["generation"].get(family)
    if not generation:
        return None
    return generation.get(subtype) or generation.get("default")


def validation_steps(route: dict[str, Any], validation: dict[str, Any], include_main_workflow: bool = True) -> list[dict[str, str]]:
    family = route.get("game_family")
    if not family or family not in validation["policies"]:
        return []
    policy = validation["policies"][family]
    steps: list[dict[str, str]] = []
    subtype = route.get("game_subtype")
    subtype_policy = {}
    if family == "template_game":
        subtype_policy = policy.get("subtype_validators", {}).get(subtype, {})

    for layer_id in policy.get("main_workflow_layers", []):
        if not include_main_workflow and layer_id in {"roundtrip_compare", "preview"}:
            continue
        layer_def = next((layer for layer in validation.get("strategy", {}).get("layers", []) if layer.get("id") == layer_id), {})
        scope = layer_def.get("scope", "single_game")
        step: dict[str, str] = {
            "action": "validate",
            "layer": layer_id,
            "scope": scope,
            "required": str(layer_def.get("required", True)).lower(),
        }
        if layer_id == "rules_validator":
            validators = subtype_policy.get("rules_validator") if subtype_policy else policy.get("rules_validator", policy.get("validators", []))
            step["validator"] = " | ".join(validators) if isinstance(validators, list) else str(validators)
        elif layer_id == "reference_invariants":
            invariants = subtype_policy.get("reference_invariants") if subtype_policy else policy.get("reference_invariants", [])
            step["reference"] = " | ".join(invariants) if isinstance(invariants, list) else str(invariants)
        elif layer_id == "fixture_regression":
            fixture = subtype_policy.get("fixture_regression") if subtype_policy else policy.get("fixture_regression", {})
            if isinstance(fixture, dict):
                step["fixture_path"] = fixture.get("path", "")
                step["fixture_status"] = fixture.get("status", "unknown")
            else:
                step["fixture_path"] = str(fixture)
                step["fixture_status"] = "optional"
        elif layer_id == "roundtrip_compare":
            step["scope"] = "main_workflow"
            step["method"] = "GET remote configuration and normalized local-vs-remote compare"
        elif layer_id == "preview":
            step["scope"] = "main_workflow"
            step["method"] = "browser preview smoke test"
        steps.append(step)
    return steps


def build_steps(route: dict[str, Any], registry: dict[str, Any], validation: dict[str, Any]) -> list[dict[str, Any]]:
    intent = route["intent"]
    scripts = registry["scripts"]
    steps: list[dict[str, Any]] = []

    if intent == "monitor_manual_operation":
        return [{"action": "start_monitor", "script": registry["monitors"]["manual_operation"]}]

    if intent in {"config_repair", "import_to_existing_game", "preview_or_publish", "inspect_or_compare"}:
        if route.get("game_name") and not route.get("game_id"):
            steps.append({"action": "resolve_existing_target", "method": "exact_game_name_lookup", "game_name": route["game_name"]})
        elif route.get("game_id"):
            steps.append({"action": "fetch_game_detail", "game_id": route["game_id"]})

    if intent == "new_production_task":
        steps.extend(
            [
                {"action": "sync_resources", "script": scripts["resource_sync"]},
                {"action": "confirm_same_name_resources", "blocking": True},
                {"action": "split_and_lock_batch", "game_family": route.get("game_family"), "game_subtype": route.get("game_subtype")},
            ]
        )
        gen_script = script_for_generation(route, registry)
        if gen_script:
            steps.append({"action": "generate_config", "script": gen_script})
        steps.extend(validation_steps(route, validation))

    if intent == "create_new_game":
        if route.get("source_url") or route.get("yach_doc_id"):
            steps.append({"action": "fetch_question_source", "script": scripts.get("fetch_yach_sheet"), "source_url": route.get("source_url"), "doc_id": route.get("yach_doc_id")})
        if route.get("sheet_name"):
            steps.append({"action": "resolve_sheet_resources", "script": scripts.get("resolve_sheet_resources"), "sheet_name": route.get("sheet_name")})
        gen_script = script_for_generation(route, registry)
        if gen_script and (route.get("config_path") or route.get("source_url") or route.get("yach_doc_id")):
            steps.append({"action": "generate_config", "script": gen_script})
            steps.extend(validation_steps(route, validation, include_main_workflow=False))
        steps.append(
            {
                "action": "create_game",
                "script": scripts["create_game"],
                "game_name": route.get("game_name"),
                "game_type": route.get("game_type"),
                "editor_entry": route.get("editor_entry"),
            }
        )
        if route.get("config_path") or route.get("source_url") or route.get("yach_doc_id"):
            steps.append({"action": "save_existing", "script": scripts["save_via_cdp"], "config_path": route.get("config_path") or "<generated_config>"})
            steps.append({"action": "roundtrip_compare", "script": scripts.get("roundtrip_compare")})
            steps.append({"action": "preview", "script": scripts.get("create_preview_url")})

    if intent == "import_to_existing_game":
        steps.extend(validation_steps(route, validation))
        steps.append({"action": "save_existing", "script": scripts["save_via_cdp"], "config_path": route.get("config_path")})
        steps.append({"action": "roundtrip_compare"})

    if intent == "config_repair":
        steps.append({"action": "patch_feedback_scope", "scope": route.get("feedback_scope"), "minimal_change": True})
        steps.extend(validation_steps(route, validation))
        if route.get("game_id") or route.get("game_name"):
            steps.append({"action": "save_existing", "script": scripts["save_via_cdp"], "config_path": route.get("config_path")})
            steps.append({"action": "roundtrip_compare"})

    if intent == "inspect_or_compare":
        steps.extend(validation_steps(route, validation))
        steps.append({"action": "report"})

    if intent == "preview_or_publish":
        if "发布" in route.get("message", ""):
            steps.append({"action": "publish_if_explicit", "script": scripts["publish_game"]})
        else:
            steps.append({"action": "generate_share_link", "script": scripts["share_link"]})

    return steps


def build_plan(route: dict[str, Any]) -> dict[str, Any]:
    stage_policy = load_json("stage_policy.json")
    registry = load_json("script_registry.json")
    validation = load_json("validation_policy.json")
    policy = stage_policy["policies"][route["intent"]]

    blocked_reasons = []
    if route.get("blocked_reason"):
        blocked_reasons.append(route["blocked_reason"])
    if not has_any(route, policy.get("required_any", [])):
        blocked_reasons.append(policy["block_if_missing"])
    missing = missing_fields(route, policy.get("required_fields", []))
    if missing:
        blocked_reasons.append(f"缺少必填字段: {', '.join(missing)}。{policy['block_if_missing']}")

    plan = {
        "schema": "coursewaremaker.workflow.plan.v1",
        "planner_version": stage_policy["version"],
        "status": "blocked" if blocked_reasons else "ready",
        "blocked_reasons": [reason for reason in blocked_reasons if reason],
        "intent": route["intent"],
        "stage": route["stage"],
        "allowed_actions": policy["allowed_actions"],
        "forbidden_actions": policy["forbidden_actions"],
        "locked_context": {
            "game_id": route.get("game_id"),
            "game_name": route.get("game_name"),
            "config_path": route.get("config_path"),
            "source_url": route.get("source_url"),
            "yach_doc_id": route.get("yach_doc_id"),
            "sheet_name": route.get("sheet_name"),
            "feedback_scope": route.get("feedback_scope"),
            "game_family": route.get("game_family"),
            "game_subtype": route.get("game_subtype"),
            "data_shape": route.get("data_shape"),
            "game_type": route.get("game_type"),
            "editor_entry": route.get("editor_entry"),
            "baseline": route.get("baseline"),
        },
        "steps": [] if blocked_reasons else build_steps(route, registry, validation),
    }
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route", help="Path to router JSON. Reads stdin if omitted.")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    plan = build_plan(read_route(args.route))
    print(json.dumps(plan, ensure_ascii=False, indent=2 if args.pretty else None))
    return 2 if plan["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
