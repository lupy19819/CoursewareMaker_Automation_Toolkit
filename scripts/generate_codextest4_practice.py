#!/usr/bin/env python3
import copy
import json
import uuid
from pathlib import Path
import sys


ROOT = Path("/Users/tal/Downloads/CoursewareMaker_Automation_Toolkit")
BASE_CONFIG = ROOT / "generated_configs/grade4_summer_diagnostic_full_config.json"
OUTPUT = ROOT / "generated_configs/codextest4_practice_config.json"
sys.path.insert(0, str(ROOT / "standard_question_toolkit/scripts"))

from question_text_layout import get_question_label_specs

QUESTION_IMAGES = {
    "q2": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-23/1b86f66f35ec4c00b30856c9271c37b4.png",
    "q8": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-23/1fe63aa531761420444fae4a8e93aa9d.png",
    "q12": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-23/46009247eb19897c595fabfaec922150.png",
    "q13": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-23/8e6cdcdec21cf56041f66539428ef22c.png",
    "q14": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-23/65244ddb0ce844d9f3765b126af5a983.png",
    "q15": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-23/07ad25877250ebd3765a56298b75a723.png",
}

FIREWORKS_SPINE = "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/spine/136920/2024-05-11/b25d6953490ba8456de8fe5af7877574.zip"
FIREWORKS_AUDIO = "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/audio/296026/2024-05-08/812b96218b5e8a3a4117ad391d6ea311.mp3"
WRONG_AUDIO = "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/audio/345733/2026-03-18/cfa60255e6ca3f100a547de9d0f046af.mp3"

# Purple choice correct / wrong state assets
PURPLE_CHOICE_CORRECT = "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-22/d6fc9acebab9d8b331c78911a1fe1067.png"
PURPLE_CHOICE_WRONG = "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-22/b7bf8aeacba7de40410621df45c47aa8.png"


def load():
    return json.loads(BASE_CONFIG.read_text())


def new_id():
    return f"gamenext_component_uuid_{uuid.uuid4()}"


def clone(comp, index=None):
    x = copy.deepcopy(comp)
    x["component_data"]["id"] = new_id()
    if index is not None:
        x["index"] = index
    return x


def set_level_number(comp, level_no, total):
    for st in comp["component_data"]["states"]:
        if "MRichText" in st.get("source", {}):
            st["source"]["MRichText"]["value"] = f"{level_no}/{total}"
    return comp


def set_text(comp, text, x, y, w, h, font_size=None, align=None, z=None):
    data = comp["component_data"]
    if z is not None:
        data["zIndex"] = z
    for st in data["states"]:
        st["transform"].update({"x": x, "y": y, "w": w, "h": h})
        label = st.setdefault("source", {}).setdefault("MLabel", {})
        label["value"] = text
        if font_size is not None:
            label["fontSize"] = font_size
        if align is not None:
            label["alignType"] = align
    return comp


def reindex_components(comps):
    for index, comp in enumerate(comps):
        comp["index"] = index
    return comps


def make_question_texts(proto, start_index, text, profile, x, y, font_size=None, z=4):
    specs = get_question_label_specs(text, profile, font_size=font_size, center_x=x, center_y=y)
    comps = []
    for offset, spec in enumerate(specs):
        comp = clone(proto, start_index + offset)
        suffix = "" if len(specs) == 1 else f"-行{offset + 1}"
        comp["component_data"]["name"] = f"【可修改】文本-题干{suffix}"
        comps.append(
            set_text(
                comp,
                spec["text"],
                spec["x"],
                spec["y"],
                spec["w"],
                spec["h"],
                spec["font_size"],
                spec["align"],
                z,
            )
        )
    return comps


def set_image(comp, url, x, y, w, h, z=0):
    data = comp["component_data"]
    data["zIndex"] = z
    if "文本-题干" in data.get("name", ""):
        data["name"] = "【可修改】配图"
    for st in data["states"]:
        st["transform"].update({"x": x, "y": y, "w": w, "h": h})
        st.setdefault("source", {}).setdefault("MSprite", {})["value"] = url
        if "MLabel" in st["source"]:
            st["source"]["MLabel"]["value"] = ""
    return comp


