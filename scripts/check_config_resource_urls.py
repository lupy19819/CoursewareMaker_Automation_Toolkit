#!/usr/bin/env python3
"""Inspect generated config resource URLs in component state sources."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


URL_RE = re.compile(r"^https?://", re.IGNORECASE)
RESOURCE_KEY_RE = re.compile(r"(audio|image|img|sprite|scene|sound|url|resource|msprite|maudio)", re.IGNORECASE)
NON_RESOURCE_VALUE_KEYS = {"audioType", "key", "animation", "state", "label", "name", "component_name", "component_id"}


class CheckError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_strings(value: Any, path: str = "") -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            found.extend(iter_strings(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(iter_strings(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        found.append({"path": path, "value": value})
    return found


def inspect_component_sources(value: Any, path: str = "") -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    urls: list[dict[str, str]] = []
    suspicious: list[dict[str, str]] = []
    if isinstance(value, dict):
        source = value.get("source")
        if isinstance(source, dict):
            for source_key in ("MSprite", "MAudio"):
                item = source.get(source_key)
                if isinstance(item, dict) and isinstance(item.get("value"), str) and item["value"]:
                    item_path = f"{path}.source.{source_key}.value" if path else f"source.{source_key}.value"
                    row = {"path": item_path, "source": source_key, "value": item["value"]}
                    if URL_RE.search(item["value"]):
                        urls.append(row)
                    else:
                        suspicious.append(row)
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            child_urls, child_suspicious = inspect_component_sources(child, child_path)
            urls.extend(child_urls)
            suspicious.extend(child_suspicious)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_urls, child_suspicious = inspect_component_sources(child, f"{path}[{index}]")
            urls.extend(child_urls)
            suspicious.extend(child_suspicious)
    return urls, suspicious


def suspicious_resource_strings(value: Any) -> list[dict[str, str]]:
    found = []
    for item in iter_strings(value):
        string = item["value"].strip()
        if not string or URL_RE.search(string):
            continue
        key = item["path"].rsplit(".", 1)[-1]
        if key in NON_RESOURCE_VALUE_KEYS:
            continue
        if key == "value" and RESOURCE_KEY_RE.search(item["path"]):
            found.append(item)
        elif key.endswith(("_url", "_urls", "_audio", "_image", "_img")) or RESOURCE_KEY_RE.search(key):
            found.append(item)
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="Generated config JSON to inspect.")
    parser.add_argument("--expect", action="append", default=[], help="Substring expected anywhere in config strings.")
    args = parser.parse_args()

    config = load_json(args.config)
    strings = iter_strings(config)
    urls, source_suspicious = inspect_component_sources(config)
    resource_suspicious = suspicious_resource_strings(config)
    missing = [
        expected
        for expected in args.expect
        if not any(expected in item["value"] for item in strings)
    ]

    summary = {
        "schema": "coursewaremaker.config_resource_url_check.v1",
        "config": str(args.config),
        "source_url_count": len(urls),
        "suspicious_source_value_count": len(source_suspicious),
        "suspicious_resource_string_count": len(resource_suspicious),
        "expectations": args.expect,
        "missing_expectations": missing,
        "source_urls": urls,
        "suspicious_source_values": source_suspicious,
        "suspicious_resource_strings": resource_suspicious,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if missing:
        raise CheckError("Missing expected config strings: " + ", ".join(missing))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CheckError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(2)
