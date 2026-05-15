#!/usr/bin/env python3
"""Guard requested actions against a deterministic CoursewareMaker plan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def read_plan(path: str | None) -> dict[str, Any]:
    if path:
        with Path(path).open(encoding="utf-8") as f:
            return json.load(f)
    return json.load(sys.stdin)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", help="Path to planner JSON. Reads stdin if omitted.")
    parser.add_argument("--action", required=True, help="Action to check, e.g. create_game or save_existing")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    plan = read_plan(args.plan)
    allowed = set(plan.get("allowed_actions", []))
    forbidden = set(plan.get("forbidden_actions", []))
    steps = {step.get("action") for step in plan.get("steps", [])}

    result: dict[str, Any] = {
        "schema": "coursewaremaker.workflow.guard.v1",
        "action": args.action,
        "intent": plan.get("intent"),
        "stage": plan.get("stage"),
        "status": "allowed",
        "reason": None,
    }

    if plan.get("status") == "blocked":
        result["status"] = "blocked"
        result["reason"] = "Plan is blocked: " + "; ".join(plan.get("blocked_reasons", []))
    elif args.action in forbidden:
        result["status"] = "blocked"
        result["reason"] = f"Action '{args.action}' is forbidden for intent '{plan.get('intent')}'."
    elif args.action not in allowed and args.action not in steps:
        result["status"] = "blocked"
        result["reason"] = f"Action '{args.action}' is not present in allowed actions or planned steps."

    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0 if result["status"] == "allowed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
