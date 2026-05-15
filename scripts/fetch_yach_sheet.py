#!/usr/bin/env python3
"""Export a Yach/Shimo workbook to xlsx with cross-platform paths.

Configuration lookup order:
1. --config
2. YACH_CONFIG_FILE
3. ./.yach-config.json
4. ~/.openclaw/workspace/.yach-config.json

The config file must contain base_url, appkey, and appsecret.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "output" / "yach_exports"
YACH_DOC_ID_RE = re.compile(r"/sheets/(?P<doc_id>[^/?#]+)")


class YachError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def default_config_path() -> Path | None:
    candidates = [
        Path.cwd() / ".yach-config.json",
        Path.home() / ".openclaw" / "workspace" / ".yach-config.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def resolve_config_path(cli_path: str | None) -> Path:
    if cli_path:
        return Path(cli_path).expanduser().resolve()
    env_path = Path(value).expanduser().resolve() if (value := os.environ.get("YACH_CONFIG_FILE")) else None
    if env_path:
        return env_path
    path = default_config_path()
    if path:
        return path.resolve()
    raise YachError("Yach config not found. Pass --config or set YACH_CONFIG_FILE.")


def extract_doc_id(value: str) -> str:
    match = YACH_DOC_ID_RE.search(value)
    return match.group("doc_id") if match else value.strip()


def http_json(url: str, *, method: str = "GET", payload: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json;charset=UTF-8"},
        method=method,
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_access_token(config: dict[str, Any]) -> str:
    params = urllib.parse.urlencode({"appkey": config["appkey"], "appsecret": config["appsecret"]})
    data = http_json(f"{config['base_url'].rstrip('/')}/gettoken?{params}")
    if data.get("code") != 200 or not data.get("obj", {}).get("access_token"):
        raise YachError(f"Failed to get Yach token: {data}")
    return data["obj"]["access_token"]


def export_xlsx(config: dict[str, Any], token: str, doc_id: str, output_path: Path, poll_interval: float, timeout_seconds: int) -> Path:
    base = config["base_url"].rstrip("/")
    data = http_json(
        f"{base}/openapi/v2/doc/export/async",
        method="POST",
        payload={"file_guid": doc_id, "type": "xlsx", "access_token": token},
    )
    if data.get("code") != 200 or not data.get("obj", {}).get("task_id"):
        raise YachError(f"Yach export failed: {data}")

    task_id = data["obj"]["task_id"]
    deadline = time.time() + timeout_seconds
    poll_url = f"{base}/openapi/v2/doc/export/async/process"
    while time.time() < deadline:
        time.sleep(poll_interval)
        params = urllib.parse.urlencode({"task_id": task_id, "access_token": token})
        poll = http_json(f"{poll_url}?{params}")
        obj = poll.get("obj") or {}
        if poll.get("code") == 200 and obj.get("progress") == 100 and obj.get("download_url"):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(obj["download_url"], timeout=60) as resp:
                output_path.write_bytes(resp.read())
            return output_path
    raise YachError(f"Yach export timed out for doc_id={doc_id}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Yach/Shimo sheet URL")
    parser.add_argument("--doc-id", help="Yach file_guid/doc id. Overrides --url parsing.")
    parser.add_argument("--output", type=Path, help="Output .xlsx path")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--config", help="Path to .yach-config.json")
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument("--timeout-seconds", type=int, default=90)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.doc_id and not args.url:
        raise YachError("Pass --doc-id or --url")
    doc_id = extract_doc_id(args.doc_id or args.url)
    config_path = resolve_config_path(args.config)
    config = read_json(config_path)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = args.output or (args.output_dir / f"{doc_id}_{timestamp}.xlsx")
    token = get_access_token(config)
    result = export_xlsx(config, token, doc_id, output_path, args.poll_interval, args.timeout_seconds)
    print(json.dumps({"doc_id": doc_id, "xlsx_path": str(result), "config_path": str(config_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
