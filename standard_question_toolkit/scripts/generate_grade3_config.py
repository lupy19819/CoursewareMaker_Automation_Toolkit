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
OUT = Path("D:/codexProject/generated_configs/grade3_summer_diagnostic_full_config.json")

CHOICE_ID = "3b9b8ec3-f7d3-11ee-b9ef-8e2f78cd4bcd"
BLANK_ID = "0b26ef14-f7e0-11ee-b9ef-8e2f78cd4bcd"
BASE_ID = "BaseComponent"
KEYBOARD_ID = "1b1a9c56-f8ab-11ee-b9ef-8e2f78cd4bcd"
ORDINARY_BLANK_SIZE = (218, 131)
VERTICAL_BLANK_SIZE = (128, 180)

STEM_NAME = "【可修改】文本-题干"
TEXT_PREFIX = "【可修改】文本"
QUESTION_TYPE_FILL = "【题型说明】填空题"


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
    for parent, key, value in list(walk(level)):
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


def set_state_audio(component, state_index, audio_config):
    states = component.get("component_data", {}).get("states", [])
    if state_index >= len(states) or not isinstance(audio_config, dict):
        return
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


def formula_component_width(value, font_size):
    return max(220, min(820, round(visual_width(value, font_size) + 90)))


def is_formula_label(value):
    return any(operator in value for operator in "+-×÷=")


def blank_answer(component, answer):
    tool = component["component_data"]["components"]["tools"]["QuestionForBlank"]
    tool["anwserConfig"] = {"answerType": "number", "anwser": str(answer)}
    tool["fillInteractive"]["isActivate"] = True
    tool["fillInteractive"]["numberUnit"] = max(1, len(str(answer)))
    tool["fillInteractive"]["tips"] = ""
    for state in component["component_data"].get("states", []):
        label = state.get("source", {}).get("MLabel")
        if isinstance(label, dict):
            label["fontSize"] = 54 if len(str(answer)) <= 2 else 45


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
    first_transform = blanks[0]["component_data"]["states"][0].get("transform", {})
    is_vertical_blank = first_transform.get("w", 0) <= 150 and first_transform.get("h", 0) >= 150
    font_size = 160 if is_vertical_blank else (54 if max_unit <= 2 else 45)
    for blank in blanks:
        set_blank_font_and_unit(blank, max_unit, font_size)
        for state in blank["component_data"].get("states", []):
            transform = state.get("transform")
            if isinstance(transform, dict):
                transform["scaleX"] = 1
                transform["scaleY"] = 1
                if is_vertical_blank:
                    transform["w"] = VERTICAL_BLANK_SIZE[0]
                    transform["h"] = VERTICAL_BLANK_SIZE[1]
                else:
                    transform["w"] = ORDINARY_BLANK_SIZE[0]
                    transform["h"] = ORDINARY_BLANK_SIZE[1]


def apply_keyboard_style(level, keyboard_template):
    keyboards = [c for c in level.get("components", []) if c.get("component_id") == KEYBOARD_ID]
    for keyboard in keyboards:
        old_data = keyboard["component_data"]
        new_data = copy.deepcopy(keyboard_template["component_data"])
        new_data["id"] = old_data.get("id", new_data.get("id"))
        new_data["name"] = old_data.get("name", new_data.get("name"))
        keyboard["component_data"] = new_data


def clone_component(component, name=None):
    new_component = copy.deepcopy(component)
    new_component["component_data"]["id"] = "gamenext_component_uuid_" + str(uuid.uuid4())
    if name:
        new_component["component_data"]["name"] = name
    return new_component


def make_choice(template, stem, options, correct_index, level_no, selected_audio=None):
    level = fresh_ids(copy.deepcopy(template))
    level["levelData"]["judge"] = {"autoJudge": 0, "judgeRule": 0}
    # Remove image components from choice template; these generated levels are text-first unless user supplies uploaded asset URLs.
    level["components"] = [
        c
        for c in level["components"]
        if not (
            c.get("component_id") == BASE_ID
            and c.get("component_data", {}).get("base") == "MSprite"
            and "图片" in c.get("component_data", {}).get("name", "")
            and c.get("component_data", {}).get("name") != "【勿动】背景图片"
        )
    ]
    for component in level["components"]:
        if component.get("component_data", {}).get("name") == STEM_NAME:
            set_label(component, stem, font_size=44, align="center")
            set_transform(component, x=0, y=160, w=1600, h=280)
    choices = [c for c in level["components"] if c.get("component_id") == CHOICE_ID]
    choices.sort(key=lambda c: c["component_data"]["states"][0]["transform"]["x"])
    while len(choices) > len(options):
        remove = choices.pop(0)
        level["components"].remove(remove)
    spacing = 360
    start = -spacing * (len(choices) - 1) / 2
    for i, component in enumerate(choices):
        set_transform(component, x=start + spacing * i, y=-230, w=320, h=132)
        set_label(component, options[i], font_size=38, align="center")
        set_state_audio(component, 1, selected_audio)
        tool = component["component_data"]["components"]["tools"]["AloneClickChoice"]
        tool["anwserConfig"]["anwserRadio"] = 1 if i == correct_index else 2
    for idx, component in enumerate(level["components"]):
        component["index"] = idx
    return level


