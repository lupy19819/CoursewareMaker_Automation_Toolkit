#!/usr/bin/env python3
"""Build per-level reference profiles for CoursewareMaker template games.

Whole-game references are useful as skeletons, but validation needs to reason
per level because one reference game can mix different formats: for example a
3-slot level and a 4-slot level in the same reading game. This script extracts
each level into an indexed reference library with stable structural signatures.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_ROOT = ROOT / "reference_configs"
OUT_ROOT = REFERENCE_ROOT / "level_references"


REFERENCE_SOURCES = [
    ("monster", REFERENCE_ROOT / "monster", "*.json"),
    ("road_adventure", REFERENCE_ROOT, "road_adventure_ref.json"),
    ("bridge", REFERENCE_ROOT, "guoqiao*_ref.json"),
    ("amusement_park", REFERENCE_ROOT, "kaixin*_ref.json"),
    ("spelling", REFERENCE_ROOT, "spelling*_ref*.json"),
    ("magic_spelling", REFERENCE_ROOT / "mofappl_configs", "*.json"),
    ("fanboat", REFERENCE_ROOT / "reading" / "fanboat_configs_all", "*.json"),
    ("train", REFERENCE_ROOT / "reading" / "train_configs_all", "*.json"),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def unwrap_config(raw: Any) -> dict[str, Any] | None:
    if isinstance(raw, dict) and "result" in raw and isinstance(raw["result"], dict) and "configuration" in raw["result"]:
        cfg = raw["result"]["configuration"]
        return json.loads(cfg) if isinstance(cfg, str) else cfg
    if isinstance(raw, dict) and isinstance(raw.get("configuration"), str):
        return json.loads(raw["configuration"])
    if isinstance(raw, dict) and isinstance(raw.get("game"), list):
        return raw
    return None


def component_display_name(comp: dict[str, Any]) -> str:
    return str(comp.get("component_data", {}).get("name") or comp.get("name") or comp.get("component_name") or "")


def component_outer_name(comp: dict[str, Any]) -> str:
    return str(comp.get("name") or component_display_name(comp))


def component_base(comp: dict[str, Any]) -> str:
    return str(comp.get("component_data", {}).get("base") or comp.get("component_name") or "")


def tools(comp: dict[str, Any]) -> dict[str, Any]:
    return comp.get("component_data", {}).get("components", {}).get("tools", {})


def state_source_keys(comp: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for state in comp.get("component_data", {}).get("states", []):
        source = state.get("source", {})
        if isinstance(source, dict):
            keys.update(str(key) for key in source)
    return keys


def source_values(comp: dict[str, Any], source_key: str) -> list[str]:
    values: list[str] = []
    for state in comp.get("component_data", {}).get("states", []):
        item = state.get("source", {}).get(source_key)
        if isinstance(item, dict) and item.get("value") not in (None, "", []):
            values.append(str(item["value"]))
    return values


def is_choice_component(comp: dict[str, Any]) -> bool:
    name = component_display_name(comp)
    outer = component_outer_name(comp)
    comp_tools = tools(comp)
    return (
        outer == "AloneClickChoice"
        or "AloneClickChoice" in comp_tools
        or "MDraggable" in comp_tools
        or any(keyword in name for keyword in ("选项", "拖拽", "物品", "词卡"))
    )


def is_prompt_component(comp: dict[str, Any]) -> bool:
    name = component_display_name(comp)
    outer = component_outer_name(comp)
    return (
        outer in {"TitleStem", "QuestionStem"}
        or any(keyword in name for keyword in ("题干", "题目", "问题", "配图", "语音", "音频", "播放按钮"))
        # 公路大冒险文本题的题干承载节点历史上叫“节点”。
        or (name == "节点" and "MLabel" in state_source_keys(comp))
    )


def modality_profile(components: list[dict[str, Any]]) -> dict[str, Any]:
    prompt_components = [comp for comp in components if is_prompt_component(comp)]
    option_components = [comp for comp in components if is_choice_component(comp)]

    def count_with(comps: list[dict[str, Any]], source_key: str) -> int:
        return sum(1 for comp in comps if source_key in state_source_keys(comp))

    def count_values(comps: list[dict[str, Any]], source_key: str) -> int:
        return sum(1 for comp in comps if source_values(comp, source_key))

    prompt_text = count_with(prompt_components, "MLabel")
    prompt_audio = count_with(prompt_components, "MAudio")
    prompt_image = count_with(prompt_components, "MSprite")
    option_text = count_with(option_components, "MLabel")
    option_audio = count_with(option_components, "MAudio")
    option_image = count_with(option_components, "MSprite")
    prompt_text_values = count_values(prompt_components, "MLabel")
    prompt_audio_values = count_values(prompt_components, "MAudio")
    prompt_image_values = count_values(prompt_components, "MSprite")
    option_text_values = count_values(option_components, "MLabel")
    option_audio_values = count_values(option_components, "MAudio")
    option_image_values = count_values(option_components, "MSprite")

    tags = []
    if prompt_text:
        tags.append("prompt_text")
    if prompt_audio:
        tags.append("prompt_audio")
    if prompt_image:
        tags.append("prompt_image")
    if option_text:
        tags.append("option_text")
    if option_audio:
        tags.append("option_audio")
    if option_image:
        tags.append("option_image")
    if not tags:
        tags.append("structure_only")
    content_tags = []
    if prompt_text_values:
        content_tags.append("prompt_text")
    if prompt_audio_values:
        content_tags.append("prompt_audio")
    if prompt_image_values:
        content_tags.append("prompt_image")
    if option_text_values:
        content_tags.append("option_text")
    if option_audio_values:
        content_tags.append("option_audio")
    if option_image_values:
        content_tags.append("option_image")
    if not content_tags:
        content_tags.append("structure_only")

    return {
        "prompt_text_component_count": prompt_text,
        "prompt_audio_component_count": prompt_audio,
        "prompt_image_component_count": prompt_image,
        "option_text_component_count": option_text,
        "option_audio_component_count": option_audio,
        "option_image_component_count": option_image,
        "prompt_text_value_count": prompt_text_values,
        "prompt_audio_value_count": prompt_audio_values,
        "prompt_image_value_count": prompt_image_values,
        "option_text_value_count": option_text_values,
        "option_audio_value_count": option_audio_values,
        "option_image_value_count": option_image_values,
        "format_tags": tags,
        "format_signature": "+".join(tags),
        "content_tags": content_tags,
        "content_signature": "+".join(content_tags),
    }


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z._-]+", "_", value).strip("_")
    return cleaned or "reference"


def level_profile(level: dict[str, Any]) -> dict[str, Any]:
    components = [c for c in level.get("components", []) if isinstance(c, dict)]
    tool_names: dict[str, int] = {}
    base_names: dict[str, int] = {}
    state_sources: dict[str, int] = {}
    for comp in components:
        for tool in tools(comp):
            tool_names[tool] = tool_names.get(tool, 0) + 1
        base = component_base(comp)
        if base:
            base_names[base] = base_names.get(base, 0) + 1
        for key in state_source_keys(comp):
            state_sources[key] = state_sources.get(key, 0) + 1

    alone_choices = [c for c in components if component_outer_name(c) == "AloneClickChoice"]
    draggables = [c for c in components if "MDraggable" in tools(c)]
    drag_places = [c for c in components if "LDragPlace" in tools(c)]
    labels = [c for c in components if "MLabel" in state_source_keys(c) or component_base(c) == "MLabel"]
    audios = [c for c in components if "MAudio" in state_source_keys(c)]
    sprites = [c for c in components if "MSprite" in state_source_keys(c)]

    option_count = len(alone_choices) or len(draggables) or 0
    slot_count = len(drag_places) or 0
    profile_key_parts = [
        f"components={len(components)}",
        f"alone={len(alone_choices)}",
        f"drag={len(draggables)}",
        f"place={len(drag_places)}",
        f"label={len(labels)}",
        f"audio={len(audios)}",
        f"sprite={len(sprites)}",
    ]
    modality = modality_profile(components)
    profile_key_parts.append(f"format={modality['format_signature']}")
    profile_key_parts.append(f"content={modality['content_signature']}")
    return {
        "component_count": len(components),
        "alone_click_choice_count": len(alone_choices),
        "draggable_count": len(draggables),
        "drag_place_count": len(drag_places),
        "option_count": option_count,
        "slot_count": slot_count,
        "label_component_count": len(labels),
        "audio_component_count": len(audios),
        "sprite_component_count": len(sprites),
        "tool_counts": dict(sorted(tool_names.items())),
        "base_counts": dict(sorted(base_names.items())),
        "state_source_counts": dict(sorted(state_sources.items())),
        **modality,
        "profile_key": "|".join(profile_key_parts),
    }


def load_source_meta(path: Path) -> dict[str, Any]:
    if path.name == "index.json":
        return {}
    index_path = path.parent / "index.json"
    if not index_path.exists():
        return {}
    try:
        game_id = path.stem
        for row in load_json(index_path):
            if row.get("game_id") == game_id:
                return row
    except Exception:
        return {}
    return {}


def iter_sources() -> list[tuple[str, Path]]:
    sources: list[tuple[str, Path]] = []
    for subtype, base_dir, pattern in REFERENCE_SOURCES:
        if not base_dir.exists():
            continue
        for path in sorted(base_dir.glob(pattern)):
            if path.name == "index.json" or not path.is_file():
                continue
            sources.append((subtype, path))
    return sources


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    index: list[dict[str, Any]] = []
    for subtype, path in iter_sources():
        try:
            raw = load_json(path)
        except json.JSONDecodeError:
            continue
        config = unwrap_config(raw)
        if not config:
            continue
        meta = load_source_meta(path)
        game_id = meta.get("game_id") or path.stem
        game_name = meta.get("game_name") or path.stem
        subtype_dir = OUT_ROOT / subtype
        subtype_dir.mkdir(parents=True, exist_ok=True)
        for level_index, level in enumerate(config.get("game", []), 1):
            if not isinstance(level, dict):
                continue
            profile = level_profile(level)
            level_file = subtype_dir / f"{safe_name(game_id)}__L{level_index:02d}.json"
            level_file.write_text(json.dumps(level, ensure_ascii=False, indent=2), encoding="utf-8")
            index.append({
                "subtype": subtype,
                "source_config": str(path.relative_to(ROOT)),
                "source_game_id": game_id,
                "source_game_name": game_name,
                "source_level_index": level_index,
                "level_reference": str(level_file.relative_to(ROOT)),
                **profile,
            })

    index.sort(key=lambda row: (row["subtype"], row["source_game_name"], row["source_level_index"]))
    (OUT_ROOT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "schema": "coursewaremaker.reference_level_index.v1",
        "index": str((OUT_ROOT / "index.json").relative_to(ROOT)),
        "level_reference_count": len(index),
        "subtypes": sorted({row["subtype"] for row in index}),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
