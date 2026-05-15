#!/usr/bin/env python3
"""Deterministic router for CoursewareMaker workflow requests.

This script intentionally avoids model judgment. It maps a user message plus
optional explicit CLI fields into a structured routing result using JSON rules.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = Path(__file__).resolve().parent
UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
CONFIG_PATH_RE = re.compile(r"(?P<path>[^\s，。；;]+(?:\.config)?\.(?:json|rtf|xlsx|csv))")
URL_RE = re.compile(r"https?://[^\s，。；;]+")
YACH_DOC_ID_RE = re.compile(r"/sheets/(?P<doc_id>[^/?#]+)")
QUOTED_NAME_RE = re.compile(r"[\"'“”‘’《](?P<name>[^\"'“”‘’》]{2,80})[\"'“”‘’》]")
NAME_MARKER_RE = re.compile(r"(?:游戏名|名字叫做|名字叫|名称为|叫做|叫)\s*[:：]?\s*[\"'“”‘’《]?(?P<name>[^\"'“”‘’》，。；;\n]{2,80})")
SHEET_MARKER_RE = re.compile(r"(?:sheet(?:中|名|为|是)?|工作表(?:中|名|为|是)?)\s*[:：]?\s*[\"'“”‘’《]?(?P<plain>[^\"'“”‘’》，。；;\n]{1,120})", re.IGNORECASE)


def load_json(name: str) -> Any:
    with (WORKFLOW_DIR / name).open(encoding="utf-8") as f:
        return json.load(f)


def contains_any(text: str, signals: list[str]) -> list[str]:
    return [signal for signal in signals if signal and signal.lower() in text.lower()]


def extract_game_id(text: str) -> str | None:
    match = UUID_RE.search(text)
    return match.group(0) if match else None


def extract_config_path(text: str) -> str | None:
    match = CONFIG_PATH_RE.search(text)
    return match.group("path") if match else None


def extract_source_url(text: str) -> str | None:
    match = URL_RE.search(text)
    return match.group(0) if match else None


def extract_yach_doc_id(text: str) -> str | None:
    url = extract_source_url(text) or text
    match = YACH_DOC_ID_RE.search(url)
    if match:
        return match.group("doc_id")
    return None


def extract_sheet_name(text: str) -> str | None:
    bracket_matches = re.findall(r"【([^】]{1,120})】", text)
    if bracket_matches:
        return bracket_matches[-1].strip() or None
    match = SHEET_MARKER_RE.search(text)
    if not match:
        return None
    return (match.group("plain") or "").strip() or None


def extract_game_name(text: str, selected_intent: str | None) -> str | None:
    marker = NAME_MARKER_RE.search(text)
    if marker:
        name = marker.group("name").strip()
        if name and not UUID_RE.search(name):
            return name

    quoted = QUOTED_NAME_RE.search(text)
    if quoted:
        name = quoted.group("name").strip()
        if name and not UUID_RE.search(name):
            return name

    # Avoid hallucinating a name from arbitrary prose. Existing-game names are
    # accepted only when the user marks them or quotes them.
    return None


def route_intent(text: str, rules: dict[str, Any]) -> dict[str, Any]:
    matches = []
    has_game_id = extract_game_id(text) is not None
    upload_signal = bool(contains_any(text, ["上传", "导入", "保存", "试一下", "写入"]))
    create_signal = bool(contains_any(text, ["新建", "创建一个新的", "生成一个新的游戏", "创建新的", "名字叫", "名字叫做"]))

    for rule in sorted(rules["rules"], key=lambda r: r["priority"]):
        signals = rule.get("signals", [])
        matched = contains_any(text, signals)
        if rule["intent"] == "import_to_existing_game" and has_game_id and upload_signal:
            matched = sorted(set(matched + ["game_id"]))
        if matched:
            matches.append({"intent": rule["intent"], "priority": rule["priority"], "signals": matched, "stage": rule["stage"]})

    if not matches:
        fallback = next(rule for rule in rules["rules"] if rule["intent"] == "new_production_task")
        matches.append({"intent": fallback["intent"], "priority": fallback["priority"], "signals": [], "stage": fallback["stage"]})

    selected = matches[0]
    intents = {m["intent"] for m in matches}
    # A production request often says assets "已经上传" while explicitly asking
    # to create a new game. Without a target game_id, the explicit create signal
    # must win over upload/import wording so weak models do not route to an
    # existing-game import path.
    if create_signal and not has_game_id and "create_new_game" in intents:
        selected = next(m for m in matches if m["intent"] == "create_new_game")
    conflict = None

    if "config_repair" in intents and "create_new_game" in intents and not has_game_id:
        conflict = "同时命中返修和新建信号，必须确认是修改已有游戏还是创建新游戏。"
    elif "preview_or_publish" in intents and "create_new_game" in intents:
        conflict = "同时命中发布/预览和新建信号，必须先确认目标动作。"

    return {"selected": selected, "matches": matches, "conflict": conflict}


def route_game_type(text: str, rules: dict[str, Any]) -> dict[str, Any]:
    matches = []
    for family in rules["families"]:
        for subtype in family["subtypes"]:
            matched = contains_any(text, subtype["keywords"])
            if matched:
                matches.append(
                    {
                        "game_family": family["game_family"],
                        "family_display_name": family["display_name"],
                        "game_subtype": subtype["game_subtype"],
                        "subtype_display_name": subtype["display_name"],
                        "matched_keywords": matched,
                        "data_shape": family["data_shape"],
                        "game_type": family["game_type"],
                        "editor_entry": family["editor_entry"],
                        "baseline": subtype["baseline"],
                    }
                )

    if not matches:
        return {
            "game_family": None,
            "family_display_name": None,
            "game_subtype": None,
            "subtype_display_name": None,
            "matched_keywords": [],
            "data_shape": None,
            "game_type": None,
            "editor_entry": None,
            "baseline": None,
            "ambiguous": False,
        }

    unique = {(m["game_family"], m["game_subtype"]) for m in matches}
    selected = matches[0]
    selected["ambiguous"] = len(unique) > 1
    selected["all_matches"] = matches
    return selected


def parse_feedback_scope(text: str) -> str | None:
    feedback_markers = ["资源用错", "位置不好", "放置区", "音频错", "正确项错", "错了", "不对", "调整", "改一下", "反馈"]
    for marker in feedback_markers:
        idx = text.find(marker)
        if idx >= 0:
            return text[max(0, idx - 30) : idx + 80].strip()
    return None


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    text = args.message or ""
    if args.message_file:
        text = Path(args.message_file).read_text(encoding="utf-8")

    intent_rules = load_json("intent_rules.json")
    game_rules = load_json("game_type_rules.json")
    intent = route_intent(text, intent_rules)
    game = route_game_type(text, game_rules)

    selected_intent = intent["selected"]["intent"]
    result = {
        "schema": "coursewaremaker.workflow.route.v1",
        "router_version": intent_rules["version"],
        "message": text,
        "intent": selected_intent,
        "stage": intent["selected"]["stage"],
        "intent_signals": intent["selected"]["signals"],
        "all_intent_matches": intent["matches"],
        "route_conflict": intent["conflict"],
        "game_id": args.game_id or extract_game_id(text),
        "game_name": args.game_name or extract_game_name(text, selected_intent),
        "config_path": args.config_path or extract_config_path(text),
        "source_url": extract_source_url(text),
        "yach_doc_id": extract_yach_doc_id(text),
        "sheet_name": extract_sheet_name(text),
        "feedback_scope": args.feedback_scope or parse_feedback_scope(text),
        "game_family": args.game_family or game["game_family"],
        "game_subtype": args.game_subtype or game["game_subtype"],
        "game_type": game["game_type"],
        "editor_entry": game["editor_entry"],
        "data_shape": game["data_shape"],
        "baseline": game["baseline"],
        "game_type_ambiguous": game.get("ambiguous", False),
        "game_type_matches": game.get("all_matches", []) if game.get("ambiguous") else [],
        "requires_confirmation": bool(intent["conflict"] or game.get("ambiguous")),
        "blocked_reason": intent["conflict"] or ("命中多个游戏类型，必须先确认具体类型。" if game.get("ambiguous") else None),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--message", "-m", help="User message to route")
    parser.add_argument("--message-file", help="Read user message from file")
    parser.add_argument("--game-id", help="Explicit target game_id override")
    parser.add_argument("--game-name", help="Explicit game name override")
    parser.add_argument("--config-path", help="Explicit local config path override")
    parser.add_argument("--feedback-scope", help="Explicit feedback scope override")
    parser.add_argument("--game-family", choices=["yundong_pk", "template_game", "standard_component"])
    parser.add_argument("--game-subtype", help="Explicit game subtype override")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args()

    result = build_result(args)
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
