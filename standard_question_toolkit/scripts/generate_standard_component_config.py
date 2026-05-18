#!/usr/bin/env python3
"""Deterministic standard-component config passthrough.

This wrapper deliberately does not ask a model to synthesize standard questions.
Until a specific standard-question generator is selected, production automation
accepts only an already generated CoursewareMaker config or detail wrapper and
normalizes it to an inner configuration JSON.
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
    if isinstance(raw, dict) and isinstance(raw.get("game"), list):
        return raw
    raise ValueError(
        "standard_component deterministic executor currently requires an existing config object "
        "with game[] or a CoursewareMaker detail wrapper"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--meta", type=Path)
    args = parser.parse_args()

    config = unwrap(json.loads(args.input.read_text(encoding="utf-8")))
    if not isinstance(config.get("game"), list) or not config["game"]:
        raise ValueError("standard_component config must contain non-empty game[]")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.meta:
        args.meta.parent.mkdir(parents=True, exist_ok=True)
        args.meta.write_text(
            json.dumps(
                {
                    "schema": "coursewaremaker.standard_component.build_meta.v1",
                    "input": str(args.input),
                    "output": str(args.output),
                    "level_count": len(config["game"]),
                    "mode": "passthrough_existing_config",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    print(json.dumps({"output": str(args.output), "level_count": len(config["game"])}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
