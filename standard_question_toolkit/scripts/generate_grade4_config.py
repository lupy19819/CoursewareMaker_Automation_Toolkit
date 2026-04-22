import copy
import json
import uuid
from pathlib import Path
from unicodedata import east_asian_width

# Layout note:
# This script is an example generator with some fixed coordinates retained for
# historical test sets. New generators should follow
# standard_question_toolkit/docs/layout_generation_method.md:
# build the whole-level content model first, then place recognition/relation/
# operation blocks. Do not tune only the stem text or only by question type.

BASE = Path("D:/codexProject/generated_configs/grade4_summer_diagnostic_q1_q2_q4_q5_config_center_stem.json")
VERT = Path("D:/codexProject/generated_configs/vertical_multiplication_text_grid_fill_config.json")
OUT = Path("D:/codexProject/generated_configs/grade4_summer_diagnostic_full_config.json")

CHOICE_ID = "3b9b8ec3-f7d3-11ee-b9ef-8e2f78cd4bcd"
BLANK_ID = "0b26ef14-f7e0-11ee-b9ef-8e2f78cd4bcd"
BASE_ID = "BaseComponent"
KEYBOARD_ID = "1b1a9c56-f8ab-11ee-b9ef-8e2f78cd4bcd"
ORDINARY_BLANK_SIZE = (218, 131)
VERTICAL_BLANK_SIZE = (128, 180)

STEM_NAME = "【可修改】文本-题干"
TEXT_PREFIX = "【可修改】文本"
KEEP_NAMES = {
    "【题型说明】填空题",
    "【勿动】音频播放按钮",
    "【勿动】背景图片",
    "【勿动】关卡组件",
    "【勿动】简易数字键盘",
}

