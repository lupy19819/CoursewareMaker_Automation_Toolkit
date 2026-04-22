import json
from copy import deepcopy
from pathlib import Path

import openpyxl


ROOT = Path(r"D:\codexProject")
RESOURCE_JSON = ROOT / "latest_resources.json"
QUESTION_XLSX = ROOT / "zhiyinlou_monster_test.xlsx"
TEMPLATE_JSON = ROOT / "monster_template_from_localstorage.json"
OUTPUT_JSON = ROOT / "Sj6贪吃小怪兽.config.json"
OUTPUT_META = ROOT / "Sj6贪吃小怪兽.build-meta.json"

SHEET_NAME = "Sj6贪吃小怪兽"
NODE_NAME_BY_OPTION = {1: "节点", 2: "节点_104", 3: "节点_103"}
RIGHT_ANIMATION_BY_OPTION = {1: "right_1_2", 2: "right_2_2", 3: "right_3_2"}


def load_questions() -> list[dict]:
    wb = openpyxl.load_workbook(QUESTION_XLSX, data_only=True)
    ws = wb[SHEET_NAME]

    questions = []
    current = None
    for row in ws.iter_rows(min_row=2, values_only=True):
        qno, audio, stem_img, stem_text, opt_no, opt_img, opt_text, is_correct, *_ = row
        if qno is None and opt_no is None:
            continue

        if qno is not None:
            current = {
                "question_no": int(qno),
                "audio_name": audio,
                "stem_img_name": stem_img,
                "stem_text": stem_text,
                "options": [],
            }
            questions.append(current)

        current["options"].append(
            {
                "option_no": int(opt_no),
                "option_img_name": opt_img,
                "option_text": opt_text,
                "is_correct": is_correct is not None,
            }
        )

    return questions


def load_resource_lookup() -> dict[str, dict]:
    rows = json.loads(RESOURCE_JSON.read_text(encoding="utf-8"))["rows"]
    return {row["name"]: row for row in rows if row.get("name")}


def get_state(component: dict, state_name: str) -> dict | None:
    for state in component["component_data"].get("states", []):
        if state.get("state") == state_name:
            return state
    return None


def ensure_state(component: dict, state_name: str, fallback_state_name: str = "default") -> dict:
    state = get_state(component, state_name)
    if state:
        return state

    fallback = deepcopy(get_state(component, fallback_state_name) or component["component_data"]["states"][0])
    fallback["state"] = state_name
    labels = {
        "default": "默认",
        "clickStart": "按下",
        "clickEnd": "抬起",
        "compLoadFinish": "组件加载完成",
        "level_correct": "全局正确",
        "level_wrong": "全局错误",
    }
    fallback["label"] = labels.get(state_name, state_name)
    component["component_data"]["states"].append(fallback)
    return fallback


def set_active_hide(state: dict) -> None:
    state.setdefault("active", {})
    state["active"]["canEdit"] = True
    state["active"]["switch"] = True
    state["active"]["value"] = "hide"


def set_node_content(component: dict, *, sprite_url: str | None, text_value: str | None) -> None:
    for state_name in ["default", "compLoadFinish", "level_correct"]:
        state = get_state(component, state_name)
        if not state:
            continue
        source = state.setdefault("source", {})
        if "MSprite" in source and sprite_url is not None:
            source["MSprite"]["value"] = sprite_url
        if "MLabel" in source:
            source["MLabel"]["value"] = text_value or ""


def remove_level_correct_state(component: dict) -> None:
    states = component["component_data"].get("states", [])
    component["component_data"]["states"] = [s for s in states if s.get("state") != "level_correct"]


