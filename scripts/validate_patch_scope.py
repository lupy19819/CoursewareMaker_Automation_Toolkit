#!/usr/bin/env python3
"""Validate that a config repair changed only allowed JSON path prefixes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class ScopeError(RuntimeError):
    pass


def load_config(path: Path) -> Any:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "result" in raw and "configuration" in raw["result"]:
        cfg = raw["result"]["configuration"]
        return json.loads(cfg) if isinstance(cfg, str) else cfg
    if isinstance(raw, dict) and isinstance(raw.get("configuration"), str):
        return json.loads(raw["configuration"])
    return raw


def flatten(value: Any, prefix: str = "$") -> dict[str, Any]:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            result.update(flatten(child, f"{prefix}.{key}"))
        if not value:
            result[prefix] = {}
        return result
    if isinstance(value, list):
        result = {}
        for index, child in enumerate(value):
            result.update(flatten(child, f"{prefix}[{index}]"))
        if not value:
            result[prefix] = []
        return result
    return {prefix: value}


def changed_paths(before: Any, after: Any) -> list[str]:
    left = flatten(before)
    right = flatten(after)
    paths = sorted(set(left) | set(right))
    return [path for path in paths if left.get(path) != right.get(path)]


def is_allowed(path: str, prefixes: list[str]) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in prefixes)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--allow", action="append", required=True, help="Allowed JSON path prefix, e.g. $.game[2].components")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    changes = changed_paths(load_config(args.before), load_config(args.after))
    violations = [path for path in changes if not is_allowed(path, args.allow)]
    report = {
        "schema": "coursewaremaker.patch_scope_report.v1",
        "before": str(args.before),
        "after": str(args.after),
        "allowed_prefixes": args.allow,
        "changed_count": len(changes),
        "violation_count": len(violations),
        "changed_paths": changes,
        "violations": violations,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if violations:
        raise ScopeError("Patch touched paths outside allowed prefixes")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ScopeError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(2)
