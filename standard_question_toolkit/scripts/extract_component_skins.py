import json
from collections import defaultdict
from pathlib import Path

DOWNLOAD = Path("D:/迅雷下载")
OUT_JSON = Path("D:/codexProject/generated_configs/component_skin_inventory.json")
OUT_MD = Path("D:/codexProject/generated_configs/component_skin_inventory.md")

FILES = [
    ("范例1", DOWNLOAD / "范例1.json"),
    ("范例2", DOWNLOAD / "范例2.json"),
]

BLANK_ID = "0b26ef14-f7e0-11ee-b9ef-8e2f78cd4bcd"
DROP_ID = "f9b49402-f73d-11ee-b9ef-8e2f78cd4bcd"
DRAG_ID = "d8b73bec-f719-11ee-b9ef-8e2f78cd4bcd"
SKIN_NAMES = {
    "a0d71ef21cdf": "沙滩皮肤",
    "df49c4739e95": "图纸皮肤",
    "edb8ccb1e5ae": "紫色星空皮肤",
}


def sprite_value(state):
    return (((state or {}).get("source") or {}).get("MSprite") or {}).get("value") or ""


def label_color(state):
    return (((state or {}).get("source") or {}).get("MLabel") or {}).get("color") or ""


def state_transform(state):
    tr = (state or {}).get("transform") or {}
    return {k: tr.get(k) for k in ("x", "y", "w", "h", "scaleX", "scaleY") if k in tr}


def add_asset(target, url, source):
    if not url:
        return
    item = target.setdefault(url, {"url": url, "sources": []})
    if source not in item["sources"]:
        item["sources"].append(source)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def skin_key(url):
    return url.rsplit("/", 1)[-1].split(".")[0][:12] if url else "unknown"


skins = {}

for file_label, path in FILES:
    data = read_json(path)
    for level_index, level in enumerate(data.get("game", []), start=1):
        components = level.get("components", [])
        bg = next(
            (
                c
                for c in components
                if c.get("component_data", {}).get("base") == "MSprite"
                and c.get("component_data", {}).get("name") == "【勿动】背景图片"
            ),
            None,
        )
        bg_url = sprite_value((bg or {}).get("component_data", {}).get("states", [{}])[0])
        key = skin_key(bg_url)
        skin = skins.setdefault(
            bg_url,
            {
                "skin_key": key,
                "skin_name": SKIN_NAMES.get(key, ""),
                "background": bg_url,
                "used_in": [],
                "input_box": {"default": {}, "answering_or_selected": {}},
                "drop_zone": {"default": {}, "responding": {}},
                "drag_option": {"default": {}, "dragging": {}, "placed": {}},
                "stem_text_background": {},
                "text_colors": {},
            },
        )
        used = f"{file_label} 第{level_index}关"
        if used not in skin["used_in"]:
            skin["used_in"].append(used)

        for component in components:
            cd = component.get("component_data", {})
            name = cd.get("name", "")
            base = cd.get("base", "")
            states = cd.get("states", [])
            cid = component.get("component_id")

            for state in states:
                color = label_color(state)
                if color:
                    color_item = skin["text_colors"].setdefault(
                        color,
                        {"color": color, "sources": []},
                    )
                    color_source = f"{used} / {name} / {state.get('state', '')}"
                    if color_source not in color_item["sources"]:
                        color_item["sources"].append(color_source)

            if cid == BLANK_ID:
                for state in states:
                    state_name = state.get("state", "")
                    url = sprite_value(state)
                    source = f"{used} / {name} / {state_name} / {state.get('label', '')}"
                    if state_name == "default":
                        add_asset(skin["input_box"]["default"], url, source)
                    elif state_name in {"answering", "correct", "wrong", "press", "selected"}:
                        add_asset(skin["input_box"]["answering_or_selected"], url, source)

            if cid == DROP_ID:
                for state in states:
                    state_name = state.get("state", "")
                    url = sprite_value(state)
                    source = f"{used} / {name} / {state_name} / {state.get('label', '')}"
                    if state_name == "default":
                        add_asset(skin["drop_zone"]["default"], url, source)
                    elif state_name in {"adsorb", "adsorbed", "placed", "willCollide", "response", "responding", "dragIn", "selected", "press"}:
                        add_asset(skin["drop_zone"]["responding"], url, source)

            if cid == DRAG_ID:
                for state in states:
                    state_name = state.get("state", "")
                    url = sprite_value(state)
                    source = f"{used} / {name} / {state_name} / {state.get('label', '')}"
                    if state_name == "default":
                        add_asset(skin["drag_option"]["default"], url, source)
                    elif state_name == "dragging":
                        add_asset(skin["drag_option"]["dragging"], url, source)
                    elif state_name == "placed":
                        add_asset(skin["drag_option"]["placed"], url, source)

            if base == "MSprite" and "文本-题干" in name:
                for state in states:
                    url = sprite_value(state)
                    if url:
                        source = f"{used} / {name} / {state.get('state', '')} / {state_transform(state)}"
                        add_asset(skin["stem_text_background"], url, source)


result = {
    "source_files": [str(path) for _, path in FILES],
    "grouping_rule": "按【勿动】背景图片的 MSprite.value 分组",
    "skins": list(skins.values()),
}

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

lines = [
    "# 组件化游戏皮肤素材清单",
    "",
    "分组规则：按每关 `【勿动】背景图片` 的 `MSprite.value` 区分皮肤。",
    "",
]
for idx, skin in enumerate(result["skins"], start=1):
    lines.extend(
        [
            f"## {skin.get('skin_name') or f'皮肤 {idx}'} / {skin['skin_key']}",
            "",
            f"- 使用关卡：{', '.join(skin['used_in'])}",
            f"- 背景图：{skin['background']}",
        ]
    )
    sections = [
        ("输入框默认图", skin["input_box"]["default"]),
        ("输入框选中/输入中图", skin["input_box"]["answering_or_selected"]),
        ("放置区默认图", skin["drop_zone"]["default"]),
        ("放置区响应图", skin["drop_zone"]["responding"]),
        ("拖拽选项默认图", skin["drag_option"]["default"]),
        ("拖拽选项拖拽中图", skin["drag_option"]["dragging"]),
        ("拖拽选项放置态图", skin["drag_option"]["placed"]),
        ("题干文本背景图", skin["stem_text_background"]),
    ]
    for title, assets in sections:
        lines.append(f"- {title}：")
        if not assets:
            lines.append("  - 未在该背景皮肤下发现")
        else:
            for url, item in assets.items():
                lines.append(f"  - {url}")
                lines.append(f"    - 来源：{'; '.join(item['sources'][:6])}")
    lines.append("- 文字色号：")
    for color, item in skin["text_colors"].items():
        lines.append(f"  - `{color}`：{'; '.join(item['sources'][:8])}")
    lines.append("")

OUT_MD.write_text("\n".join(lines), encoding="utf-8")
print(OUT_JSON)
print(OUT_MD)
print("skins", len(result["skins"]))
for skin in result["skins"]:
    print(skin["skin_key"], len(skin["used_in"]), skin["background"])
