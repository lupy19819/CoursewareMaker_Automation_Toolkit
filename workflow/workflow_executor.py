#!/usr/bin/env python3
"""Single deterministic CoursewareMaker workflow executor.

This is the only automation execution entrypoint. It does not define a second
workflow. It routes the user message, asks the planner for ordered steps, guards
dangerous actions, then uses execution_registry.json to run fixed adapters.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = Path(__file__).resolve().parent


class ExecutorError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_name(name: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff._-]+", "_", name).strip("_") or "courseware_task"


def run(cmd: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    resolved = [sys.executable if item == "python" else item for item in cmd]
    print("+ " + " ".join(str(x) for x in resolved), flush=True)
    proc = subprocess.run(resolved, cwd=ROOT, input=input_text, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if proc.returncode != 0:
        raise ExecutorError(f"Command failed ({proc.returncode}): {' '.join(str(x) for x in resolved)}")
    return proc


def run_json(cmd: list[str], *, input_text: str | None = None) -> dict[str, Any]:
    return json.loads(run(cmd, input_text=input_text).stdout)


def route(message: str, args: argparse.Namespace) -> dict[str, Any]:
    cmd = [sys.executable, "workflow/workflow_router.py", "-m", message]
    if args.game_name:
        cmd += ["--game-name", args.game_name]
    if args.config_path:
        cmd += ["--config-path", str(args.config_path)]
    if args.game_family:
        cmd += ["--game-family", args.game_family]
    if args.game_subtype:
        cmd += ["--game-subtype", args.game_subtype]
    result = run_json(cmd)
    if args.input and not result.get("config_path"):
        result["config_path"] = str(args.input)
    if args.xlsx and not result.get("config_path"):
        result["config_path"] = str(args.xlsx)
    if args.sheet:
        result["sheet_name"] = args.sheet
    if args.source_url:
        result["source_url"] = args.source_url
    if args.yach_doc_id:
        result["yach_doc_id"] = args.yach_doc_id
    return result


def plan(route_result: dict[str, Any]) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "workflow/workflow_planner.py"],
        cwd=ROOT,
        input=json.dumps(route_result, ensure_ascii=False),
        text=True,
        capture_output=True,
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    parsed = json.loads(proc.stdout)
    if proc.returncode != 0 or parsed.get("status") != "ready":
        raise ExecutorError("Plan blocked: " + "; ".join(parsed.get("blocked_reasons", [])))
    return parsed


def guard(action: str, plan_result: dict[str, Any]) -> None:
    proc = subprocess.run(
        [sys.executable, "workflow/workflow_guard.py", "--action", action],
        cwd=ROOT,
        input=json.dumps(plan_result, ensure_ascii=False),
        text=True,
        capture_output=True,
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if proc.returncode != 0:
        raise ExecutorError(f"Guard blocked action '{action}'")


def adapter_for(route_result: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    family = route_result.get("game_family")
    subtype = route_result.get("game_subtype")
    adapter = registry.get("generation_adapters", {}).get(family, {}).get(subtype)
    if not adapter:
        raise ExecutorError(f"No execution adapter for {family}/{subtype}. Add it to workflow/execution_registry.json.")
    return adapter


def format_cmd(command: list[str], values: dict[str, Any]) -> list[str]:
    formatted = []
    for item in command:
        try:
            value = item.format(**values)
        except KeyError as exc:
            raise ExecutorError(f"Adapter command references missing value: {exc}") from exc
        if value not in {"", "None"}:
            formatted.append(value)
    return formatted


def choose_input(route_result: dict[str, Any], adapter: dict[str, Any], args: argparse.Namespace, out_dir: Path) -> tuple[Path, Path | None]:
    xlsx_path = args.xlsx
    input_path = args.input or args.config_path

    if adapter.get("input_format") == "xlsx":
        if not xlsx_path and (route_result.get("source_url") or route_result.get("yach_doc_id")):
            fetch_args = [sys.executable, "scripts/fetch_yach_sheet.py", "--output", str(out_dir / "source.xlsx")]
            if route_result.get("yach_doc_id"):
                fetch_args += ["--doc-id", route_result["yach_doc_id"]]
            else:
                fetch_args += ["--url", route_result["source_url"]]
            fetched = run_json(fetch_args)
            xlsx_path = Path(fetched["xlsx_path"])
        if not xlsx_path:
            raise ExecutorError("This route requires --xlsx or a Yach source URL/doc id.")
        return xlsx_path, None

    if adapter.get("input_format") == "json":
        if not input_path:
            raise ExecutorError("This route requires --input <dynamic_questions.json>.")
        return Path(input_path), None

    raise ExecutorError(f"Unsupported adapter input_format: {adapter.get('input_format')}")


def preflight_resources(input_path: Path, route_result: dict[str, Any], adapter: dict[str, Any], args: argparse.Namespace, out_dir: Path) -> dict[str, str]:
    support = adapter.get("supports_resource_filter")
    manifest = out_dir / "resources.manifest.json"
    if support == "sheet":
        sheet = args.sheet or route_result.get("sheet_name")
        if not sheet:
            raise ExecutorError("Sheet resource preflight requires a sheet name.")
        filtered = out_dir / "resources.filtered.json"
        run(
            [
                sys.executable,
                "scripts/resolve_sheet_resources.py",
                "--xlsx",
                str(input_path),
                "--sheet",
                sheet,
                "--resources",
                str(args.resources),
                "--output",
                str(filtered),
                "--manifest",
                str(manifest),
            ]
        )
        return {"filtered_resources": str(filtered), "resource_manifest": str(manifest)}
    if support == "json_manifest":
        run(
            [
                sys.executable,
                "scripts/resolve_input_resources.py",
                "--input",
                str(input_path),
                "--resources",
                str(args.resources),
                "--manifest",
                str(manifest),
            ]
        )
        return {"filtered_resources": "", "resource_manifest": str(manifest)}
    return {"filtered_resources": "", "resource_manifest": ""}


def generate_config(route_result: dict[str, Any], args: argparse.Namespace, out_dir: Path, adapter: dict[str, Any]) -> dict[str, str]:
    input_path, _ = choose_input(route_result, adapter, args, out_dir)
    resources = preflight_resources(input_path, route_result, adapter, args, out_dir)
    game_name = args.game_name or route_result.get("game_name") or route_result.get("game_subtype") or "courseware"
    config_path = out_dir / f"{safe_name(game_name)}.config.json"
    meta_path = out_dir / f"{safe_name(game_name)}.build-meta.json"
    template = args.template or adapter.get("default_template") or route_result.get("baseline") or ""
    sheet = args.sheet or route_result.get("sheet_name") or ""
    if adapter.get("requires_sheet") and not sheet:
        raise ExecutorError("This adapter requires --sheet or a sheet name in the message.")
    if adapter.get("requires_options") and not args.options:
        raise ExecutorError("This adapter requires --options <2|3|4>.")

    values = {
        "input": str(input_path),
        "xlsx": str(input_path),
        "sheet": sheet,
        "template": str(template),
        "config": str(config_path),
        "meta": str(meta_path),
        "filtered_resources": resources["filtered_resources"],
        "options": str(args.options or ""),
    }
    run(format_cmd(adapter["command"], values))

    # Some legacy generators still choose their output path internally.
    legacy_output = ROOT / f"{sheet}.config.json" if sheet else None
    legacy_meta = ROOT / f"{sheet}.build-meta.json" if sheet else None
    if legacy_output and legacy_output.exists() and not config_path.exists():
        shutil.move(str(legacy_output), str(config_path))
    if legacy_meta and legacy_meta.exists() and not meta_path.exists():
        shutil.move(str(legacy_meta), str(meta_path))
    if not config_path.exists():
        raise ExecutorError(f"Generator did not produce expected config: {config_path}")

    validator = adapter.get("validator")
    if validator:
        run(format_cmd(validator, {**values, "config": str(config_path), "meta": str(meta_path)}))

    return {
        "input_path": str(input_path),
        "config_path": str(config_path),
        "meta_path": str(meta_path) if meta_path.exists() else "",
        **resources,
    }


def create_save_preview(route_result: dict[str, Any], plan_result: dict[str, Any], args: argparse.Namespace, out_dir: Path, generated: dict[str, str], registry: dict[str, Any]) -> dict[str, str]:
    if args.dry_run:
        return {}
    game_name = args.game_name or route_result.get("game_name")
    if not game_name:
        raise ExecutorError("Creating a game requires a game name.")

    template_ids = registry["template_ids"]
    template_id = args.template_id or (
        template_ids["yundong_pk"] if route_result.get("game_family") == "yundong_pk" else template_ids["default_template_game"]
    )

    guard("create_game", plan_result)
    run(["node", "scripts/create_game_auto.js", game_name, template_id, generated["config_path"]])
    game_id = (ROOT / "latest_game_id.txt").read_text(encoding="utf-8").strip()
    if not game_id:
        raise ExecutorError("create_game_auto.js did not write latest_game_id.txt")

    guard("roundtrip_compare", plan_result)
    run(["node", "scripts/save_game_config_via_cdp.js", game_id, generated["config_path"]])
    remote_path = out_dir / f"{safe_name(game_name)}.remote.config.json"
    run(["node", "scripts/roundtrip_compare_config.js", game_id, generated["config_path"], str(remote_path)])
    preview_path = out_dir / f"{safe_name(game_name)}.preview.json"
    preview = run_json(["node", "scripts/create_preview_url.js", game_id, str(preview_path)])

    return {
        "game_id": game_id,
        "editor_url": f"https://coursewaremaker.speiyou.com/#/editor?game_id={game_id}",
        "preview_url": preview.get("preview_url", ""),
        "remote_config_path": str(remote_path),
        "preview_manifest": str(preview_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--message", "-m", required=True)
    parser.add_argument("--input", type=Path, help="Dynamic question JSON for JSON-based generators")
    parser.add_argument("--xlsx", type=Path, help="Question workbook for Excel-based generators")
    parser.add_argument("--sheet")
    parser.add_argument("--source-url")
    parser.add_argument("--yach-doc-id")
    parser.add_argument("--game-name")
    parser.add_argument("--game-family", choices=["yundong_pk", "template_game", "standard_component"])
    parser.add_argument("--game-subtype")
    parser.add_argument("--config-path", type=Path)
    parser.add_argument("--template")
    parser.add_argument("--template-id")
    parser.add_argument("--options", type=int, choices=[2, 3, 4], help="Reading game option count")
    parser.add_argument("--resources", type=Path, default=ROOT / "resources" / "latest_resources.json")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="Stop after source/resource/config generation and validation")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    route_result = route(args.message, args)
    plan_result = plan(route_result)
    registry = load_json(WORKFLOW_DIR / "execution_registry.json")
    adapter = adapter_for(route_result, registry)

    game_name = args.game_name or route_result.get("game_name") or route_result.get("game_subtype") or "courseware_task"
    out_dir = (args.output_dir or ROOT / "output" / "courseware_runs" / safe_name(game_name)).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    generated = generate_config(route_result, args, out_dir, adapter)
    online = {}
    if route_result.get("intent") == "create_new_game":
        online = create_save_preview(route_result, plan_result, args, out_dir, generated, registry)
    elif route_result.get("intent") in {"new_production_task", "inspect_or_compare"}:
        pass
    else:
        raise ExecutorError(f"Executor does not yet automate intent: {route_result.get('intent')}")

    result = {
        "schema": "coursewaremaker.workflow.execution_result.v1",
        "dry_run": bool(args.dry_run),
        "intent": route_result.get("intent"),
        "game_family": route_result.get("game_family"),
        "game_subtype": route_result.get("game_subtype"),
        "game_name": game_name,
        **generated,
        **online,
    }
    result_path = out_dir / f"{safe_name(game_name)}.execution-result.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({**result, "result_path": str(result_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ExecutorError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