def update_level(level: dict, question: dict, resource_lookup: dict[str, dict], total_levels: int) -> dict:
    components = level["components"]
    comp_by_node_name = {}
    click_by_position = {}
    title_stem = None
    effect_monster = None
    level_number = None

    for comp in components:
        comp_name = comp.get("name")
        cd = comp.get("component_data", {})
        cd_name = cd.get("name", "")

        if comp_name == "TitleStem":
            title_stem = comp
        elif comp_name == "LevelNumber":
            level_number = comp
        elif comp_name == "AloneClickChoice":
            x = cd["states"][0]["transform"]["x"]
            if x < -200:
                click_by_position[1] = comp
            elif x < 200:
                click_by_position[2] = comp
            else:
                click_by_position[3] = comp
        elif cd_name in {"节点", "节点_103", "节点_104"}:
            # Fixed binding: left=节点, center=节点_104, right=节点_103
            comp_by_node_name[cd_name] = comp
        elif cd_name == "节点_102":
            effect_monster = comp

    audio_res = resource_lookup.get(question["audio_name"])
    if not audio_res:
        raise KeyError(f"Missing audio resource: {question['audio_name']}")

    correct_option = next(opt["option_no"] for opt in question["options"] if opt["is_correct"])

    # TitleStem
    click_end = ensure_state(title_stem, "clickEnd")
    click_end.setdefault("source", {}).setdefault("MAudio", {})
    click_end["source"]["MAudio"]["value"] = audio_res["url"]
    click_end["source"]["MAudio"]["audioType"] = "play_audio"

    comp_load_finish = ensure_state(title_stem, "compLoadFinish")
    comp_load_finish.setdefault("source", {}).setdefault("MAudio", {})
    comp_load_finish["source"]["MAudio"]["value"] = ""
    comp_load_finish["jump"] = {
        "canEdit": True,
        "opened": 1,
        "type": "countdown",
        "to": "clickEnd",
        "duration": 0.5,
    }

    title_correct = ensure_state(title_stem, "level_correct", "default")
    set_active_hide(title_correct)

    # LevelNumber display
    if level_number:
        default_state = get_state(level_number, "default")
        if default_state and "MRichText" in default_state.get("source", {}):
            default_state["source"]["MRichText"]["value"] = f"{question['question_no']}/{total_levels}"

    # Choices and nodes
    for opt in question["options"]:
        option_no = opt["option_no"]
        node_name = NODE_NAME_BY_OPTION[option_no]
        node_comp = comp_by_node_name[node_name]
        click_comp = click_by_position[option_no]
        is_image_option = bool(opt["option_img_name"])

        sprite_url = None
        text_value = ""
        if is_image_option:
            img_res = resource_lookup.get(opt["option_img_name"])
            if not img_res:
                raise KeyError(f"Missing image resource: {opt['option_img_name']}")
            sprite_url = img_res["url"]
        else:
            text_value = opt["option_text"] or ""

        set_node_content(node_comp, sprite_url=sprite_url, text_value=text_value)

        click_comp["component_data"]["components"]["tools"]["AloneClickChoice"]["anwserConfig"]["anwserRadio"] = (
            1 if opt["is_correct"] else 2
        )

        if opt["is_correct"]:
            correct_state = ensure_state(node_comp, "level_correct", "default")
            set_node_content(node_comp, sprite_url=sprite_url, text_value=text_value)
            set_active_hide(correct_state)
        else:
            remove_level_correct_state(node_comp)

    # Monster feedback animation
    if effect_monster:
        effect_correct = ensure_state(effect_monster, "level_correct", "default")
        effect_correct.setdefault("source", {}).setdefault("MSpine", {})
        effect_correct["source"]["MSpine"]["animation"] = RIGHT_ANIMATION_BY_OPTION[correct_option]

    return {
        "question_no": question["question_no"],
        "audio_name": question["audio_name"],
        "audio_url": audio_res["url"],
        "correct_option": correct_option,
        "option_type": "image" if question["options"][0]["option_img_name"] else "text",
    }


def main() -> None:
    questions = load_questions()
    resource_lookup = load_resource_lookup()
    config = json.loads(TEMPLATE_JSON.read_text(encoding="utf-8"))

    total_levels = len(questions)
    config["game"] = deepcopy(config["game"][:total_levels])

    build_meta = {"sheet_name": SHEET_NAME, "question_count": total_levels, "levels": []}
    for level, question in zip(config["game"], questions, strict=True):
        build_meta["levels"].append(update_level(level, question, resource_lookup, total_levels))

    OUTPUT_JSON.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTPUT_META.write_text(json.dumps(build_meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(build_meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
