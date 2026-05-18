#!/usr/bin/env python3
"""Rule validator for deterministic template-game configs.

The generator remains responsible for exact layout construction. This validator
checks stable, subtype-specific contracts after generation so weak models cannot
silently accept missing question data, wrong answer wiring, or empty assets.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "workflow" / "game_input_schemas.json"
DEFAULT_REFERENCE_INDEX = ROOT / "reference_configs" / "level_references" / "index.json"


class ValidationError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def unwrap_config(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict) and "result" in raw and isinstance(raw["result"], dict) and "configuration" in raw["result"]:
        cfg = raw["result"]["configuration"]
        return json.loads(cfg) if isinstance(cfg, str) else cfg
    if isinstance(raw, dict) and isinstance(raw.get("configuration"), str):
        return json.loads(raw["configuration"])
    if isinstance(raw, dict):
        return raw
    raise ValidationError("config root must be an object")


def normalize_items(payload: Any, schema: dict[str, Any]) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        raise ValidationError("input must be a JSON object or list")
    # Reading games use slots as option/placement data inside one level, not
    # as a multi-level container. Keep this check before generic container_keys.
    if payload.get("slots") or payload.get("answers"):
        return [payload]
    for key in schema.get("container_keys", []):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    raise ValidationError(f"input does not contain any supported container key: {schema.get('container_keys', [])}")


def has_any(item: dict[str, Any], groups: list[list[str]]) -> bool:
    for group in groups or []:
        if any(item.get(key) for key in group):
            return True
    return not groups


def option_is_correct(option: Any, keys: list[str]) -> bool:
    if isinstance(option, dict):
        return any(bool(option.get(key)) for key in keys)
    if isinstance(option, (list, tuple)) and len(option) > 1:
        return bool(option[1])
    return False


def component_name(comp: dict[str, Any]) -> str:
    return str(comp.get("component_data", {}).get("name") or comp.get("name") or comp.get("component_name") or "")


def flatten_components(config: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for level in config.get("game", []):
        out.extend(level.get("components", []))
    return out


def source_values(value: Any, key: str) -> list[str]:
    values: list[str] = []
    if isinstance(value, dict):
        source = value.get("source")
        if isinstance(source, dict):
            item = source.get(key)
            if isinstance(item, dict) and item.get("value"):
                values.append(str(item["value"]))
        for child in value.values():
            values.extend(source_values(child, key))
    elif isinstance(value, list):
        for child in value:
            values.extend(source_values(child, key))
    return values


def tools(comp: dict[str, Any]) -> dict[str, Any]:
    return comp.get("component_data", {}).get("components", {}).get("tools", {})


def state_source_keys(comp: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for state in comp.get("component_data", {}).get("states", []):
        source = state.get("source", {})
        if isinstance(source, dict):
            keys.update(str(key) for key in source)
    return keys


def component_source_values(comp: dict[str, Any], source_key: str) -> list[str]:
    values: list[str] = []
    for state in comp.get("component_data", {}).get("states", []):
        item = state.get("source", {}).get(source_key)
        if isinstance(item, dict) and item.get("value") not in (None, "", []):
            values.append(str(item["value"]))
    return values


def is_choice_component(comp: dict[str, Any]) -> bool:
    name = component_name(comp)
    comp_tools = tools(comp)
    return (
        comp.get("name") == "AloneClickChoice"
        or component_name(comp) == "AloneClickChoice"
        or "AloneClickChoice" in comp_tools
        or "MDraggable" in comp_tools
        or any(keyword in name for keyword in ("选项", "拖拽", "物品", "词卡"))
    )


def is_prompt_component(comp: dict[str, Any]) -> bool:
    name = component_name(comp)
    return (
        comp.get("name") in {"TitleStem", "QuestionStem"}
        or any(keyword in name for keyword in ("题干", "题目", "问题", "配图", "语音", "音频", "播放按钮"))
        or (name == "节点" and "MLabel" in state_source_keys(comp))
    )


def modality_profile(components: list[dict[str, Any]]) -> dict[str, Any]:
    prompt_components = [comp for comp in components if is_prompt_component(comp)]
    option_components = [comp for comp in components if is_choice_component(comp)]

    def count_with(comps: list[dict[str, Any]], source_key: str) -> int:
        return sum(1 for comp in comps if source_key in state_source_keys(comp))

    def count_values(comps: list[dict[str, Any]], source_key: str) -> int:
        return sum(1 for comp in comps if component_source_values(comp, source_key))

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
        "format_signature": "+".join(tags),
        "content_signature": "+".join(content_tags),
    }


def level_profile_key(level: dict[str, Any]) -> str:
    components = [c for c in level.get("components", []) if isinstance(c, dict)]
    alone_choices = [c for c in components if c.get("name") == "AloneClickChoice" or component_name(c) == "AloneClickChoice"]
    draggables = [c for c in components if "MDraggable" in tools(c)]
    drag_places = [c for c in components if "LDragPlace" in tools(c)]
    labels = [c for c in components if "MLabel" in state_source_keys(c) or c.get("component_data", {}).get("base") == "MLabel"]
    audios = [c for c in components if "MAudio" in state_source_keys(c)]
    sprites = [c for c in components if "MSprite" in state_source_keys(c)]
    modality = modality_profile(components)
    return "|".join([
        f"components={len(components)}",
        f"alone={len(alone_choices)}",
        f"drag={len(draggables)}",
        f"place={len(drag_places)}",
        f"label={len(labels)}",
        f"audio={len(audios)}",
        f"sprite={len(sprites)}",
        f"format={modality['format_signature']}",
        f"content={modality['content_signature']}",
    ])


def validate_input(subtype: str, input_path: Path | None, expected_levels: int | None) -> tuple[list[Any], list[str]]:
    warnings: list[str] = []
    if not input_path:
        return [], ["No input file supplied; skipped input contract validation"]
    schemas = load_json(SCHEMA_PATH).get("template_game", {})
    schema = schemas.get(subtype)
    if not schema:
        raise ValidationError(f"No template input schema for subtype: {subtype}")
    items = normalize_items(load_json(input_path), schema)
    if expected_levels is not None and len(items) != expected_levels:
        raise ValidationError(f"input level count {len(items)} != config game count {expected_levels}")

    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise ValidationError(f"L{index}: input item must be an object")
        for field in schema.get("required_fields", []):
            if field not in item or item.get(field) in (None, "", []):
                raise ValidationError(f"L{index}: missing required field: {field}")
        if not has_any(item, schema.get("required_any", [])):
            raise ValidationError(f"L{index}: missing required-any field group: {schema.get('required_any')}")
        options_field = schema.get("options_field")
        if options_field:
            options = item.get(options_field)
            if not isinstance(options, list):
                raise ValidationError(f"L{index}: {options_field} must be a list")
            if schema.get("option_count") and len(options) != schema["option_count"]:
                raise ValidationError(f"L{index}: {options_field} count must be {schema['option_count']}, got {len(options)}")
            if schema.get("option_correct_keys"):
                correct_count = sum(1 for option in options if option_is_correct(option, schema["option_correct_keys"]))
                if correct_count != 1:
                    raise ValidationError(f"L{index}: exactly one option must be correct, got {correct_count}")
            correct_field = schema.get("correct_field")
            if correct_field and item.get(correct_field) not in options:
                raise ValidationError(f"L{index}: {correct_field} must be one of {options_field}")
    return items, warnings


def validate_config_shape(config: dict[str, Any]) -> list[dict[str, Any]]:
    levels = config.get("game")
    if not isinstance(levels, list) or not levels:
        raise ValidationError("template game config must contain a non-empty game[]")
    for index, level in enumerate(levels, 1):
        if not isinstance(level.get("components"), list) or not level["components"]:
            raise ValidationError(f"L{index}: missing non-empty components[]")
    return levels


def validate_road(config: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for index, level in enumerate(config["game"], 1):
        choices = [c for c in level.get("components", []) if c.get("name") == "AloneClickChoice" or component_name(c) == "AloneClickChoice"]
        if len(choices) != 3:
            raise ValidationError(f"L{index}: road_adventure must have 3 AloneClickChoice components, got {len(choices)}")
        radios = []
        for choice in choices:
            cfg = tools(choice).get("AloneClickChoice", {}).get("anwserConfig", {})
            radios.append(cfg.get("anwserRadio"))
        if radios.count(1) != 1:
            raise ValidationError(f"L{index}: road_adventure must have exactly one anwserRadio=1, got {radios}")
    return warnings


def validate_drag_game(config: dict[str, Any], subtype: str) -> list[str]:
    for index, level in enumerate(config["game"], 1):
        components = level.get("components", [])
        places = [c for c in components if "LDragPlace" in tools(c)]
        draggables = [c for c in components if "MDraggable" in tools(c)]
        if not places:
            raise ValidationError(f"L{index}: {subtype} must contain drag places")
        if not draggables:
            raise ValidationError(f"L{index}: {subtype} must contain draggable items")
        empty_places = [component_name(c) for c in places if not tools(c).get("LDragPlace", {}).get("itemList")]
        if empty_places:
            raise ValidationError(f"L{index}: drag places missing itemList: {empty_places}")
    return []


def validate_audio_image_presence(config: dict[str, Any], subtype: str) -> list[str]:
    components = flatten_components(config)
    audios = [v for comp in components for v in source_values(comp, "MAudio") if v]
    sprites = [v for comp in components for v in source_values(comp, "MSprite") if v]
    warnings: list[str] = []
    if subtype in {"spelling", "magic_spelling", "amusement_park", "bridge"} and not audios:
        raise ValidationError(f"{subtype} generated config has no audio URL in component states")
    if subtype in {"spelling", "bridge"} and not sprites:
        raise ValidationError(f"{subtype} generated config has no image URL in component states")
    if subtype == "amusement_park" and not sprites:
        warnings.append("amusement_park config has no sprite URL detected; verify the template keeps scene resources elsewhere")
    return warnings


def validate_reading(config: dict[str, Any], subtype: str) -> list[str]:
    validate_drag_game(config, subtype)
    for index, level in enumerate(config["game"], 1):
        topic_audio = False
        for comp in level.get("components", []):
            name = component_name(comp)
            if ("题干" in name or "语音" in name or "音频" in name) and source_values(comp, "MAudio"):
                topic_audio = True
        if not topic_audio:
            raise ValidationError(f"L{index}: {subtype} topic audio not found")
    return []


def validate_reference_profiles(
    config: dict[str, Any],
    subtype: str,
    reference_index: Path | None,
    policy: str,
) -> list[str]:
    warnings: list[str] = []
    if not reference_index:
        return warnings
    if not reference_index.exists():
        message = f"reference level index not found: {reference_index}"
        if policy == "require":
            raise ValidationError(message)
        return [message]

    rows = [row for row in load_json(reference_index) if row.get("subtype") == subtype]
    if not rows:
        message = f"no level references for subtype={subtype}"
        if policy == "require":
            raise ValidationError(message)
        return [message]

    by_profile = {}
    for row in rows:
        by_profile.setdefault(row.get("profile_key"), []).append(row)

    for index, level in enumerate(config["game"], 1):
        profile = level_profile_key(level)
        if profile not in by_profile:
            message = f"L{index}: no matching per-level reference profile for {subtype}: {profile}"
            if policy == "require":
                raise ValidationError(message)
            warnings.append(message)
    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--subtype", required=True)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--meta", type=Path)
    parser.add_argument("--reference-index", type=Path)
    parser.add_argument("--reference-policy", choices=["warn", "require"], default="warn")
    args = parser.parse_args()

    config = unwrap_config(load_json(args.config))
    levels = validate_config_shape(config)
    warnings: list[str] = []
    _, input_warnings = validate_input(args.subtype, args.input, len(levels) if args.input else None)
    warnings.extend(input_warnings)

    if args.subtype == "road_adventure":
        warnings.extend(validate_road(config))
    elif args.subtype in {"bridge"}:
        warnings.extend(validate_drag_game(config, args.subtype))
    elif args.subtype in {"fanboat", "train"}:
        warnings.extend(validate_reading(config, args.subtype))

    reference_index = args.reference_index
    if reference_index and not reference_index.is_absolute():
        reference_index = ROOT / reference_index
    warnings.extend(validate_reference_profiles(config, args.subtype, reference_index, args.reference_policy))
    warnings.extend(validate_audio_image_presence(config, args.subtype))

    report = {
        "schema": "coursewaremaker.template_game_validation.v1",
        "config": str(args.config),
        "subtype": args.subtype,
        "level_count": len(levels),
        "warning_count": len(warnings),
        "warnings": warnings,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(2)