def set_blank(comp, answer, x, y, w=218, h=131, font_size=None, z=5):
    data = comp["component_data"]
    data["zIndex"] = z
    tools = data["components"]["tools"]["QuestionForBlank"]
    tools["anwserConfig"]["anwser"] = str(answer)
    tools["fillInteractive"]["numberUnit"] = max(1, len(str(answer)))
    for st in data["states"]:
        st["transform"].update({"x": x, "y": y, "w": w, "h": h})
        label = st.setdefault("source", {}).setdefault("MLabel", {})
        if font_size is not None:
            label["fontSize"] = font_size
    return comp


def ensure_choice_states(comp):
    states = comp["component_data"]["states"]
    names = {s["state"] for s in states}
    base = copy.deepcopy(states[1] if len(states) > 1 else states[0])
    if "correct" not in names:
        st = copy.deepcopy(base)
        st["state"] = "correct"
        st["label"] = "当前组件正确"
        st["source"]["MSprite"]["value"] = PURPLE_CHOICE_CORRECT
        st["source"]["MAudio"]["value"] = ""
        states.append(st)
    if "wrong" not in names:
        st = copy.deepcopy(base)
        st["state"] = "wrong"
        st["label"] = "当前组件错误"
        st["source"]["MSprite"]["value"] = PURPLE_CHOICE_WRONG
        st["source"]["MAudio"]["value"] = ""
        states.append(st)
    return comp


def set_choice(comp, text, x, y, correct=False):
    comp = ensure_choice_states(comp)
    data = comp["component_data"]
    data["components"]["tools"]["AloneClickChoice"]["anwserConfig"]["anwserRadio"] = 1 if correct else 2
    for st in data["states"]:
        st["transform"].update({"x": x, "y": y})
        label = st["source"].get("MLabel", {})
        label["value"] = text
    return comp


def make_fireworks(proto_image, index):
    fw = clone(proto_image, index)
    fw["name"] = "BaseComponent"
    fw["component_name"] = "节点"
    fw["component_id"] = "BaseComponent"
    fw["component_url"] = ""
    data = fw["component_data"]
    data["name"] = "【勿动】闯关成功撒花"
    data["base"] = "MSpine"
    data["zIndex"] = 99
    data["components"]["tools"] = {}
    data["components"]["source"] = {"MSpine": {"w": 4196.01, "h": 1909.72}, "MAudio": 1}
    data["components"]["judgeRules"]["inAnswerPool"] = True
    data["components"]["webEditorCustomInfo"]["isAnswerComponent"] = False
    data["components"]["webEditorCustomInfo"]["isJudgeComponent"] = False
    data["edit"]["curState"] = "default"
    data["states"] = [
        {
            "groupKey": "",
            "state": "default",
            "label": "默认",
            "notDelete": False,
            "transform": {
                "x": 0,
                "y": 0,
                "w": 4196.01,
                "h": 1909.72,
                "scaleX": 1,
                "scaleY": 1,
                "rot": 0,
                "editRot": False,
                "anchorX": 0.5,
                "anchorY": 0.5,
            },
            "source": {
                "MAudio": {"value": "", "loop": False, "loopNum": 1, "audioType": "play_effect_1"},
                "MSpine": {
                    "value": FIREWORKS_SPINE,
                    "spineId": 2722,
                    "opacity": False,
                    "animation": "",
                    "playTime": 1,
                    "waitAudioLoop": False,
                    "timeScale": 1,
                },
            },
            "jump": {"canEdit": True, "opened": 0, "type": "", "to": "", "duration": 0},
            "active": {"canEdit": True, "switch": True, "value": "hide"},
        },
        {
            "groupKey": "",
            "state": "passSuccess",
            "label": "闯关成功",
            "notDelete": False,
            "transform": {
                "x": 0,
                "y": 0,
                "w": 4196.01,
                "h": 1909.72,
                "scaleX": 1,
                "scaleY": 1,
                "rot": 0,
                "editRot": False,
                "anchorX": 0.5,
                "anchorY": 0.5,
            },
            "source": {
                "MAudio": {"value": FIREWORKS_AUDIO, "loop": False, "loopNum": 1, "audioType": "play_effect_1"},
                "MSpine": {
                    "value": FIREWORKS_SPINE,
                    "spineId": 2722,
                    "opacity": False,
                    "animation": "animation",
                    "playTime": 1,
                    "waitAudioLoop": False,
                    "timeScale": 1,
                },
            },
            "jump": {"canEdit": True, "opened": 0, "type": "", "to": "", "duration": 0},
            "active": {"canEdit": True, "switch": False, "value": "show"},
        },
    ]
    return fw


