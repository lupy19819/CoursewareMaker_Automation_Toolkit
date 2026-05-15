#!/usr/bin/env python3
"""Run a deterministic CoursewareMaker production task end to end.

Current supported create path:
- template_game / monster from a Yach xlsx sheet.

The script is intentionally conservative: unsupported game subtypes fail with a
clear message instead of asking the model to improvise.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MONSTER_TEMPLATE_ID = "70a3010b-0b7a-11ef-b3a3-fa7902489df6"


class WorkflowRunError(RuntimeError):
    pass


def run(cmd: list[str], *, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    print("+ " + " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if proc.returncode != 0:
        raise WorkflowRunError(f"Command failed ({proc.returncode}): {' '.join(cmd)}")
    return proc


def run_json(cmd: list[str]) -> dict[str, Any]:
    proc = run(cmd)
    return json.loads(proc.stdout)


def safe_name(name: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff._-]+", "_", name).strip("_") or "courseware_task"


def route_message(message: str) -> dict[str, Any]:
    return run_json([sys.executable, "workflow/workflow_router.py", "-m", message])


def plan_route(route: dict[str, Any]) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "workflow/workflow_planner.py"],
        cwd=ROOT,
        input=json.dumps(route, ensure_ascii=False),
        text=True,
        capture_output=True,
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    plan = json.loads(proc.stdout)
    if proc.returncode != 0 or plan.get("status") != "ready":
        raise WorkflowRunError("Plan blocked: " + "; ".join(plan.get("blocked_reasons", [])))
    return plan


def run_monster_create(route: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    game_name = args.game_name or route.get("game_name")
    sheet_name = args.sheet or route.get("sheet_name")
    source_url = args.source_url or route.get("source_url")
    doc_id = args.yach_doc_id or route.get("yach_doc_id")
    if not game_name:
        raise WorkflowRunError("Missing game name")
    if not sheet_name:
        raise WorkflowRunError("Missing sheet name")
    if not args.xlsx and not source_url and not doc_id:
        raise WorkflowRunError("Missing xlsx path or Yach source URL/doc id")

    out_dir = (args.output_dir or ROOT / "output" / "courseware_runs" / safe_name(game_name)).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    xlsx_path = args.xlsx
    if not xlsx_path:
        fetch_args = [sys.executable, "scripts/fetch_yach_sheet.py", "--output", str(out_dir / f"{safe_name(game_name)}.xlsx")]
        if doc_id:
            fetch_args += ["--doc-id", doc_id]
        else:
            fetch_args += ["--url", source_url]
        fetched = run_json(fetch_args)
        xlsx_path = Path(fetched["xlsx_path"])

    filtered_resources = out_dir / f"{safe_name(game_name)}.resources.filtered.json"
    resource_manifest = out_dir / f"{safe_name(game_name)}.resources.manifest.json"
    run(
        [
            sys.executable,
            "scripts/resolve_sheet_resources.py",
            "--xlsx",
            str(xlsx_path),
            "--sheet",
            sheet_name,
            "--resources",
            str(args.resources),
            "--output",
            str(filtered_resources),
            "--manifest",
            str(resource_manifest),
        ]
    )

    config_path = out_dir / f"{safe_name(game_name)}.config.json"
    meta_path = out_dir / f"{safe_name(game_name)}.build-meta.json"
    run(
        [
            sys.executable,
            "scripts/build_sj6_monster_config.py",
            "--xlsx",
            str(xlsx_path),
            "--sheet",
            sheet_name,
            "--resources",
            str(filtered_resources),
            "--template",
            "reference_configs/monster/贪吃_reference_clean.json",
            "--output",
            str(config_path),
            "--meta",
            str(meta_path),
        ]
    )
    run(
        [
            sys.executable,
            "scripts/validate_monster_config.py",
            str(config_path),
            "--meta",
            str(meta_path),
            "--reference",
            "reference_configs/monster/贪吃_reference_clean.json",
        ]
    )

    if args.dry_run:
        result = {
            "dry_run": True,
            "game_name": game_name,
            "xlsx_path": str(xlsx_path),
            "config_path": str(config_path),
            "meta_path": str(meta_path),
            "resource_manifest": str(resource_manifest),
        }
        result_path = out_dir / f"{safe_name(game_name)}.dry-run-result.json"
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({**result, "result_path": str(result_path)}, ensure_ascii=False, indent=2))
        return result

    run(["node", "scripts/create_game_auto.js", game_name, MONSTER_TEMPLATE_ID, str(config_path)])
    latest_id = (ROOT / "latest_game_id.txt").read_text(encoding="utf-8").strip()
    if not latest_id:
        raise WorkflowRunError("create_game_auto.js did not write latest_game_id.txt")

    run(["node", "scripts/save_game_config_via_cdp.js", latest_id, str(config_path)])
    remote_path = out_dir / f"{safe_name(game_name)}.remote.config.json"
    run(["node", "scripts/roundtrip_compare_config.js", latest_id, str(config_path), str(remote_path)])
    preview_path = out_dir / f"{safe_name(game_name)}.preview.json"
    preview = run_json(["node", "scripts/create_preview_url.js", latest_id, str(preview_path)])

    result = {
        "game_name": game_name,
        "game_id": latest_id,
        "editor_url": f"https://coursewaremaker.speiyou.com/#/editor?game_id={latest_id}",
        "preview_url": preview.get("preview_url"),
        "xlsx_path": str(xlsx_path),
        "config_path": str(config_path),
        "meta_path": str(meta_path),
        "resource_manifest": str(resource_manifest),
        "remote_config_path": str(remote_path),
        "preview_manifest": str(preview_path),
    }
    result_path = out_dir / f"{safe_name(game_name)}.run-result.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({**result, "result_path": str(result_path)}, ensure_ascii=False, indent=2))
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--message", "-m", required=True)
    parser.add_argument("--game-name")
    parser.add_argument("--sheet")
    parser.add_argument("--source-url")
    parser.add_argument("--yach-doc-id")
    parser.add_argument("--xlsx", type=Path)
    parser.add_argument("--resources", type=Path, default=ROOT / "resources" / "latest_resources.json")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="Stop after source/resource/config generation and validation")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    route = route_message(args.message)
    plan_route(route)
    if route.get("intent") != "create_new_game":
        raise WorkflowRunError(f"Unsupported end-to-end intent: {route.get('intent')}")
    if route.get("game_family") != "template_game" or route.get("game_subtype") != "monster":
        raise WorkflowRunError(
            "End-to-end executor currently supports create_new_game for template_game/monster only. "
            "Use the subtype generator scripts for this route."
        )
    run_monster_create(route, args)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WorkflowRunError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
