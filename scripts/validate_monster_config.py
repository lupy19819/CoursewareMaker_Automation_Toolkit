#!/usr/bin/env python3
"""Validate a CoursewareMaker 贪吃小怪兽 config.

Checks:
- root shape and level count;
- component order against a reference template when provided;
- TitleStem clickEnd/compLoadFinish audio rules;
- option node and click-component mapping;
- exactly one correct option;
- correct option level_correct hidden state;
- wrong options do not retain level_correct;
- feedback monster animation matches the correct option;
- prompt image/text and option image/text content according to build meta when provided.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


NODE_NAME_BY_OPTION = {1: "节点", 2: "节点_104", 3: "节点_103"}
RIGHT_ANIMATION_BY_OPTION = {1: "right_1_2", 2: "right_2_2", 3: "right_3_2"}
NO_AUDIO_PROMPT_TYPES = {"no_audio_image", "no_audio_text"}
PROMPT_TEXT_STYLE = {
    "x": 0,
    "y": 250,
    "w": 980,
    "h": 180,
    "fontSize": 72,
    "color": "#000000",
    "fontFamily": "FZCuYuan-M03S",
}


def load_config(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if "result" in raw and "configuration" in raw.get("result", {}):
        cfg = raw["result"]["configuration"]
        return json.loads(cfg) if isinstance(cfg, str) else cfg
    if "configuration" in raw and isinstance(raw["configuration"], str):
        return json.loads(raw["configuration"])
    if "game" in raw:
        return raw
    raise ValueError(f"无法识别文件结构，顶层 keys: {list(raw.keys())}")


def load_meta(path: Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def get_state(component: dict[str, Any], state_name: str) -> dict[str, Any] | None:
    for state in component.get("component_data", {}).get("states", []):
        if state.get("state") == state_name:
            return state
    return None


def active_is_hidden(state: dict[str, Any] | None) -> bool:
    active = (state or {}).get("active", {})
    return active.get("canEdit") is True and active.get("switch") is True and active.get("value") == "hide"


def state_transform(component: dict[str, Any] | None, state_name: str = "default") -> dict[str, Any]:
    if not component:
        return {}
    state = get_state(component, state_name) or {}
    return state.get("transform", {})


def source_value(component: dict[str, Any] | None, source_name: str, state_name: str = "default") -> str:
    if not component:
        return ""
    state = get_state(component, state_name) or {}
    return state.get("source", {}).get(source_name, {}).get("value", "") or ""


def label_source(component: dict[str, Any] | None, state_name: str = "default") -> dict[str, Any]:
    if not component:
        return {}
    state = get_state(component, state_name) or {}
    return state.get("source", {}).get("MLabel", {})


def has_source(component: dict[str, Any], source_name: str) -> bool:
    for state in component.get("component_data", {}).get("states", []):
        if source_name in state.get("source", {}):
            return True
    return False


def is_system_or_choice_component(comp: dict[str, Any]) -> bool:
    cd_name = comp.get("component_data", {}).get("name", "")
    comp_name = comp.get("name")
    return (
        comp_name in {"TitleStem", "LevelNumber", "AloneClickChoice"}
        or cd_name in set(NODE_NAME_BY_OPTION.values())
        or cd_name in {"背景", "节点_102", "节点_106", "节点_107"}
    )


def option_text_nodes(level: dict[str, Any]) -> dict[int, dict[str, Any]]:
    candidates = []
    for comp in level.get("components", []):
        cd = comp.get("component_data", {})
        if is_system_or_choice_component(comp) or cd.get("base") != "MLabel" or not has_source(comp, "MLabel"):
            continue
        tr = state_transform(comp)
        x = tr.get("x")
        y = tr.get("y", 0)
        if x is not None and y < 150:
            candidates.append((x, comp))
    if len(candidates) < 3:
        return {}
    return {idx: comp for idx, (_, comp) in enumerate(sorted(candidates, key=lambda item: item[0])[:3], start=1)}


def tool_radio(component: dict[str, Any]) -> Any:
    return (
        component.get("component_data", {})
        .get("components", {})
        .get("tools", {})
        .get("AloneClickChoice", {})
        .get("anwserConfig", {})
        .get("anwserRadio")
    )


def index_components(level: dict[str, Any]) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    clicks: dict[int, dict[str, Any]] = {}
    title = None
    level_number = None
    effect = None
    for comp in level.get("components", []):
        cd = comp.get("component_data", {})
        cd_name = cd.get("name", "")
        comp_name = comp.get("name")
        if comp_name == "TitleStem" or comp.get("component_name") == "音频播放按钮":
            title = comp
        elif comp_name == "LevelNumber" or comp.get("component_name") == "关卡数组件":
            level_number = comp
        elif comp_name == "AloneClickChoice" or comp.get("component_name") == "点击选择":
            states = cd.get("states", [])
            x = states[0].get("transform", {}).get("x", 0) if states else 0
            if x < -200:
                clicks[1] = comp
            elif x < 200:
                clicks[2] = comp
            else:
                clicks[3] = comp
        elif cd_name in set(NODE_NAME_BY_OPTION.values()):
            nodes[cd_name] = comp
        elif cd_name == "节点_102":
            effect = comp
    return {
        "nodes": nodes,
        "clicks": clicks,
        "title": title,
        "level_number": level_number,
        "effect": effect,
        "option_text_nodes": option_text_nodes(level),
    }


def component_signature(level: dict[str, Any]) -> list[tuple[str, str, str]]:
    sig = []
    for comp in level.get("components", []):
        cd = comp.get("component_data", {})
        if cd.get("name") == "题干文本" and cd.get("base") == "MLabel":
            continue
        sig.append((comp.get("component_name", ""), comp.get("name", ""), cd.get("name", "")))
    return sig


def validate(path: Path, *, expected_levels: int | None, meta_path: Path | None, reference_path: Path | None) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    cfg = load_config(path)
    meta = load_meta(meta_path)
    game = cfg.get("game", [])

    if expected_levels is None and meta:
        expected_levels = meta.get("question_count")
    if expected_levels is not None and len(game) != expected_levels:
        errors.append(f"关卡数应为 {expected_levels}，实际 {len(game)}")

    ref_sig = None
    if reference_path:
        ref = load_config(reference_path)
        ref_sig = component_signature(ref["game"][0])

    meta_levels = meta.get("levels", []) if meta else []
    if meta and len(meta_levels) != len(game):
        errors.append(f"meta 关卡数应为 {len(game)}，实际 {len(meta_levels)}")

    for gi, level_data in enumerate(game):
        level = gi + 1
        indexed = index_components(level_data)
        nodes = indexed["nodes"]
        clicks = indexed["clicks"]
        title = indexed["title"]
        effect = indexed["effect"]
        text_nodes = indexed["option_text_nodes"]
        meta_level = meta_levels[gi] if gi < len(meta_levels) else None
        question_type = (meta_level or {}).get("question_type")

        if ref_sig and component_signature(level_data) != ref_sig:
            errors.append(f"关{level}: components[] 顺序或组件签名与参考模板不一致")

        if question_type not in NO_AUDIO_PROMPT_TYPES and not title:
            errors.append(f"关{level}: 缺少 TitleStem/音频播放按钮")
        elif title:
            click_end = get_state(title, "clickEnd")
            click_audio = (click_end or {}).get("source", {}).get("MAudio", {}).get("value", "")
            comp_load = get_state(title, "compLoadFinish")
            load_audio = (comp_load or {}).get("source", {}).get("MAudio", {}).get("value", "")
            jump = (comp_load or {}).get("jump", {})
            if question_type not in NO_AUDIO_PROMPT_TYPES and not click_audio:
                errors.append(f"关{level}: TitleStem.clickEnd 音频 URL 为空")
            if question_type in NO_AUDIO_PROMPT_TYPES and click_audio:
                errors.append(f"关{level}: 无音频题 TitleStem.clickEnd 音频应为空")
            if load_audio:
                errors.append(f"关{level}: TitleStem.compLoadFinish 音频应为空，实际非空")
            if jump.get("type") != "countdown" or jump.get("to") != "clickEnd":
                errors.append(f"关{level}: TitleStem.compLoadFinish.jump 应为 countdown -> clickEnd")
            if not active_is_hidden(get_state(title, "level_correct")):
                errors.append(f"关{level}: TitleStem.level_correct.active 应为 hide")

        for option_no, node_name in NODE_NAME_BY_OPTION.items():
            if node_name not in nodes:
                errors.append(f"关{level}: 缺少选项视觉节点 {node_name}")
            if option_no not in clicks:
                errors.append(f"关{level}: 缺少位置 {option_no} 的 AloneClickChoice")

        radios = {option_no: tool_radio(clicks[option_no]) for option_no in clicks if option_no in [1, 2, 3]}
        correct_options = [option_no for option_no, radio in radios.items() if radio == 1]
        invalid_radios = {option_no: radio for option_no, radio in radios.items() if radio not in (1, 2)}
        if invalid_radios:
            errors.append(f"关{level}: anwserRadio 非法: {invalid_radios}")
        if len(correct_options) != 1:
            errors.append(f"关{level}: 正确选项数量应为 1，实际 {len(correct_options)} (radios={radios})")
            correct_option = None
        else:
            correct_option = correct_options[0]

        for option_no, node_name in NODE_NAME_BY_OPTION.items():
            node = nodes.get(node_name)
            if not node:
                continue
            correct_state = get_state(node, "level_correct")
            if option_no == correct_option:
                if not correct_state:
                    errors.append(f"关{level}: 正确节点 {node_name} 缺少 level_correct")
                elif not active_is_hidden(correct_state):
                    errors.append(f"关{level}: 正确节点 {node_name}.level_correct.active 应为 hide")
            elif correct_state:
                errors.append(f"关{level}: 错误节点 {node_name} 不应保留 level_correct")

        if effect and correct_option:
            effect_correct = get_state(effect, "level_correct")
            animation = (effect_correct or {}).get("source", {}).get("MSpine", {}).get("animation", "")
            expected_animation = RIGHT_ANIMATION_BY_OPTION[correct_option]
            if animation != expected_animation:
                errors.append(f"关{level}: 节点_102 正确反馈动效应为 {expected_animation}，实际 {animation}")
        elif not effect:
            errors.append(f"关{level}: 缺少节点_102 小怪兽反馈组件")

        if meta_level:
            if meta_level.get("correct_option") and correct_option and meta_level["correct_option"] != correct_option:
                errors.append(f"关{level}: meta correct_option={meta_level['correct_option']} 但配置为 {correct_option}")
            prompt = meta_level.get("prompt", {})
            prompt_node_name = prompt.get("prompt_node_name")
            prompt_node = next(
                (comp for comp in level_data.get("components", []) if comp.get("component_data", {}).get("name") == prompt_node_name),
                None,
            )
            if prompt.get("prompt_text") and (not prompt_node or source_value(prompt_node, "MLabel") != prompt["prompt_text"]):
                errors.append(f"关{level}: 题干文字与 meta 不一致")
            if prompt.get("prompt_image_url") and (not prompt_node or source_value(prompt_node, "MSprite") != prompt["prompt_image_url"]):
                errors.append(f"关{level}: 题干图片与 meta 不一致")
            for opt in meta_level.get("options", []):
                node = nodes.get(opt["node_name"])
                if not node:
                    continue
                sprites = {
                    state_name: source_value(node, "MSprite", state_name)
                    for state_name in ["default", "compLoadFinish", "level_correct"]
                    if get_state(node, state_name)
                }
                label = source_value(node, "MLabel")
                if opt.get("image_url"):
                    if sprites.get("default") != opt["image_url"]:
                        errors.append(f"关{level}: 选项{opt['option_no']} 默认状态图片 URL 与 meta 不一致")
                    if sprites.get("compLoadFinish") != opt["image_url"]:
                        errors.append(f"关{level}: 选项{opt['option_no']} 组件加载完成状态图片 URL 与 meta 不一致")
                    if opt.get("is_correct") and sprites.get("level_correct") != opt["image_url"]:
                        errors.append(f"关{level}: 正确选项{opt['option_no']} 全局正确状态图片 URL 与 meta 不一致")
                if opt.get("text") and label != opt["text"]:
                    text_node = text_nodes.get(opt["option_no"])
                    text_node_label = source_value(text_node, "MLabel") if text_node else ""
                    if text_node_label != opt["text"]:
                        errors.append(f"关{level}: 选项{opt['option_no']} 文本与 meta 不一致")
                if not opt.get("image_url") and not opt.get("text"):
                    warnings.append(f"关{level}: 选项{opt['option_no']} meta 未记录图片或文本")
            if prompt.get("prompt_mode") == "text" and prompt_node:
                tr = state_transform(prompt_node)
                src = label_source(prompt_node)
                style = prompt.get("prompt_style") or PROMPT_TEXT_STYLE
                for key in ["x", "y", "w", "h"]:
                    if tr.get(key) != style.get(key):
                        errors.append(f"关{level}: 题干文字组件 transform.{key} 应为 {style.get(key)}，实际 {tr.get(key)}")
                for key in ["fontSize", "color", "fontFamily"]:
                    if src.get(key) != style.get(key):
                        errors.append(f"关{level}: 题干文字组件 MLabel.{key} 应为 {style.get(key)}，实际 {src.get(key)}")

    if errors:
        print(f"INVALID — {path}")
        for e in errors:
            print(f"  ERROR: {e}")
        for w in warnings:
            print(f"  WARN:  {w}")
        return 1
    print(f"VALID — {path}")
    for w in warnings:
        print(f"  WARN: {w}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="Generated config JSON or API detail JSON")
    parser.add_argument("expected_levels", nargs="?", type=int, help="Expected level count (legacy positional)")
    parser.add_argument("--meta", type=Path, help="Build meta emitted by build_sj6_monster_config.py")
    parser.add_argument("--reference", type=Path, help="Optional reference template for component signature comparison")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        return validate(args.config, expected_levels=args.expected_levels, meta_path=args.meta, reference_path=args.reference)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
