import json
import copy
import sys
import uuid
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

BLANK_TEXT_COLOR = {
    "紫色": "#EADFFF",
    "黄色": "#8C3C0B",
    "蓝色": "#FFFFFF",
}

TITLE_COLOR = {
    "紫色": "#EADFFF",
    "黄色": "#000000",
    "蓝色": "#9EFAFF",
}

FONT_RULES = {
    "紫色": {"title": 80, "content": 80, "answer": 90},
    "黄色": {"title": 80, "content": 75, "answer": 75},
    "蓝色": {"title": 60, "content": 60, "answer": 75},
}

IMAGE_SIZE = {
    "3年级-1.png": (1046, 223),
    "3年级-4.png": (1594, 571),
    "3年级-11.png": (1099, 156),
    "3年级-12.png": (605, 404),
    "3年级-15.png": (1033, 218),
    "4年级-1.png": (1259, 380),
    "4年级-2.png": (916, 210),
    "4年级-3.png": (1646, 110),
    "4年级-6-1.png": (853, 508),
    "4年级-6-2.png": (945, 252),
    "4年级-7.png": (730, 525),
    "4年级-9.png": (591, 484),
    "4年级-12.png": (557, 475),
    "4年级-14.png": (919, 521),
    "4年级-15.png": (1209, 202),
}

IMAGE_LAYOUTS = {
    "grade3": {
        0: [("3年级-1.png", 0, 115, 980, 210)],
        3: [("3年级-4.png", 0, 70, 1450, 520)],
        10: [("3年级-11.png", 0, 20, 1040, 150)],
        11: [("3年级-12.png", 0, 25, 600, 330)],
        14: [("3年级-15.png", 140, -90, 900, 190)],
    },
    "grade4": {
        0: [("4年级-1.png", 0, 30, 980, 300)],
        1: [("4年级-2.png", 0, 35, 900, 210)],
        2: [("4年级-3.png", 0, 60, 1350, 110)],
        5: [
            ("4年级-6-1.png", -350, 75, 520, 310),
            ("4年级-6-2.png", 420, 60, 560, 155),
        ],
        6: [("4年级-7.png", 0, 55, 520, 375)],
        8: [("4年级-9.png", 95, 0, 430, 350)],
        11: [("4年级-12.png", 220, 40, 430, 365)],
        13: [("4年级-14.png", 110, 35, 560, 320)],
        14: [("4年级-15.png", 120, -90, 850, 142)],
    },
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


def set_label_style(component, color, font_size=None):
    for state in component.get("component_data", {}).get("states", []):
        label = state.get("source", {}).get("MLabel")
        if not isinstance(label, dict):
            continue
        label["fontColor"] = color
        if font_size is not None:
            label["fontSize"] = font_size


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
    set_label_color(component, BLANK_TEXT_COLOR[skin])


def apply_keyboard(component, resources, skin):
    prefix = {"紫色": "purple", "黄色": "yellow", "蓝色": "blue"}[skin]
    states = component.get("component_data", {}).get("states", [])
    urls = {
        "num_default": sprite_url(resources, f"{skin}__填空题__{prefix}Num1.png"),
        "num_pressed": sprite_url(resources, f"{skin}__填空题__{prefix}Num2.png"),
        "delete_default": sprite_url(resources, f"{skin}__填空题__{prefix}Delete1.png"),
        "delete_pressed": sprite_url(resources, f"{skin}__填空题__{prefix}Delete2.png"),
        "right_default": sprite_url(resources, f"{skin}__填空题__{prefix}Right1.png"),
        "right_pressed": sprite_url(resources, f"{skin}__填空题__{prefix}Right2.png"),
    }
    state_asset = {
        2: "num_default",
        3: "num_pressed",
        4: "num_default",
        5: "delete_default",
        6: "delete_pressed",
        7: "delete_default",
        8: "right_default",
        9: "right_pressed",
        10: "right_default",
    }
    for idx, state in enumerate(states):
        if idx in state_asset:
            set_sprite_value(state, urls[state_asset[idx]])
    set_label_color(component, TEXT_COLOR[skin])


def image_proto(level):
    for component in level.get("components", []):
        if component.get("component_data", {}).get("name") == "【勿动】背景图片":
            return component
    raise ValueError("Missing background component to clone as image proto")


def add_image(level, proto, url, image_name, x, y, max_w, max_h):
    src_w, src_h = IMAGE_SIZE[image_name]
    scale = min(max_w / src_w, max_h / src_h)
    component = copy.deepcopy(proto)
    data = component["component_data"]
    data["id"] = "gamenext_component_uuid_" + str(uuid.uuid4())
    data["name"] = f"【可修改】配图-{image_name}"
    for state in data.get("states", []):
        tr = state.get("transform", {})
        if isinstance(tr, dict):
            tr.update({
                "x": x,
                "y": y,
                "w": round(src_w * scale),
                "h": round(src_h * scale),
                "scaleX": 1,
                "scaleY": 1,
            })
        set_sprite_value(state, url)
    level.setdefault("components", []).append(component)


def apply_images(data, image_resources, grade_key):
    for index, layouts in IMAGE_LAYOUTS.get(grade_key, {}).items():
        level = data["game"][index]
        level["components"] = [
            component for component in level.get("components", [])
            if not component.get("component_data", {}).get("name", "").startswith("【可修改】配图")
        ]
        proto = image_proto(level)
        for image_name, x, y, max_w, max_h in layouts:
            add_image(level, proto, image_resources[image_name], image_name, x, y, max_w, max_h)
        for idx, component in enumerate(level["components"]):
            component["index"] = idx


def apply_level_skin(level, resources, skin):
    for component in level.get("components", []):
        data = component.get("component_data", {})
        name = data.get("name", "")
        component_id = component.get("component_id")
        if name.startswith("【题型说明】"):
            for state in data.get("states", []):
                label = state.get("source", {}).get("MLabel")
                if isinstance(label, dict):
                    label["value"] = ""
            continue
        if name == "【勿动】背景图片":
            apply_background(component, resources, skin)
        elif component_id == CHOICE_ID:
            apply_choice(component, resources, skin)
        elif component_id == BLANK_ID:
            apply_blank(component, resources, skin)
        elif component_id == KEYBOARD_ID:
            apply_keyboard(component, resources, skin)
        elif data.get("base") == "MLabel":
            is_title = "题干" in name
            is_answer = not is_title and skin in {"紫色", "黄色", "蓝色"}
            color = TITLE_COLOR[skin] if is_title else TEXT_COLOR[skin]
            if skin == "蓝色" and is_answer:
                color = "#FFFFFF"
            font_size = FONT_RULES[skin]["title" if is_title else "answer" if is_answer else "content"]
            set_label_style(component, color, font_size)


def main():
    if len(sys.argv) < 3:
        raise SystemExit(
            "Usage: apply_diagnostic_skins.py <config.json> <skin_upload_map.json> "
            "[image_upload_map.json]"
        )
    config_path = Path(sys.argv[1])
    resource_path = Path(sys.argv[2])
    data = json.loads(config_path.read_text(encoding="utf-8"))
    resources = json.loads(resource_path.read_text(encoding="utf-8"))
    for index, level in enumerate(data.get("game", [])):
        apply_level_skin(level, resources, level_skin(index))
    if len(sys.argv) >= 4:
        image_resources = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
        grade_key = "grade3" if "grade3" in config_path.name else "grade4"
        apply_images(data, image_resources, grade_key)
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(config_path)
    print("applied diagnostic skins", len(data.get("game", [])))


if __name__ == "__main__":
    main()