def make_fill(
    template,
    stem,
    answers,
    level_no,
    row_labels=None,
    inline_blank_x=None,
    inline_blank_y=None,
    inline_align="center",
    inline_text_w=1600,
    inline_text_h=110,
):
    level = fresh_ids(copy.deepcopy(template))
    components = level["components"]
    text_components = [
        c
        for c in components
        if c.get("component_id") == BASE_ID
        and c.get("component_data", {}).get("base") == "MLabel"
        and c.get("component_data", {}).get("name", "").startswith(TEXT_PREFIX)
    ]
    blank_components = [c for c in components if c.get("component_id") == BLANK_ID]

    proto_text = text_components[0]
    proto_blank = blank_components[0]
    keep = []
    for c in components:
        name = c.get("component_data", {}).get("name", "")
        if name in [QUESTION_TYPE_FILL, "【勿动】音频播放按钮", "【勿动】背景图片", "【勿动】关卡组件", "【勿动】简易数字键盘"]:
            keep.append(c)
    text_components = []
    blank_components = []
    for i, answer in enumerate(answers):
        text = proto_text if i == 0 else clone_component(proto_text, f"【可修改】文本{i+1}")
        blank = proto_blank if i == 0 else clone_component(proto_blank, f"【可修改】输入框{i+1}")
        text_components.append(text)
        blank_components.append(blank)
        keep.extend([text, blank])
    level["components"] = keep

    rows = len(answers)
    if rows == 1:
        ys = [40]
    elif rows == 2:
        ys = [110, -110]
    elif rows == 3:
        ys = [175, 15, -145]
    elif rows <= 6:
        ys = [260, 105, -50, -205, -360, -515][:rows]
    else:
        ys = [260 - i * 155 for i in range(rows)]

    for i, text in enumerate(text_components):
        value = row_labels[i] if row_labels else (stem if i == 0 else "")
        font_size = 42 if rows > 3 else 50
        align = "right"
        x = -340
        w = 1000
        blank_x = 350
        if row_labels and is_formula_label(value):
            w = formula_component_width(value, font_size)
            gap = 35
            blank_w = ORDINARY_BLANK_SIZE[0]
            group_w = w + gap + blank_w
            x = -group_w / 2 + w / 2
            blank_x = -group_w / 2 + w + gap + blank_w / 2
        if inline_blank_x is not None and rows == 1 and not row_labels:
            value = value.replace("多少", "　" * 4, 1)
            align = inline_align
            x = 0
            w = inline_text_w
        set_label(text, value, font_size=font_size, align=align)
        set_transform(text, x=x, y=ys[i], w=w, h=inline_text_h if inline_blank_x is not None and rows == 1 and not row_labels else 110)
    for i, blank in enumerate(blank_components):
        blank_answer(blank, answers[i])
        if inline_blank_x is not None and rows == 1:
            blank_x = inline_blank_x
        elif row_labels:
            value = row_labels[i]
            if is_formula_label(value):
                font_size = 42 if rows > 3 else 50
                w = formula_component_width(value, font_size)
                gap = 35
                blank_x = w / 2 + gap / 2
            else:
                blank_x = 350
        else:
            blank_x = 350
        blank_y = inline_blank_y if inline_blank_y is not None and rows == 1 else ys[i]
        set_transform(blank, x=blank_x, y=blank_y, w=ORDINARY_BLANK_SIZE[0], h=ORDINARY_BLANK_SIZE[1])

    if row_labels:
        # Add a centered stem header using the first text component's clone.
        header = clone_component(proto_text, "【可修改】文本-题干")
        set_label(header, stem, font_size=44, align="center")
        set_transform(header, x=0, y=330, w=1600, h=120)
        level["components"].append(header)

    normalize_blank_level(level)
    for idx, component in enumerate(level["components"]):
        component["index"] = idx
    return level


base = load(BASE)
vertical = load(VERT)
choice_template = base["game"][0]
fill_template = base["game"][2]
vertical_level = fresh_ids(copy.deepcopy(vertical["game"][0]))
normalize_blank_level(vertical_level)
blank_template = next(c for c in fill_template["components"] if c.get("component_id") == BLANK_ID)
blank_active_audio = blank_template["component_data"]["states"][1]["source"]["MAudio"]
standard_keyboard = next(c for c in vertical_level["components"] if c.get("component_id") == KEYBOARD_ID)