def set_practice_level(level):
    level["levelData"]["autoNextLevel"] = {"auto": True, "wait": 3}
    level["levelData"]["autoStopLevel"] = {"auto": False, "errorCount": 0, "wait": 0}
    level["levelData"]["failAutoReset"] = {"auto": False, "wait": 0}
    return level


def set_wrong_audio(title_comp):
    for st in title_comp["component_data"]["states"]:
        if st["state"] == "level_wrong":
            st["source"]["MAudio"]["value"] = WRONG_AUDIO
        elif st["state"] == "level_correct":
            st["source"]["MAudio"]["value"] = ""
    return title_comp


def make_choice_level(base, level_no, total, stem, options, answer_index, image_url=None, image_rect=None):
    src = base["game"][0 if len(options) == 4 else 2]["components"]
    comps = [
        clone(src[0], 0),
        set_wrong_audio(clone(src[1], 1)),
        clone(src[2], 2),
        set_level_number(clone(src[3], 3), level_no, total),
    ]
    comps.extend(
        make_question_texts(
            src[4],
            4,
            stem,
            "purple_choice_medium" if image_url else "purple_choice_stem",
            0,
            215 if image_url else 150,
            52 if image_url else 60,
        )
    )
    if len(options) == 4:
        positions = [540, 180, -180, -540]
    else:
        positions = [360, 0, -360]
    for i, opt in enumerate(options):
        comps.append(set_choice(clone(src[5 + i], 5 + i), opt, positions[i], -255 if image_url else -230, i == answer_index))
    if image_url:
        img_index = len(comps)
        img_proto = clone(src[-1], img_index)
        x, y, w, h = image_rect
        comps.append(set_image(img_proto, image_url, x, y, w, h, 1))
    comps.append(make_fireworks(src[-1], len(comps)))
    level = copy.deepcopy(base["game"][0])
    level["components"] = reindex_components(comps)
    return set_practice_level(level)


def make_yellow_level(base, level_no, total, title, rows):
    proto = base["game"][7]["components"]
    comps = [
        clone(proto[0], 0),
        set_wrong_audio(clone(proto[1], 1)),
        clone(proto[2], 2),
        set_level_number(clone(proto[3], 3), level_no, total),
        clone(proto[4], 4),
    ]
    title_comps = make_question_texts(
        proto[9],
        5,
        title,
        "yellow_title" if len(title) <= 8 else "yellow_body",
        0,
        335,
        72 if len(title) <= 8 else 58,
    )
    comps.extend(title_comps)
    idx = 5 + len(title_comps)
    for row in rows:
        if row["kind"] == "text_blank":
            comps.append(set_text(clone(proto[5], idx), row["text"], row["text_x"], row["y"], row["text_w"], 115, row.get("font", 58), row.get("align", "right"), 7))
            idx += 1
            comps.append(set_blank(clone(proto[6], idx), row["answer"], row["blank_x"], row["y"], row.get("blank_w", 218), 131, row.get("blank_font", 54), 5))
            idx += 1
        elif row["kind"] == "free_text":
            comps.append(set_text(clone(proto[5], idx), row["text"], row["x"], row["y"], row["w"], row["h"], row.get("font", 50), row.get("align", "left"), 7))
            idx += 1
    comps.append(make_fireworks(proto[2], idx))
    level = copy.deepcopy(base["game"][7])
    level["components"] = reindex_components(comps)
    return set_practice_level(level)