IMAGES = {
    "q6": {
        "url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-15/d43f5ef87ff390b6ea046af7e173932b.png",
        "width": 613,
        "height": 447,
        "id": 74252,
    },
    "q7": {
        "url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-15/12818d1b2e4ccd6184181cbd7cc25124.png",
        "width": 330,
        "height": 246,
        "id": 74253,
    },
    "q12": {
        "url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-15/4ffebd21da2a0faf0e08051446f25e99.png",
        "width": 316,
        "height": 291,
        "id": 74254,
    },
    "q14": {
        "url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-15/3fc07f12518e18bd425985aab3f91e0a.png",
        "width": 379,
        "height": 193,
        "id": 74255,
    },
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def walk(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield obj, k, v
            yield from walk(v)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield obj, i, v
            yield from walk(v)


def fresh_ids(level):
    level["id"] = "gamenext_level_uuid_" + str(uuid.uuid4())
    id_map = {}
    for _, _, value in list(walk(level)):
        if isinstance(value, str) and value.startswith("gamenext_component_uuid_"):
            id_map.setdefault(value, "gamenext_component_uuid_" + str(uuid.uuid4()))
    for parent, key, value in walk(level):
        if isinstance(value, str) and value in id_map:
            parent[key] = id_map[value]
    return level


def set_transform(component, x=None, y=None, w=None, h=None):
    for state in component.get("component_data", {}).get("states", []):
        tr = state.get("transform")
        if not isinstance(tr, dict):
            continue
        if x is not None:
            tr["x"] = x
        if y is not None:
            tr["y"] = y
        if w is not None:
            tr["w"] = w
        if h is not None:
            tr["h"] = h
        tr["scaleX"] = 1
        tr["scaleY"] = 1


def set_label(component, value, font_size=None, align=None):
    for state in component.get("component_data", {}).get("states", []):
        label = state.get("source", {}).get("MLabel")
        if not isinstance(label, dict):
            continue
        label["value"] = value
        if font_size is not None:
            label["fontSize"] = font_size
        if align is not None:
            label["alignType"] = align


def set_sprite(component, url):
    for state in component.get("component_data", {}).get("states", []):
        sprite = state.get("source", {}).get("MSprite")
        if isinstance(sprite, dict):
            sprite["value"] = url
            if isinstance(sprite.get("nineGrid"), dict):
                sprite["nineGrid"]["enable"] = False


def set_state_audio(component, state_index, audio_config):
    states = component.get("component_data", {}).get("states", [])
    if state_index < len(states) and isinstance(audio_config, dict):
        states[state_index].setdefault("source", {})["MAudio"] = copy.deepcopy(audio_config)


def visual_width(value, font_size):
    total = 0.0
    for char in value:
        if char == " ":
            total += font_size * 0.45
        elif char.isascii():
            total += font_size * 0.58
        elif east_asian_width(char) in "WF":
            total += font_size
        else:
            total += font_size * 0.78
    return total


def formula_width(value, font_size):
    return max(220, min(850, round(visual_width(value, font_size) + 90)))


def is_formula_label(value):
    return any(op in value for op in "+-×÷=")


def clone_component(component, name=None):
    cloned = copy.deepcopy(component)
    cloned["component_data"]["id"] = "gamenext_component_uuid_" + str(uuid.uuid4())
    if name:
        cloned["component_data"]["name"] = name
    return cloned


def blank_answer(component, answer):
    tool = component["component_data"]["components"]["tools"]["QuestionForBlank"]
    tool["anwserConfig"] = {"answerType": "number", "anwser": str(answer)}
    tool["fillInteractive"]["isActivate"] = True
    tool["fillInteractive"]["numberUnit"] = max(1, len(str(answer)))
    tool["fillInteractive"]["tips"] = ""


def set_blank_font_and_unit(component, number_unit, font_size):
    tool = component["component_data"]["components"]["tools"]["QuestionForBlank"]
    tool["fillInteractive"]["numberUnit"] = number_unit
    for state in component["component_data"].get("states", []):
        label = state.get("source", {}).get("MLabel")
        if isinstance(label, dict):
            label["fontSize"] = font_size


def normalize_blank_level(level):
    blanks = [c for c in level.get("components", []) if c.get("component_id") == BLANK_ID]
    if not blanks:
        return
    answers = [
        c["component_data"]["components"]["tools"]["QuestionForBlank"]["anwserConfig"].get("anwser", "")
        for c in blanks
    ]
    max_unit = max(1, *(len(str(answer)) for answer in answers))
    first = blanks[0]["component_data"]["states"][0].get("transform", {})
    is_vertical = first.get("w", 0) <= 150 and first.get("h", 0) >= 150
    font_size = 160 if is_vertical else (54 if max_unit <= 2 else 45)
    for blank in blanks:
        set_blank_font_and_unit(blank, max_unit, font_size)
        for state in blank["component_data"].get("states", []):
            tr = state.get("transform")
            if isinstance(tr, dict):
                tr["scaleX"] = 1
                tr["scaleY"] = 1
                if is_vertical:
                    tr["w"], tr["h"] = VERTICAL_BLANK_SIZE
                else:
                    tr["w"], tr["h"] = ORDINARY_BLANK_SIZE


def apply_keyboard_style(level, keyboard_template):
    for keyboard in [c for c in level.get("components", []) if c.get("component_id") == KEYBOARD_ID]:
        old_data = keyboard["component_data"]
        new_data = copy.deepcopy(keyboard_template["component_data"])
        new_data["id"] = old_data.get("id", new_data.get("id"))
        new_data["name"] = old_data.get("name", new_data.get("name"))
        keyboard["component_data"] = new_data


def find_image_proto(template):
    return next(
        c
        for c in template["components"]
        if c.get("component_id") == BASE_ID
        and c.get("component_data", {}).get("base") == "MSprite"
        and c.get("component_data", {}).get("name") == "【勿动】背景图片"
    )


def add_image(level, image_proto, image_info, x, y, max_w, max_h):
    scale = min(max_w / image_info["width"], max_h / image_info["height"])
    w = round(image_info["width"] * scale)
    h = round(image_info["height"] * scale)
    image = clone_component(image_proto, "【可修改】配图")
    set_sprite(image, image_info["url"])
    set_transform(image, x=x, y=y, w=w, h=h)
    level["components"].append(image)


def make_choice(template, stem, options, correct_index, selected_audio):
    level = fresh_ids(copy.deepcopy(template))
    level["levelData"]["judge"] = {"autoJudge": 0, "judgeRule": 0}
    for component in level["components"]:
        if component.get("component_data", {}).get("name") == STEM_NAME:
            set_label(component, stem, font_size=44, align="center")
            set_transform(component, x=0, y=140, w=1500, h=260)
    choices = [c for c in level["components"] if c.get("component_id") == CHOICE_ID]
    choices.sort(key=lambda c: c["component_data"]["states"][0]["transform"]["x"])
    while len(choices) > len(options):
        removed = choices.pop(0)
        level["components"].remove(removed)
    spacing = 360
    start = -spacing * (len(choices) - 1) / 2
    for i, component in enumerate(choices):
        set_transform(component, x=start + spacing * i, y=-230, w=320, h=132)
        set_label(component, options[i], font_size=38, align="center")
        set_state_audio(component, 1, selected_audio)
        tool = component["component_data"]["components"]["tools"]["AloneClickChoice"]
        tool["anwserConfig"]["anwserRadio"] = 1 if i == correct_index else 2
    reindex(level)
    return level


def make_fill(template, stem, answers, row_labels=None, header_y=330, rows_y=None, two_columns=False):
    level = fresh_ids(copy.deepcopy(template))
    components = level["components"]
    texts = [
        c
        for c in components
        if c.get("component_id") == BASE_ID
        and c.get("component_data", {}).get("base") == "MLabel"
        and c.get("component_data", {}).get("name", "").startswith(TEXT_PREFIX)
    ]
    blanks = [c for c in components if c.get("component_id") == BLANK_ID]
    proto_text = texts[0]
    proto_blank = blanks[0]
    keep = [c for c in components if c.get("component_data", {}).get("name") in KEEP_NAMES]
    text_components, blank_components = [], []
    for i, answer in enumerate(answers):
        text = proto_text if i == 0 else clone_component(proto_text, f"【可修改】文本{i + 1}")
        blank = proto_blank if i == 0 else clone_component(proto_blank, f"【可修改】输入框{i + 1}")
        text_components.append(text)
        blank_components.append(blank)
        keep.extend([text, blank])
    level["components"] = keep

    rows = len(answers)
    if rows_y is None:
        if rows == 1:
            rows_y = [40]
        elif rows == 2:
            rows_y = [110, -110]
        elif rows == 3:
            rows_y = [175, 15, -145]
        else:
            rows_y = [220, 55, -110, -275, -440, -605][:rows]

    if row_labels:
        header = clone_component(proto_text, "【可修改】文本-题干")
        set_label(header, stem, font_size=44, align="center")
        set_transform(header, x=0, y=header_y, w=1550, h=130)
        level["components"].append(header)

    for i, text in enumerate(text_components):
        value = row_labels[i] if row_labels else (stem if i == 0 else "")
        font_size = 42 if rows > 3 else 50
        if two_columns:
            col = i % 2
            row = i // 2
            x_text = -380 if col == 0 else 285
            x_blank = -135 if col == 0 else 530
            y = rows_y[row]
            w = 260
            align = "right"
        elif row_labels and is_formula_label(value):
            y = rows_y[i]
            w = formula_width(value, font_size)
            gap = 35
            group_w = w + gap + ORDINARY_BLANK_SIZE[0]
            x_text = -group_w / 2 + w / 2
            x_blank = -group_w / 2 + w + gap + ORDINARY_BLANK_SIZE[0] / 2
            align = "right"
        elif row_labels:
            y = rows_y[i]
            x_text, x_blank, w, align = -340, 350, 1000, "right"
        else:
            y = rows_y[i]
            x_text, x_blank, w, align = 0, 350, 1450, "center"
        set_label(text, value, font_size=font_size, align=align)
        set_transform(text, x=x_text, y=y, w=w, h=115)
        blank_answer(blank_components[i], answers[i])
        set_transform(blank_components[i], x=x_blank, y=y, w=ORDINARY_BLANK_SIZE[0], h=ORDINARY_BLANK_SIZE[1])

    normalize_blank_level(level)
    reindex(level)
    return level


def make_inline_fill(template, stem, answer, blank_x, blank_y, align="center", text_w=1450, text_h=150):
    level = make_fill(template, stem, [answer])
    text = next(
        c
        for c in level["components"]
        if c.get("component_id") == BASE_ID and c.get("component_data", {}).get("base") == "MLabel"
    )
    blank = next(c for c in level["components"] if c.get("component_id") == BLANK_ID)
    set_label(text, stem, font_size=44, align=align)
    set_transform(text, x=0, y=135, w=text_w, h=text_h)
    set_transform(blank, x=blank_x, y=blank_y, w=ORDINARY_BLANK_SIZE[0], h=ORDINARY_BLANK_SIZE[1])
    normalize_blank_level(level)
    reindex(level)
    return level


def make_image_fill(template, image_proto, stem, answers, image_key, row_labels=None, image_pos=(0, 60, 520, 300), **kwargs):
    level = make_fill(template, stem, answers, row_labels=row_labels, **kwargs)
    add_image(level, image_proto, IMAGES[image_key], *image_pos)
    reindex(level)
    return level


def reindex(level):
    for idx, component in enumerate(level["components"]):
        component["index"] = idx


base = load(BASE)
vertical = load(VERT)
choice_template = base["game"][0]
fill_template = base["game"][2]
image_proto = find_image_proto(fill_template)
vertical_level = fresh_ids(copy.deepcopy(vertical["game"][0]))
normalize_blank_level(vertical_level)
blank_template = next(c for c in fill_template["components"] if c.get("component_id") == BLANK_ID)
blank_active_audio = blank_template["component_data"]["states"][1]["source"]["MAudio"]
standard_keyboard = next(c for c in vertical_level["components"] if c.get("component_id") == KEYBOARD_ID)

levels = [
    make_choice(
        choice_template,
        "长方形长16厘米，宽4厘米，面积是（  ）平方厘米。",
        ["64", "40", "20", "60"],
        0,
        blank_active_audio,
    ),
    make_choice(
        choice_template,
        "要使7□3 ÷ 7的商中间有0，□里最大能填（  ）。",
        ["6", "5", "8", "7"],
        0,
        blank_active_audio,
    ),
    make_choice(
        choice_template,
        "黑珠、白珠按“白、黑、黑、白”的顺序循环排列，一共有182个珠子，最后一个珠子是（  ）。",
        ["黑珠", "白珠", "无法判断"],
        0,
        blank_active_audio,
    ),
    make_fill(
        fill_template,
        "竖式计算",
        ["910", "1296", "399"],
        ["35 × 26 =", "72 × 18 =", "21 × 19 ="],
    ),
    make_fill(
        fill_template,
        "竖式计算",
        ["42", "170", "51"],
        ["294 ÷ 7 =", "680 ÷ 4 =", "357 ÷ 7 ="],
    ),
    make_image_fill(
        fill_template,
        image_proto,
        "根据三（3）班男生一分钟跳绳成绩统计图，把表格填写完整。",
        ["5", "6", "8", "6"],
        "q6",
        ["优秀 =", "良好 =", "及格 =", "不及格 ="],
        image_pos=(0, 95, 500, 300),
        rows_y=[-165, -330],
        two_columns=True,
    ),
    make_image_fill(
        fill_template,
        image_proto,
        "如图是奇思学校操场一角，它的面积是（  ）平方米。（单位：米）",
        ["2600"],
        "q7",
        ["面积 ="],
        image_pos=(0, 90, 420, 270),
        rows_y=[-260],
    ),
    make_fill(
        fill_template,
        "简便计算",
        ["16", "6"],
        ["4.47 + 2.38 + 4.53 + 4.62 =", "4.1 + 1.3 + 1.7 - 1.1 ="],
    ),
    make_inline_fill(
        fill_template,
        "学而思三年级有81名同学参加广播操表演，排成一个实心方阵。如果外面增加一层，共需要增加    个学生。",
        "40",
        blank_x=440,
        blank_y=15,
    ),
    make_inline_fill(
        fill_template,
        "田田给洋娃娃配衣服：上衣3种，裙子2种，鞋子2种。一件上衣加一条裙子加一双鞋算一个搭配方案，田田共有    种搭配方案。",
        "12",
        blank_x=520,
        blank_y=-30,
        text_h=210,
    ),
    make_inline_fill(
        fill_template,
        "小张平时7:10出门，7:30到教室，骑车速度是每分钟90米。周三自行车坏了，他7:00步行出发，7:30准时到教室，他步行的速度是每分钟    米。",
        "60",
        blank_x=565,
        blank_y=-50,
        text_h=240,
    ),
    make_image_fill(
        fill_template,
        image_proto,
        "从最左边的“我”字开始，只能向右、向右下相邻的字读，依次读出“我爱世界杯”。一共有（  ）种不同的读法。",
        ["16"],
        "q12",
        ["读法 ="],
        image_pos=(0, 85, 380, 300),
        rows_y=[-260],
    ),
    make_inline_fill(
        fill_template,
        "四年级（1）班小测有两道思考题：两道题全对12人，第一题做对48人，第二题做对42人，两道题都错3人。全班一共有    名同学。",
        "81",
        blank_x=545,
        blank_y=-35,
        text_h=230,
    ),
    make_image_fill(
        fill_template,
        image_proto,
        "数一数，右面的图中一共有（  ）个三角形。",
        ["42"],
        "q14",
        ["三角形 ="],
        image_pos=(0, 105, 450, 260),
        rows_y=[-250],
    ),
    make_inline_fill(
        fill_template,
        "摩托车和自行车从相距280千米的甲、乙两地相向而行，摩托车每小时行52千米，自行车每小时行18千米，两车从出发到相遇经过    小时。",
        "4",
        blank_x=565,
        blank_y=-40,
        align="left",
        text_w=1300,
        text_h=240,
    ),
]

for level in levels:
    if any(component.get("component_id") == BLANK_ID for component in level.get("components", [])):
        apply_keyboard_style(level, standard_keyboard)
        normalize_blank_level(level)
        reindex(level)

new_data = copy.deepcopy(base)
new_data["game"] = levels
scores = [round((i + 1) * 100 / len(levels)) - round(i * 100 / len(levels)) for i in range(len(levels))]
new_data["common"]["global_config"]["score_config"] = {
    "type": "average",
    "score": scores,
    "additional_score": [],
}
OUT.write_text(json.dumps(new_data, ensure_ascii=False, indent=2), encoding="utf-8")
print(OUT)
print("levels", len(levels))
print("scores", scores, "sum", sum(scores))
