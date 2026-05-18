#!/usr/bin/env python3
"""Resolve resource-like values referenced by a dynamic JSON input file.

This is a conservative preflight helper for template-game generators whose
question data is JSON rather than Excel. It does not rewrite the input. It only
reports resource names/URLs used by the current task so the workflow can block
on missing or duplicate task resources without depending on model judgment.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESOURCES = ROOT / "resources" / "latest_resources.json"
DEFAULT_SCHEMAS = ROOT / "workflow" / "game_input_schemas.json"
URL_RE = re.compile(r"^https?://", re.IGNORECASE)
RESOURCE_KEY_RE = re.compile(r"(audio|image|img|sprite|scene|sound|url|resource)", re.IGNORECASE)


class ResolveError(RuntimeError):
    pass


def clean(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def load_rows(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw if isinstance(raw, list) else raw.get("rows", [])
    if not isinstance(rows, list):
        raise ResolveError(f"Resource file must be a list or contain rows[]: {path}")
    return rows


def row_name(row: dict[str, Any]) -> str | None:
    return clean(row.get("name") or row.get("名字"))


def normalize_category(row: dict[str, Any]) -> str:
    category = str(row.get("category") or row.get("type") or "").lower()
    url = str(row.get("url") or row.get("URL") or "")
    if category:
        return category
    if "/audio/" in url or url.lower().endswith((".mp3", ".wav", ".m4a")):
        return "audio"
    if "/image/" in url or url.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        return "image"
    return ""


def infer_category(key_path: str, value: str) -> str | None:
    lowered = f"{key_path} {value}".lower()
    if "audio" in lowered or "sound" in lowered or value.lower().endswith((".mp3", ".wav", ".m4a")):
        return "audio"
    if any(token in lowered for token in ("image", "img", "sprite", "scene")) or value.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        return "image"
    return None


def walk(value: Any, key_path: str = "") -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            next_path = f"{key_path}.{key}" if key_path else str(key)
            found.extend(walk(child, next_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(walk(child, f"{key_path}[{index}]"))
    else:
        string = clean(value)
        if not string:
            return found
        if URL_RE.search(string) or RESOURCE_KEY_RE.search(key_path):
            category = infer_category(key_path, string)
            found.append({"path": key_path, "value": string, "category": category or ""})
    return found


def schema_resource_keys(schema_path: Path, family: str | None, subtype: str | None) -> set[str]:
    if not family or not subtype:
        return set()
    schemas = json.loads(schema_path.read_text(encoding="utf-8"))
    contract = schemas.get(family, {}).get(subtype, {})
    fields = contract.get("resource_fields", {})
    keys: set[str] = set()
    for values in fields.values():
        keys.update(str(item) for item in values)
    return keys


def walk_schema(value: Any, resource_keys: set[str], key_path: str = "") -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            next_path = f"{key_path}.{key}" if key_path else str(key)
            if str(key) in resource_keys:
                for ref in collect_strings(child, next_path):
                    found.append(ref)
            else:
                found.extend(walk_schema(child, resource_keys, next_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(walk_schema(child, resource_keys, f"{key_path}[{index}]"))
    return found


def collect_strings(value: Any, key_path: str) -> list[dict[str, str]]:
    if isinstance(value, str):
        string = clean(value)
        if not string:
            return []
        return [{"path": key_path, "value": string, "category": infer_category(key_path, string) or ""}]
    if isinstance(value, list):
        found: list[dict[str, str]] = []
        for index, child in enumerate(value):
            found.extend(collect_strings(child, f"{key_path}[{index}]"))
        return found
    if isinstance(value, dict):
        found = []
        for key, child in value.items():
            found.extend(collect_strings(child, f"{key_path}.{key}"))
        return found
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--resources", type=Path, default=DEFAULT_RESOURCES)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--allow-duplicates", action="store_true")
    parser.add_argument("--schema-family")
    parser.add_argument("--schema-subtype")
    parser.add_argument("--schema-file", type=Path, default=DEFAULT_SCHEMAS)
    args = parser.parse_args()

    if not args.input.exists():
        raise ResolveError(f"Input JSON not found: {args.input}")
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    resource_keys = schema_resource_keys(args.schema_file, args.schema_family, args.schema_subtype)
    refs = walk_schema(payload, resource_keys) if resource_keys else walk(payload)
    rows = load_rows(args.resources)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        name = row_name(row)
        if name:
            grouped[name].append(row)

    named_refs = [ref for ref in refs if not URL_RE.search(ref["value"])]
    urls = [ref for ref in refs if URL_RE.search(ref["value"])]
    missing = sorted({ref["value"] for ref in named_refs if ref["value"] not in grouped})
    duplicates = {ref["value"]: len(grouped[ref["value"]]) for ref in named_refs if len(grouped.get(ref["value"], [])) > 1}
    mismatches = []
    for ref in named_refs:
        expected = ref.get("category")
        if not expected or ref["value"] not in grouped:
            continue
        actual = normalize_category(grouped[ref["value"]][-1])
        if actual and expected and actual != expected:
            mismatches.append({"path": ref["path"], "name": ref["value"], "expected": expected, "actual": actual})

    manifest = {
        "schema": "coursewaremaker.resource_manifest.v1",
        "input": str(args.input),
        "resource_file": str(args.resources),
        "referenced_count": len(refs),
        "named_count": len(named_refs),
        "url_count": len(urls),
        "missing": missing,
        "duplicates": duplicates,
        "mismatches": mismatches,
        "references": refs,
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))

    if missing:
        raise ResolveError("Missing resources: " + ", ".join(missing))
    if mismatches:
        raise ResolveError("Resource category mismatches found")
    if duplicates and not args.allow_duplicates:
        raise ResolveError("Duplicate resources used by this input: " + ", ".join(sorted(duplicates)))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ResolveError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(2)