def make_blue_level(base, level_no, total, top_text=None, mid_parts=None, image_url=None, image_rect=None, extra_texts=None):
    proto = base["game"][14]["components"]
    comps = [
        set_wrong_audio(clone(proto[1], 1)),
        clone(proto[2], 2),
        set_level_number(clone(proto[3], 3), level_no, total),
        clone(proto[4], 4),
    ]
    top_text_comps = make_question_texts(
        proto[0],
        0,
        top_text or "",
        "blue_body",
        0,
        205 if top_text else 135,
        50,
    )
    comps = top_text_comps + comps
    idx = 5 + max(0, len(top_text_comps) - 1)
    if mid_parts:
        for part in mid_parts:
            kind = part["kind"]
            if kind == "text":
                text_comp = clone(proto[5], idx)
                text_comp["component_data"]["name"] = f"【可修改】文本{idx}"
                comps.append(set_text(text_comp, part["text"], part["x"], part["y"], part["w"], part["h"], part.get("font", 54), part.get("align", "center"), 7))
                idx += 1
            elif kind == "blank":
                comps.append(set_blank(clone(proto[6], idx), part["answer"], part["x"], part["y"], part.get("w", 218), part.get("h", 131), part.get("font", 54), 5))
                idx += 1
            elif kind == "image":
                comps.append(set_image(clone(proto[7], idx), part["url"], part["x"], part["y"], part["w"], part["h"], 1))
                idx += 1
    if image_url and image_rect:
        x, y, w, h = image_rect
        comps.append(set_image(clone(proto[7], idx), image_url, x, y, w, h, 1))
        idx += 1
    if extra_texts:
        for item in extra_texts:
            text_comp = clone(proto[5], idx)
            text_comp["component_data"]["name"] = f"【可修改】文本{idx}"
            comps.append(set_text(text_comp, item["text"], item["x"], item["y"], item["w"], item["h"], item.get("font", 50), item.get("align", "left"), 7))
            idx += 1
    comps.append(make_fireworks(proto[7], idx))
    level = copy.deepcopy(base["game"][14])
    level["components"] = reindex_components(comps)
    return set_practice_level(level)


