import json
import sys
from pathlib import Path


CHOICE_ID = "3b9b8ec3-f7d3-11ee-b9ef-8e2f78cd4bcd"
BLANK_ID = "0b26ef14-f7e0-11ee-b9ef-8e2f78cd4bcd"
KEYBOARD_ID = "1b1a9c56-f8ab-11ee-b9ef-8e2f78cd4bcd"

SKIN_BY_LEVEL_INDEX = {
    range(0, 5): "紫色",
    range(5, 10): "黄色",
    range(10, 15): "蓝色",
}

TEXT_COLOR = {
    "紫色": "#EADFFF",
    "黄色": "#8C3C0B",
    "蓝色": "#9EFAFF",
}

TITLE_COLOR = {
    "紫色": "#EADFFF",
    "黄色": "#000000",
    "蓝色": "#9EFAFF",
}


def level_skin(index):
    for level_range, skin in SKIN_BY_LEVEL_INDEX.items():
        if index in level_range:
            return skin
    return "蓝色"


def sprite_url(resources, key):
    try:
        return resources[key]
    except KeyError as exc:
        raise KeyError(f"Missing uploaded skin resource: {key}") from exc


def set_sprite_value(state, url):
    sprite = state.get("source", {}).get("MSprite")
    if not isinstance(sprite, dict):
        return
    sprite["value"] = url
    if isinstance(sprite.get("nineGrid"), dict):
        sprite["nineGrid"]["enable"] = False


def set_label_color(component, color):
    for state in component.get("component_data", {}).get("states", []):
        label = state.get("source", {}).get("MLabel")
        if isinstance(label, dict):
            label["fontColor"] = color


def apply_background(component, resources, skin):
    states = component.get("component_data", {}).get("states", [])
    if not states:
        return
    bg_name = {"紫色": "purpleBg", "黄色": "yellowBg", "蓝色": "blueBg"}[skin]
    set_sprite_value(states[0], sprite_url(resources, f"{skin}__{bg_name}.png"))


def apply_choice(component, resources, skin):
    states = component.get("component_data", {}).get("states", [])
    if not states:
        return
    transform = states[0].get("transform", {})
    wide = transform.get("w", 0) > 340
    names = {
        "紫色": ("aa", "aa1") if wide else ("a", "a1"),
        "黄色": ("b2", "b3") if wide else ("b", "b1"),
        "蓝色": ("c2", "c3") if wide else ("c", "c1"),
    }[skin]
    for idx, name in enumerate(names[: len(states)]):
        set_sprite_value(states[idx], sprite_url(resources, f"{skin}__选择题__{name}.png"))
    set_label_color(component, "#8C3C0B" if skin == "黄色" else "#FFFFFF")


def apply_blank(component, resources, skin):
    prefix = {"紫色": "purple", "黄色": "yellow", "蓝色": "blue"}[skin]
    default_name = "buleDefault" if skin == "蓝色" else f"{prefix}Default"
    selected_name = f"{prefix}Selected"
    states = component.get("component_data", {}).get("states", [])
    if not states:
        return
    urls = [
        sprite_url(resources, f"{skin}__填空题__{default_name}.png"),
        sprite_url(resources, f"{skin}__填空题__{selected_name}.png"),
        sprite_url(resources, f"{skin}__填空题__right.png"),
        sprite_url(resources, f"{skin}__填空题__wrong.png"),
    ]
    for idx, state in enumerate(states):
        set_sprite_value(state, urls[min(idx, len(urls) - 1)])
    set_label_color(component, "#FFFFFF")


def apply_keyboard(component, resources, skin):
    prefix = {"紫色": "purple", "黄色": "yellow", "蓝色": "blue"}[skin]
    states = component.get("component_data", {}).get("states", [])
    keyboard_assets = [
        f"{prefix}Num1",
        f"{prefix}Num2",
        f"{prefix}Delete1",
        f"{prefix}Delete2",
        f"{prefix}Right1",
        f"{prefix}Right2",
    ]
    urls = [
        sprite_url(resources, f"{skin}__填空题__{asset}.png")
        for asset in keyboard_assets
    ]
    for idx, state in enumerate(states):
        sprite = state.get("source", {}).get("MSprite")
        if not isinstance(sprite, dict) or not sprite.get("value"):
            continue
        # The numeric keyboard template repeats default/pressed/disabled groups.
        set_sprite_value(state, urls[(idx - 2) % len(urls)] if idx >= 2 else urls[0])
    set_label_color(component, "#8C3C0B" if skin == "黄色" else "#FFFFFF")


def apply_level_skin(level, resources, skin):
    for component in level.get("components", []):
        data = component.get("component_data", {})
        name = data.get("name", "")
        component_id = component.get("component_id")
        if name == "【勿动】背景图片":
            apply_background(component, resources, skin)
        elif component_id == CHOICE_ID:
            apply_choice(component, resources, skin)
        elif component_id == BLANK_ID:
            apply_blank(component, resources, skin)
        elif component_id == KEYBOARD_ID:
            apply_keyboard(component, resources, skin)
        elif data.get("base") == "MLabel":
            color = TITLE_COLOR[skin] if "题干" in name else TEXT_COLOR[skin]
            set_label_color(component, color)


def main():
    if len(sys.argv) < 3:
        raise SystemExit("Usage: apply_diagnostic_skins.py <config.json> <skin_upload_map.json>")
    config_path = Path(sys.argv[1])
    resource_path = Path(sys.argv[2])
    data = json.loads(config_path.read_text(encoding="utf-8"))
    resources = json.loads(resource_path.read_text(encoding="utf-8"))
    for index, level in enumerate(data.get("game", [])):
        apply_level_skin(level, resources, level_skin(index))
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(config_path)
    print("applied diagnostic skins", len(data.get("game", [])))


if __name__ == "__main__":
    main()
