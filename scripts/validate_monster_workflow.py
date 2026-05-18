#!/usr/bin/env python3
"""Run the full deterministic validation stack for monster configs."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, cwd=ROOT, text=True)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--meta", type=Path)
    parser.add_argument("--reference", type=Path, default=Path("reference_configs/monster/贪吃_reference_clean.json"))
    parser.add_argument("--reference-index", type=Path, default=Path("reference_configs/level_references/index.json"))
    parser.add_argument("--reference-policy", choices=["warn", "require"], default="warn")
    args = parser.parse_args()

    monster_cmd = [
        sys.executable,
        "scripts/validate_monster_config.py",
        str(args.config),
        "--reference",
        str(args.reference),
    ]
    if args.meta:
        monster_cmd.extend(["--meta", str(args.meta)])
    run(monster_cmd)

    run([
        sys.executable,
        "scripts/validate_template_game_config.py",
        str(args.config),
        "--subtype",
        "monster",
        "--reference-index",
        str(args.reference_index),
        "--reference-policy",
        args.reference_policy,
    ])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