def build_levels(base):
    levels = []
    total = 15
    levels.append(make_choice_level(base, 1, total, "下面的数中，只读一个零的是（  ）。", ["608400", "67000420", "3050907"], 1))
    levels.append(make_choice_level(base, 2, total, "对盲棋，谁能蒙着眼睛，把手中的棋放到棋盘上相应的位置，谁就赢。\n谁赢的可能性最大（  ）。", ["小明", "小红", "小宇", "小丁"], 0, QUESTION_IMAGES["q2"], (0, -5, 739, 525)))
    levels.append(make_choice_level(base, 3, total, "下列说法中不正确的是（  ）。", ["射线是直线的一部分", "线段是直线的一部分", "直线的长度大于射线的长度", "直线可以无限延伸"], 2))

    levels.append(make_yellow_level(base, 4, total, "单位换算。", [
        {"kind": "text_blank", "text": "（1）100厘米 =", "text_x": -180, "blank_x": 150, "y": 170, "text_w": 360, "answer": 10},
        {"kind": "text_blank", "text": "分米 =", "text_x": 480, "blank_x": 710, "y": 170, "text_w": 220, "answer": 1},
        {"kind": "free_text", "text": "米；", "x": 900, "y": 170, "w": 100, "h": 100, "font": 58, "align": "left"},
        {"kind": "text_blank", "text": "（2）23平方米 =", "text_x": -180, "blank_x": 170, "y": 35, "text_w": 380, "answer": 2300},
        {"kind": "free_text", "text": "平方分米；    4平方分米 =", "x": 620, "y": 35, "w": 520, "h": 100, "font": 54, "align": "left"},
        {"kind": "text_blank", "text": "", "text_x": 0, "blank_x": 880, "y": 35, "text_w": 0, "answer": 400},
        {"kind": "free_text", "text": "平方厘米；", "x": 1090, "y": 35, "w": 200, "h": 100, "font": 54, "align": "left"},
        {"kind": "text_blank", "text": "（3）", "text_x": -610, "blank_x": -370, "y": -100, "text_w": 140, "answer": 6},
        {"kind": "free_text", "text": "平方米 = 600平方分米 =", "x": 0, "y": -100, "w": 540, "h": 100, "font": 54, "align": "center"},
        {"kind": "text_blank", "text": "", "text_x": 0, "blank_x": 460, "y": -100, "text_w": 0, "answer": 60000},
        {"kind": "free_text", "text": "平方厘米。", "x": 675, "y": -100, "w": 220, "h": 100, "font": 54, "align": "left"},
    ]))

    levels.append(make_yellow_level(base, 5, total, "计算下面各题。（请在试卷上写出过程）", [
        {"kind": "text_blank", "text": "（1）48 × 27 =", "text_x": -150, "blank_x": 170, "y": 180, "text_w": 360, "answer": 1296},
        {"kind": "text_blank", "text": "（2）102 × 85 =", "text_x": -150, "blank_x": 170, "y": 45, "text_w": 360, "answer": 8670},
        {"kind": "text_blank", "text": "（3）754 ÷ 29 =", "text_x": -150, "blank_x": 170, "y": -90, "text_w": 360, "answer": 26},
        {"kind": "text_blank", "text": "（4）876 ÷ 73 =", "text_x": -150, "blank_x": 170, "y": -225, "text_w": 360, "answer": 12},
    ]))

    levels.append(make_yellow_level(base, 6, total, "解方程。", [
        {"kind": "text_blank", "text": "（1）解方程：7x + 5 = 19，解得x =", "text_x": -110, "blank_x": 420, "y": 130, "text_w": 930, "answer": 2, "font": 50, "align": "left"},
        {"kind": "text_blank", "text": "（2）解方程：8（2 + x）= 72，解得x =", "text_x": -110, "blank_x": 440, "y": -30, "text_w": 980, "answer": 7, "font": 50, "align": "left"},
    ]))

    levels.append(make_yellow_level(base, 7, total, "胡胡出门看到一串有规律的数，他想要计算出这串数的和，你能帮帮他吗？", [
        {"kind": "text_blank", "text": "9+13+17+……+97 =", "text_x": -160, "blank_x": 180, "y": 40, "text_w": 420, "answer": 1219, "font": 60},
    ]))

    levels.append(make_blue_level(base, 8, total,
        top_text="如下图所示，其中有",
        mid_parts=[
            {"kind": "blank", "answer": 6, "x": -430, "y": 180},
            {"kind": "text", "text": "条线段，", "x": -250, "y": 180, "w": 220, "h": 90, "font": 54, "align": "left"},
            {"kind": "blank", "answer": 1, "x": -40, "y": 180},
            {"kind": "text", "text": "条直线，", "x": 140, "y": 180, "w": 220, "h": 90, "font": 54, "align": "left"},
            {"kind": "blank", "answer": 8, "x": 350, "y": 180},
            {"kind": "text", "text": "射线。", "x": 520, "y": 180, "w": 180, "h": 90, "font": 54, "align": "left"},
        ],
        image_url=QUESTION_IMAGES["q8"],
        image_rect=(500, 20, 700, 148),
    ))

    levels.append(make_blue_level(base, 9, total,
        top_text="王奶奶家养了5头奶牛，7天产牛奶630千克，照这样计算，8头奶牛15天可生产牛奶",
        mid_parts=[
            {"kind": "blank", "answer": 2160, "x": 180, "y": -10},
            {"kind": "text", "text": "千克。", "x": 390, "y": -10, "w": 180, "h": 90, "font": 56, "align": "left"},
        ],
        extra_texts=[{"text": "（请在试卷上写出过程）", "x": -520, "y": -10, "w": 500, "h": 90, "font": 46, "align": "left"}],
    ))

    levels.append(make_blue_level(base, 10, total,
        top_text="牛牛班期末考试，全班同学的数学平均分是80分，牛牛的数学成绩为90分，其他同学的平均分为79分。",
        mid_parts=[
            {"kind": "text", "text": "问：其他同学有", "x": -450, "y": 10, "w": 280, "h": 90, "font": 52, "align": "left"},
            {"kind": "blank", "answer": 10, "x": -180, "y": 10},
            {"kind": "text", "text": "人，全班有", "x": 40, "y": 10, "w": 240, "h": 90, "font": 52, "align": "left"},
            {"kind": "blank", "answer": 11, "x": 300, "y": 10},
            {"kind": "text", "text": "人。", "x": 500, "y": 10, "w": 100, "h": 90, "font": 52, "align": "left"},
        ],
        extra_texts=[{"text": "（请在试卷上写出计算过程）", "x": 0, "y": -120, "w": 680, "h": 90, "font": 44, "align": "center"}],
    ))

    levels.append(make_blue_level(base, 11, total,
        top_text="一辆汽车运送2000件玻璃仪器，双方协商规定：每件运费2元，如损坏一件，不但扣除本件的运费，还要赔10元，结果实得运费3796元，",
        mid_parts=[
            {"kind": "text", "text": "这次运输过程中共损坏了", "x": -230, "y": -10, "w": 460, "h": 90, "font": 50, "align": "left"},
            {"kind": "blank", "answer": 17, "x": 150, "y": -10},
            {"kind": "text", "text": "件玻璃仪器。", "x": 360, "y": -10, "w": 250, "h": 90, "font": 50, "align": "left"},
        ],
        extra_texts=[{"text": "（请在试卷上写出计算过程）", "x": 620, "y": -10, "w": 420, "h": 90, "font": 42, "align": "left"}],
    ))

    levels.append(make_blue_level(base, 12, total,
        top_text="求下列角的度数。",
        mid_parts=[
            {"kind": "text", "text": "如图，已知∠1 = 90°，∠4 = 65°，求∠2 =", "x": -240, "y": 140, "w": 980, "h": 90, "font": 48, "align": "left"},
            {"kind": "blank", "answer": 25, "x": 320, "y": 140},
            {"kind": "text", "text": "和∠3 =", "x": 520, "y": 140, "w": 200, "h": 90, "font": 48, "align": "left"},
            {"kind": "blank", "answer": 65, "x": 710, "y": 140},
            {"kind": "text", "text": "。", "x": 850, "y": 140, "w": 50, "h": 90, "font": 48, "align": "left"},
        ],
        image_url=QUESTION_IMAGES["q12"],
        image_rect=(560, -80, 466, 404),
    ))

    levels.append(make_blue_level(base, 13, total,
        top_text="某游乐场的停车场汽车停车按时分段计费，收费标准见下表。（请在试卷上写出计算过程）",
        mid_parts=[
            {"kind": "image", "url": QUESTION_IMAGES["q13"], "x": 0, "y": 115, "w": 1020, "h": 286},
            {"kind": "text", "text": "（1）希希家的汽车在该停车场停了7小时，要付", "x": -250, "y": -130, "w": 900, "h": 90, "font": 46, "align": "left"},
            {"kind": "blank", "answer": 13, "x": 310, "y": -130},
            {"kind": "text", "text": "元停车费。", "x": 520, "y": -130, "w": 220, "h": 90, "font": 46, "align": "left"},
            {"kind": "text", "text": "（2）糖糖老师把车停在游乐场停车场，停了14个小时，需要缴费", "x": -160, "y": -250, "w": 1180, "h": 90, "font": 42, "align": "left"},
            {"kind": "blank", "answer": 31, "x": 520, "y": -250},
            {"kind": "text", "text": "元。", "x": 690, "y": -250, "w": 80, "h": 90, "font": 42, "align": "left"},
            {"kind": "text", "text": "（3）如果连连老师交了25元，那么连连老师停了", "x": -240, "y": -360, "w": 980, "h": 90, "font": 42, "align": "left"},
            {"kind": "blank", "answer": 12, "x": 350, "y": -360},
            {"kind": "text", "text": "小时。", "x": 520, "y": -360, "w": 120, "h": 90, "font": 42, "align": "left"},
        ],
    ))

    levels.append(make_blue_level(base, 14, total,
        top_text="胡胡看到一幅图，在图里面出现了好多 个三角形，请你帮他数一数图中有",
        mid_parts=[
            {"kind": "blank", "answer": 24, "x": 350, "y": 175},
            {"kind": "text", "text": "个三角形。", "x": 560, "y": 175, "w": 220, "h": 90, "font": 56, "align": "left"},
        ],
        image_url=QUESTION_IMAGES["q14"],
        image_rect=(0, -55, 760, 513),
    ))

    levels.append(make_blue_level(base, 15, total,
        top_text="如图所示，胡胡有两个相同的直角三角形，他把两个相同的直角三角形叠放在一起，问：阴影部分的面积是",
        mid_parts=[
            {"kind": "blank", "answer": 17, "x": 260, "y": 135},
            {"kind": "text", "text": "平方厘米。（单位：厘米）", "x": 520, "y": 135, "w": 430, "h": 90, "font": 52, "align": "left"},
        ],
        image_url=QUESTION_IMAGES["q15"],
        image_rect=(500, -95, 650, 474),
    ))
    return levels


def main():
    cfg = load()
    cfg["common"]["global_config"]["time_countdown"]["switch_countdown"] = False
    levels = build_levels(cfg)
    cfg["game"] = levels
    OUTPUT.write_text(json.dumps(cfg, ensure_ascii=False, indent=2))
    print(str(OUTPUT))


if __name__ == "__main__":
    main()