choice_questions = [
    (
        "用 6、9、8、2 这四张数字卡片摆出一个最大的四位数（卡片不能旋转），这个数和它的近似数分别是（ ）。",
        ["6982，7000", "9862，10000", "9862，9000"],
        1,
    ),
    (
        "下面计算正确的是（ ）。",
        ["59÷8=7……2", "29÷4=6……5", "48÷6=7……6", "38÷7=5……3"],
        3,
    ),
    (
        "小明收集的邮票数是小红的 5 倍。下面可以表示两人邮票数量关系的是图（ ）。",
        ["小红5份，小明1份", "小红5份，小明5份", "小红1份，小明5份"],
        2,
    ),
    (
        "将图形沿虚线折成一个小立方体。根据原题图，选择其中一个面应是（ ）。",
        ["A", "B", "C", "D"],
        1,
    ),
    (
        "奥奥步行街长300米，在街的一边每隔20米挂一个红灯笼（两端都挂），一共挂了（ ）个红灯笼。",
        ["15", "16", "17"],
        1,
    ),
]

levels = []
for i, (stem, options, correct) in enumerate(choice_questions, 1):
    levels.append(make_choice(choice_template, stem, options, correct, i, selected_audio=blank_active_audio))

levels.append(
    make_fill(
        fill_template,
        "大数计算",
        ["621", "597", "377"],
        6,
        ["（1）263 + 358 =", "（2）62 + 535 =", "（3）338 - 168 + 207 ="],
    )
)
levels.append(
    make_fill(
        fill_template,
        "乘法计算",
        ["24", "72", "210", "10", "3", "2"],
        7,
        ["6 × 4 =", "8 × 9 =", "30 × 7 =", "20 ÷ 2 =", "24 ÷ 8 =", "18 ÷ 9 ="],
    )
)
levels.append(
    make_fill(
        fill_template,
        "列竖式计算",
        ["990", "624"],
        8,
        ["（1）198 × 5 =", "（2）104 × 6 ="],
    )
)
levels.append(vertical_level)
levels.append(
    make_fill(
        fill_template,
        "根据图形特点填空：图（ ）是正方形，图（ ）是三角形，图（ ）是圆。",
        ["7", "6", "2"],
        10,
        ["正方形图号 =", "三角形图号 =", "圆形图号 ="],
    )
)
levels.append(
    make_fill(
        fill_template,
        "○ ÷ 6 = 3 …… ▲，▲ 最大是多少？○ 最大是多少？",
        ["5", "23"],
        11,
        ["▲ 最大 =", "○ 最大 ="],
    )
)
levels.append(
    make_fill(
        fill_template,
        "长方形菜园用 60 米篱笆正好围起来，宽是 10 米，长是多少米？",
        ["20"],
        12,
        inline_blank_x=575,
    )
)
levels.append(
    make_fill(
        fill_template,
        "分段计费：1-30 吨每吨 2 元，31-60 吨每吨 3 元，61 吨及以上每吨 4 元。",
        ["170", "45"],
        13,
        ["用水 65 吨，应缴水费 =", "水费 105 元，可能用水 ="],
    )
)
levels.append(
    make_fill(
        fill_template,
        "8 只猴子 3 天吃了 72 个桃子，每只猴子每天吃的数量相同。",
        ["3", "105"],
        14,
        ["1 只猴子 1 天吃 =", "5 只猴子 7 天吃 ="],
    )
)
levels.append(
    make_fill(
        fill_template,
        "第一天喝了总量的一半多 6 瓶，第二天喝了剩下的一半，\n这时还剩 6 瓶，原来一共买了多少瓶果汁？",
        ["30"],
        15,
        inline_blank_x=-120,
        inline_blank_y=0,
        inline_align="left",
        inline_text_w=1200,
        inline_text_h=220,
    )
)

for level in levels:
    if any(component.get("component_id") == BLANK_ID for component in level.get("components", [])):
        apply_keyboard_style(level, standard_keyboard)
        normalize_blank_level(level)
        for idx, component in enumerate(level["components"]):
            component["index"] = idx

new_data = copy.deepcopy(base)
new_data["game"] = levels
scores = [
    round((i + 1) * 100 / len(levels)) - round(i * 100 / len(levels))
    for i in range(len(levels))
]
new_data["common"]["global_config"]["score_config"] = {
    "type": "average",
    "score": scores,
    "additional_score": [],
}
OUT.write_text(json.dumps(new_data, ensure_ascii=False, indent=2), encoding="utf-8")
print(OUT)
print("levels", len(levels))
