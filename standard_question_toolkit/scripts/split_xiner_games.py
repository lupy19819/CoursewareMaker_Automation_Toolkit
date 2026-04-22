import ast
import copy
import json
from pathlib import Path

INPUT = Path("D:/迅雷下载/新二.txt")
OUT_DIR = Path("D:/codexProject/generated_configs/xiner_split_12_games")

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
    global_config = data.setdefault("common", {}).setdefault("global_config", {})
    countdown = global_config.setdefault("time_countdown", {})
    countdown["switch_countdown"] = True
    countdown["countdown_time"] = 120


def normalize_score(data):
    global_config = data.setdefault("common", {}).setdefault("global_config", {})
    global_config["score_config"] = {
        "type": "average",
        "score": [100],
        "additional_score": [],
    }


def apply_first_level_draft(level, first_level):
    level_data = level.setdefault("levelData", {})
    first_level_data = first_level.get("levelData", {})

    ui_config = level_data.setdefault("uiConfig", {})
    first_ui_config = first_level_data.get("uiConfig", {})
    for key in DRAFT_UI_KEYS:
        if key in first_ui_config:
            ui_config[key] = copy.deepcopy(first_ui_config[key])

    for key in DRAFT_LEVEL_KEYS:
        if key in first_level_data:
            level_data[key] = copy.deepcopy(first_level_data[key])


def main():
    data = read_wrapped_json(INPUT)
    levels = data.get("game", [])
    if len(levels) != 12:
        raise ValueError(f"Expected 12 levels, got {len(levels)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    first_level = levels[0]
    manifest = []

    for index, level in enumerate(levels, start=1):
        game_data = copy.deepcopy(data)
        single_level = copy.deepcopy(level)
        apply_first_level_draft(single_level, first_level)
        game_data["game"] = [single_level]
        normalize_countdown(game_data)
        normalize_score(game_data)

        out_path = OUT_DIR / f"新二_第{index:02d}关_单关游戏.json"
        write_json(out_path, game_data)
        manifest.append(
            {
                "source_level": index,
                "file": str(out_path),
                "level_count": 1,
                "countdown_time": 120,
                "draft_copied_from": "原游戏第一关",
            }
        )

    write_json(OUT_DIR / "拆分清单.json", {"source": str(INPUT), "games": manifest})
    print(f"generated {len(manifest)} games")
    print(OUT_DIR)


if __name__ == "__main__":
    main()
