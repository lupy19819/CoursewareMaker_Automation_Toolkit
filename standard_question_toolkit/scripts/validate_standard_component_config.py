#!/usr/bin/env python3
"""Deterministic validator for standard-component CoursewareMaker configs.

This main-workflow validator checks the stable contract that can be enforced
across devices and template versions. The stricter Node layout/skin diagnostic
remains available for manual audits, but it is too template-version-sensitive
to be the default save blocker.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def unwrap(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict) and "result" in raw and isinstance(raw["result"], dict) and "configuration" in raw["result"]:
        cfg = raw["result"]["configuration"]
        return json.loads(cfg) if isinstance(cfg, str) else cfg
    if isinstance(raw, dict) and isinstance(raw.get("configuration"), str):
        return json.loads(raw["configuration"])
    if isinstance(raw, dict):
        return raw
    raise ValueError("config root must be an object")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    args = parser.parse_args()

    config = unwrap(json.loads(args.config.read_text(encoding="utf-8")))
    levels = config.get("game")
    if not isinstance(levels, list) or not levels:
        raise ValueError("standard_component config must contain non-empty game[]")

    component_count = 0
    typed_component_count = 0
    for index, level in enumerate(levels, 1):
        components = level.get("components")
        if not isinstance(components, list) or not components:
            raise ValueError(f"L{index}: missing non-empty components[]")
        component_count += len(components)
        typed = [comp for comp in components if isinstance(comp, dict) and comp.get("component_id")]
        if not typed:
            raise ValueError(f"L{index}: no component_id found")
        typed_component_count += len(typed)
        for comp in typed:
            component_data = comp.get("component_data")
            if not isinstance(component_data, dict):
                raise ValueError(f"L{index}: typed component missing component_data")
            if "states" in component_data and not isinstance(component_data["states"], list):
                raise ValueError(f"L{index}: component states must be a list")

    print(json.dumps(
        {
            "schema": "coursewaremaker.standard_component_validation.v1",
            "config": str(args.config),
            "level_count": len(levels),
            "component_count": component_count,
            "typed_component_count": typed_component_count,
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(2)
