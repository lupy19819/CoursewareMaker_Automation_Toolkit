import ast
import copy
import json
from pathlib import Path

SOURCE = Path("D:/迅雷下载/新一.txt")
DRAFT_SOURCE = Path("D:/迅雷下载/新二.txt")
OUT_DIR = Path("D:/codexProject/generated_configs/xinyi_split_12_games")

DRAFT_UI_KEYS = ("BtnEraserLevel", "BtnPenLevel", "BtnResetLevel")
DRAFT_LEVEL_KEYS = ("drawComLevel", "eraserLevelBtn", "penLevelBtn", "resetLevelBtn")


def read_wrapped_json(path: Path):
    text = path.read_text(encoding="utf-8-sig").strip()
    if len(text) >= 2 and text[0] == "'" and text[-1] == "'":
        text = ast.literal_eval(text)
    return json.loads(text)


def write_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_countdown(data):
    countdown = data.setdefault("common", {}).setdefault("global_config", {}).setdefault("time_countdown", {})
    countdown["switch_countdown"] = True
    countdown["countdown_time"] = 120


def normalize_score(data):
    data.setdefault("common", {}).setdefault("global_config", {})["score_config"] = {
        "type": "average",
        "score": [100],
        "additional_score": [],
    }


def apply_draft_from_template(level, draft_level):
    level_data = level.setdefault("levelData", {})
    draft_level_data = draft_level.get("levelData", {})

    ui_config = level_data.setdefault("uiConfig", {})
    draft_ui_config = draft_level_data.get("uiConfig", {})
    for key in DRAFT_UI_KEYS:
        if key in draft_ui_config:
            ui_config[key] = copy.deepcopy(draft_ui_config[key])

    for key in DRAFT_LEVEL_KEYS:
        if key in draft_level_data:
            level_data[key] = copy.deepcopy(draft_level_data[key])


def main():
    source_data = read_wrapped_json(SOURCE)
    draft_data = read_wrapped_json(DRAFT_SOURCE)

    source_levels = source_data.get("game", [])
    draft_levels = draft_data.get("game", [])
    if len(source_levels) != 12:
        raise ValueError(f"Expected 12 source levels, got {len(source_levels)}")
    if not draft_levels:
        raise ValueError("Draft source has no levels")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    draft_level = draft_levels[0]
    manifest = []

    for index, level in enumerate(source_levels, start=1):
        single_game = copy.deepcopy(source_data)
        single_level = copy.deepcopy(level)
        apply_draft_from_template(single_level, draft_level)
        single_game["game"] = [single_level]
        normalize_countdown(single_game)
        normalize_score(single_game)

        out_path = OUT_DIR / f"新一_第{index:02d}关_单关游戏.json"
        write_json(out_path, single_game)
        manifest.append(
            {
                "source_level": index,
                "file": str(out_path),
                "level_count": 1,
                "countdown_time": 120,
                "draft_copied_from": "新二第一关",
            }
        )

    write_json(OUT_DIR / "拆分清单.json", {"source": str(SOURCE), "draft_source": str(DRAFT_SOURCE), "games": manifest})
    print(f"generated {len(manifest)} games")
    print(OUT_DIR)


if __name__ == "__main__":
    main()
