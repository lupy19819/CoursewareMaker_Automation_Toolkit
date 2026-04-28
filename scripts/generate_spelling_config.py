#!/usr/bin/env python3
"""
单词拼拼乐配置生成脚本 v3.0
支持答题区三种组件：slot（拖拽放置区）、space（英语空格）、fixed（固定文本）
"""

import json, uuid, copy, os

# ===== 题目数据 =====
# word_audio_url: 喇叭自动播放的单词发音（GAME_LEVEL_START 后1秒自动播放）
# word_image_url: 节点_37 的单词插图
# answer_area: 答题区组件列表（从左到右）
#   slot  - 拖拽放置区，content 为正确答案
#   space - 英语词间空格（不可交互）
#   fixed - 固定文本字母（不可拖拽）
# items: 拖拽物品列表（乱序，给学生的选项）
LEVELS = [
    {
        "text": "make a snowman",
        "answer_area": [
            {"type": "slot", "content": "m"},
            {"type": "slot", "content": "ake"},
            {"type": "space"},
            {"type": "fixed", "content": "a"},
            {"type": "space"},
            {"type": "slot", "content": "sn"},
            {"type": "slot", "content": "ow"},
            {"type": "slot", "content": "man"},
        ],
        "items": ["sn", "ake", "m", "ow", "man"],
        "word_audio_url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/audio/345733/2026-04-28/e239493a64b7a7452027b4e2fb89f49c.mp3",
        "word_image_url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-28/26b57e6177da88d60eefafc94be7fe5a.png",
    },
    {
        "text": "clean the room",
        "answer_area": [
            {"type": "slot", "content": "cl"},
            {"type": "slot", "content": "ean"},
            {"type": "space"},
            {"type": "slot", "content": "the"},
            {"type": "space"},
            {"type": "slot", "content": "r"},
            {"type": "slot", "content": "oom"},
        ],
        "items": ["ean", "oom", "the", "cl", "r"],
        "word_audio_url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/audio/345733/2026-04-28/6ac7c1c00fefcae73368d5bd7d268566.mp3",
        "word_image_url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-28/6cb587a7cf2a9e61399eddf7697b72f6.png",
    },
    {
        "text": "fat",
        "answer_area": [
            {"type": "slot", "content": "f"},
            {"type": "slot", "content": "a"},
            {"type": "slot", "content": "t"},
        ],
        "items": ["t", "a", "f"],
        "word_audio_url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/audio/345733/2026-04-28/5e5dee35c2efa1d326849af95370f0f3.mp3",
        "word_image_url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-28/852a78cce639ea9254a58e6cf46da6a6.png",
    },
]

# ===== 固定资源（全从新参考配置提取）=====
BASE = "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com"

IMG = {
    "bg":         f"{BASE}/assets/image/345733/2025-04-15/ba880b85b1ecb22d3219f892a3ccc789.png",
    "table":      f"{BASE}/assets/image/345733/2025-04-15/527fee5a2b3f6efacc682d9414d20189.png",
    "mask_bg":    f"{BASE}/assets/image/345733/2025-04-15/f6212cc5dec201968c913015bdc6098f.png",
    "slot_def":   f"{BASE}/assets/image/345733/2025-04-15/8526949e1188945eba88834a0252b932.png",
    "slot_hov":   f"{BASE}/assets/image/345733/2025-04-15/be5d793b5a3ad3718ebc6df0f7fb5b24.png",
    "slot_plc":   f"{BASE}/assets/image/345733/2025-04-15/ef13b4b597432199360be23ea10c8ac6.png",
    "item_def":   f"{BASE}/assets/image/345733/2025-04-15/0999d9af59db1c3f14c4879d82bfe06e.png",
    "item_err":   f"{BASE}/assets/image/345733/2025-04-15/03a6daafb13dea7fd270a442d2100757.png",
    "item_plc":   f"{BASE}/assets/image/345733/2025-04-15/44206c2e655075fb8915d7c1cc636de2.png",
    "text_bg":    f"{BASE}/assets/image/345733/2025-04-16/73024e0e941e07287d03a1240daee1e7.png",
    "text_head":  f"{BASE}/assets/image/345733/2025-04-16/655b9960bcea73df1899e6edf17c69eb.png",
    "text_tail":  f"{BASE}/assets/image/345733/2025-04-16/d8e0c14a800133f64e0cdad1e2391d16.png",
    # 文本头/文本尾「自定义状态1」用的过渡空白图（两者共用）
    "text_blank": f"{BASE}/assets/image/345733/2025-04-15/d606aa1fdcd836d152e17fad6d332b24.png",
    "lvnum_bg":   f"{BASE}/assets/image/V0025307/2025-06-23/86383fe6868d3c5f95e786199dd6af82.png",
}

SPINE_FIN      = f"{BASE}/assets/spine/345733/2025-04-15/3d4c41ce940352581883288c246d0816.zip"
SPINE_FIN_ID   = 44228
SPINE_HORN     = f"{BASE}/assets/spine/136920/2025-04-15/89f75d41b172a99be49bb968404159a3.zip"
SPINE_HORN_ID  = 44272

AUDIO = {
    "fin_entry":  f"{BASE}/assets/audio/345733/2025-04-21/440229ebb5dad494c6444d721282c3bf.mp3",
    "correct":    f"{BASE}/assets/audio/345733/2025-04-21/84fe769d09f625848f2273d2ddc1b163.mp3",
    "wrong":      f"{BASE}/assets/audio/345733/2025-04-21/c7b4c33719fe5f975ee930e121b5e1c5.mp3",
    "placed":     f"{BASE}/assets/audio/345733/2025-04-21/0b159a8aad32ad0ad9d6ccfd6ea77f31.mp3",
    "dragging":   f"{BASE}/assets/audio/345733/2025-04-21/2be351e5ae2928e22921219993ac5102.mp3",
}

# ===== 固定 UUID（跨关卡复用）=====
UUID_BG       = "gamenext_component_uuid_0bd3859e-7d9a-4271-b61a-7163e37f4fcb"
UUID_TABLE    = "gamenext_component_uuid_c070190d-6a68-47ac-b8e6-9105182752fb"
UUID_MASK     = "gamenext_component_uuid_60691e8d-e9e4-49d0-9b25-0e2ef4f45409"
UUID_FIN      = "gamenext_component_uuid_3799ea3d-57b9-49d0-8b89-7f42f8840d2b"
UUID_TH       = "gamenext_component_uuid_826126ae-c7a0-4557-8c3f-63e9d42290f0"
UUID_TT       = "gamenext_component_uuid_7401d729-8274-45db-a9b6-315a54a4c4f6"
UUID_NODE37   = "gamenext_component_uuid_3f2120d9-0e12-4374-bd39-896d60eaf355"
UUID_LVNUM    = "gamenext_component_uuid_d393da57-a032-4460-b90d-e5862139aca3"
UUID_SMOKE    = "gamenext_component_uuid_bde41702-5f25-420f-8cac-36fda83a164b"
UUID_HORN     = "gamenext_component_uuid_be60d1a5-774d-4392-be8e-6d68f9d18cc6"

# 固定状态 key（全局复用，来自参考配置）
K_BG_WAIT       = "custom-1744770901336"
K_FIN_ENTER     = "custom-1744696846240"
K_FIN_DONE      = "custom-1744697563745"
K_FIN_OK        = "custom-1744698172400"
K_FIN_WRONG     = "custom-1744698220830"
K_SMOKE_ENTER   = "custom-1744696897830"
K_SMOKE_DONE    = "custom-1744697941599"
K_SMOKE_WRONG   = "custom-1744699470165"
K_MASK_PREP     = "custom-1744698702273"
K_MASK_HIDE     = "custom-1744697364141"
K_TF_PREP       = "custom-1744698802817"
K_TF_HIDE       = "custom-1744697332541"
K_TH_PREP       = "custom-1744698751758"
K_TH_HIDE       = "custom-1744697355297"
K_TT_PREP       = "custom-1744698824078"
K_TT_HIDE       = "custom-1744697324219"
K_ITEM_HIDE     = "custom-1744705119085"
K_HORN_AUTO     = "custom-1747217853044"

# 布局参数
SLOT_Y     = -93.97   # 放置区 y
SLOT_W     = 237
SPACE_W    = 51       # 英语空格宽度
SLOT_H     = 161
TEXT_CX    = -163.89  # 文本区域水平中心 x
TEXT_Y     = -98.13
TEXT_W     = 458.09
TEXT_H     = 164
ITEM_Y     = -372.0   # 拖拽物品 y
ITEM_W     = 239
ITEM_H     = 170
ITEM_GAP   = 275      # 物品水平间距
ITEM_X_OFFSET = -150  # 拖拽物品整体左移偏移量（避免被 fin 动效遮挡）

# 固定文本宽度：按字符数估算（FZCuYuan 90px，每字符约58px + 边距40）
def fixed_text_w(letter):
    return max(100, len(letter) * 58 + 40)


def uid():
    return f"gamenext_component_uuid_{uuid.uuid4()}"


def make_event_trigger(event_name, source_id, target_state):
    return {
        "action": "changeState", "collapsed": False,
        "event": event_name, "params": {"state": target_state},
        "source": source_id, "trigger": "all_event" if source_id == "system" else "all_state"
    }


def base_comp_data(name, zIndex, base="MSprite", extra_sources=None):
    """生成基础组件 component_data 框架"""
    sources = {"MSprite": 1}
    if base == "MSpine":
        sources = {"MSprite": 1, "MSpine": {"h": 664.75, "w": 657}}
    if extra_sources:
        sources.update(extra_sources)
    return {
        "id": uid(),
        "edit_description": "",
        "component_id": "",
        "name": name,
        "zIndex": zIndex,
        "base": base,
        "components": {
            "tools": {},
            "source": sources,
            "lockState": {"state": False, "componentId": "", "componentName": "", "componentState": ""},
            "judgeRules": {"forbidIfCorrect": False, "inAnswerPool": True},
            "webEditorCustomInfo": {"chain": "", "isAnswerComponent": False, "isJudgeComponent": False}
        },
        "edit": {"lock": True, "curState": "default", "baseNotChange": False},
        "custom": [],
        "state_group": [],
        "states": [],
        "event": {
            "eventMap": [{"label": "点击", "name": "click", "sys": False}],
            "dispatchFunList": [
                {"allowEventName": ["all"], "label": "显示", "name": "onShow"},
                {"allowEventName": ["all"], "label": "隐藏", "name": "onHide"},
                {"allowEventName": ["all"], "label": "旋转", "name": "onRotated"},
                {"allowEventName": ["all"], "label": "倍速", "name": "onTimeScale"},
            ],
            "value": []
        }
    }


def state_sprite(state_key, label, x, y, w, h, img_url,
                 audio_url="", jump_type="", jump_to="", jump_dur=0,
                 active_show=True, active_switch=False,
                 notDelete=False, groupKey="", extra_label_val="", extra_label_color="#000000"):
    src = {
        "MLabel": {"value": extra_label_val, "color": extra_label_color,
                   "fontFamily": "FZCuYuan-M03S", "fontSize": 32,
                   "isBold": False, "isItalic": False, "isUnderline": False,
                   "alignType": "center", "interval": [0,0,0,0,0], "closeable": True},
        "MSprite": {"key": "", "value": img_url}
    }
    if audio_url:
        src["MAudio"] = {"value": audio_url, "loop": False, "loopNum": 1, "audioType": "play_effect_1"}
    return {
        "groupKey": groupKey,
        "state": state_key,
        "label": label,
        "notDelete": notDelete,
        "transform": {"x": x, "y": y, "w": w, "h": h,
                      "scaleX": 1, "scaleY": 1, "rot": 0, "editRot": False,
                      "anchorX": 0.5, "anchorY": 0.5},
        "source": src,
        "jump": {"canEdit": True, "opened": 1 if jump_type else 0, "type": jump_type, "to": jump_to, "duration": jump_dur},
        "active": {"canEdit": True, "switch": active_switch, "value": "show" if active_show else "hide"}
    }


def make_bg(word_text):
    """背景组件（固定UUID，有开场等待状态）"""
    cd = base_comp_data("背景", 0)
    cd["id"] = UUID_BG
    cd["edit"]["curState"] = K_BG_WAIT
    cd["states"] = [
        state_sprite("default", "默认", 0, 0, 2048, 1152, IMG["bg"]),
        state_sprite(K_BG_WAIT, "开场等待", 0, 0, 2048, 1152, IMG["bg"],
                     jump_type="countdown", jump_to="default", jump_dur=1.5),
    ]
    cd["event"]["value"] = [make_event_trigger("GAME_LEVEL_START", "system", K_BG_WAIT)]
    return {"component_data": cd, "component_id": "BaseComponent",
            "component_name": "节点", "component_url": "", "index": 0, "name": "BaseComponent", "version": "0.0.0"}


def make_table():
    """桌子组件（固定UUID）"""
    cd = base_comp_data("桌子", 1)
    cd["id"] = UUID_TABLE
    cd["states"] = [
        state_sprite("default", "默认", 0, -384.56, 2048, 382, IMG["table"],
                     active_switch=False)
    ]
    return {"component_data": cd, "component_id": "BaseComponent",
            "component_name": "节点", "component_url": "", "index": 1, "name": "BaseComponent", "version": "0.0.0"}


def make_space(x, idx_label):
    """英语空格（词间分隔，仅占位，不可交互）"""
    cd = base_comp_data(f"英语空格{idx_label}", 8)
    cd["states"] = [{
        "groupKey": "", "state": "default", "label": "默认", "notDelete": False,
        "transform": {"x": x, "y": SLOT_Y, "w": SPACE_W, "h": SLOT_H,
                      "scaleX": 1, "scaleY": 1, "rot": 0, "editRot": False, "anchorX": 0.5, "anchorY": 0.5},
        "source": {"MSprite": {"key": "", "value": IMG["text_blank"]}},
        "jump": {"canEdit": True, "opened": 0, "type": "", "to": "", "duration": 0},
        "active": {"canEdit": True, "switch": True, "value": "hide"}  # 解锁显影，默认隐藏
    }]
    return {"component_data": cd, "component_id": "BaseComponent",
            "component_name": "节点", "component_url": "", "index": idx_label, "name": "BaseComponent", "version": "0.0.0"}


IMG_FIXED_TEXT_BG = "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-28/70428cf856e3acb0aebcd929d60c4c6b.png"

# 固定文本背景图九宫格配置（同时用于 文本-XX 和 文本-fin）
NINE_GRID_FIXED = {"enable": True, "top": 30.7522, "right": 22.8713, "bottom": 33.0302, "left": 32.0198}

def sprite_with_nine(url, nine_grid=None):
    """构造带九宫格配置的 MSprite source 项"""
    s = {"key": "", "value": url}
    if nine_grid:
        s["nineGrid"] = nine_grid
    return s

def make_fixed_text(letter, x, idx_label):
    """固定文本（答题区中不可拖拽的字母，宽度按内容自适应）"""
    w = fixed_text_w(letter)
    cd = base_comp_data(f"文本-{letter}", 20 - idx_label)
    cd["states"] = [{
        "groupKey": "", "state": "default", "label": "默认", "notDelete": False,
        "transform": {"x": x, "y": SLOT_Y, "w": w, "h": SLOT_H,
                      "scaleX": 1, "scaleY": 1, "rot": 0, "editRot": False, "anchorX": 0.5, "anchorY": 0.5},
        "source": {
            "MLabel": {"value": letter, "color": "#BA7123", "fontFamily": "FZCuYuan-M03S",
                       "fontSize": 90, "isBold": False, "isItalic": False, "isUnderline": False,
                       "alignType": "center", "interval": [0, 40, 0, 0, 0], "closeable": True},
            "MSprite": sprite_with_nine(IMG_FIXED_TEXT_BG, NINE_GRID_FIXED)
        },
        "jump": {"canEdit": True, "opened": 0, "type": "", "to": "", "duration": 0},
        "active": {"canEdit": True, "switch": False, "value": "show"}
    }]
    return {"component_data": cd, "component_id": "BaseComponent",
            "component_name": "节点", "component_url": "", "index": idx_label, "name": "BaseComponent", "version": "0.0.0"}


def make_drag_slot(letter, x, idx_label):
    """拖拽放置区"""
    slot_id = uid()
    cd = {
        "id": slot_id,
        "edit_description": "",
        "component_id": "f9b49402-f73d-11ee-b9ef-8e2f78cd4bcd",
        "name": f"拖拽放置区{idx_label}",
        "zIndex": 20 - idx_label,
        "base": "MSprite",
        "components": {
            "tools": {"LDragPlace": {
                "blinkCount": 2, "blinkTime": 1, "blinkType": "wrong",
                "canMoveDragElement": True, "checkType": "stop",
                "hasBlink": True, "itemList": [letter],
                "numWrongWait": 1, "oneOrMore": "one", "oneReplace": True,
                "placeType": "Center", "placedCountLimit": True, "placedMaxCount": 1,
                "rePos": 1, "showResultState": True, "sort": "unseq",
                "sortData": {"sortType": "left-top", "paddingX": 0, "paddingY": 0,
                             "paddingTop": 0, "paddingBottom": 0, "paddingLeft": 0, "paddingRight": 0},
                "tag": "", "typeWrong": "cur", "typeWrongCount": "wrong", "worngBack": True
            }},
            "source": {"MSprite": 1},
            "lockState": {"state": False, "componentId": "", "componentName": "", "componentState": ""},
            "judgeRules": {"forbidIfCorrect": False, "inAnswerPool": True},
            "webEditorCustomInfo": {"chain": "LDragPlace/LComponent/MComponent/cc.Component/cc.Object",
                                    "isAnswerComponent": True, "isJudgeComponent": True}
        },
        "edit": {"lock": True, "curState": "adsorb", "baseNotChange": False},
        "custom": [],
        "state_group": [],
        "states": [
            {
                "groupKey": "", "state": "default", "label": "默认", "notDelete": False,
                "transform": {"x": x, "y": SLOT_Y, "w": SLOT_W, "h": SLOT_H,
                              "scaleX": 1, "scaleY": 1, "rot": 0, "editRot": False, "anchorX": 0.5, "anchorY": 0.5},
                "source": {"MSprite": {"key": "", "value": IMG["slot_def"]}},
                "jump": {"canEdit": True, "opened": 0, "type": "", "to": "", "duration": 0},
                "active": {"canEdit": True, "switch": False, "value": "show"}
            },
            {
                "groupKey": "", "state": "adsorb", "label": "可吸附", "notDelete": False,
                "transform": {"x": x, "y": SLOT_Y, "w": SLOT_W, "h": SLOT_H,
                              "scaleX": 1, "scaleY": 1, "rot": 0, "editRot": False, "anchorX": 0.5, "anchorY": 0.5},
                "source": {"MAudio": {"value": "", "loop": False, "loopNum": 1, "audioType": "play_effect_1"},
                           "MSprite": {"key": "", "value": IMG["slot_hov"]}},
                "jump": {"canEdit": True, "opened": 0, "type": "", "to": "", "duration": 0},
                "active": {"canEdit": True, "switch": False, "value": "show"}
            },
            {
                "groupKey": "", "state": "adsorbed", "label": "被吸附", "notDelete": False,
                "transform": {"x": x, "y": SLOT_Y, "w": SLOT_W, "h": SLOT_H,
                              "scaleX": 1, "scaleY": 1, "rot": 0, "editRot": False, "anchorX": 0.5, "anchorY": 0.5},
                "source": {"MAudio": {"value": "", "loop": False, "loopNum": 1, "audioType": "play_effect_1"},
                           "MSprite": {"key": "", "value": IMG["slot_plc"]}},
                "jump": {"canEdit": True, "opened": 0, "type": "", "to": "", "duration": 0},
                "active": {"canEdit": True, "switch": False, "value": "show"}
            },
        ],
        "event": {
            "eventMap": [{"label": "点击", "name": "click", "sys": False},
                         {"label": "未作答", "name": "unanswerd", "sys": False},
                         {"label": "作答中", "name": "answering", "sys": False},
                         {"label": "正确", "name": "correct", "sys": False},
                         {"label": "错误", "name": "wrong", "sys": False}],
            "dispatchFunList": [
                {"allowEventName": ["all"], "label": "显示", "name": "onShow"},
                {"allowEventName": ["all"], "label": "隐藏", "name": "onHide"},
                {"allowEventName": ["all"], "label": "旋转", "name": "onRotated"}
            ],
            "value": []
        }
    }
    return {"component_data": cd,
            "component_id": "f9b49402-f73d-11ee-b9ef-8e2f78cd4bcd",
            "component_name": "拖拽放置区",
            "component_url": f"{BASE}/assetboundle/LDragPlace/0.2.0/3X/LDragPlace.zip",
            "index": idx_label, "name": "LDragPlace", "version": "0.2.0"}


def make_drag_item(letter, x, idx_label):
    """拖拽物品"""
    item_id = uid()
    item_h = 167 if len(letter) >= 2 else 170  # 多字母稍矮
    fs = 90
    interval_y = 40  # y offset in interval

    def item_state(state_key, label, img, audio="", active_show=True, active_switch=True,
                   extra_interval_y=40):
        src = {
            "MLabel": {"value": letter, "color": "#BA7123", "fontFamily": "FZCuYuan-M03S",
                       "fontSize": fs, "isBold": False, "isItalic": False, "isUnderline": False,
                       "alignType": "center", "interval": [0, extra_interval_y, 0, 0, 0], "closeable": True},
            "MSprite": {"key": "", "value": img}
        }
        if audio:
            src["MAudio"] = {"value": audio, "loop": False, "loopNum": 1, "audioType": "play_effect_1"}
        return {
            "groupKey": "", "state": state_key, "label": label, "notDelete": False,
            "transform": {"x": x, "y": ITEM_Y, "w": ITEM_W, "h": item_h,
                          "scaleX": 1, "scaleY": 1, "rot": 0, "editRot": False, "anchorX": 0.5, "anchorY": 0.5},
            "source": src,
            "jump": {"canEdit": True, "opened": 0, "type": "", "to": "", "duration": 0},
            "active": {"canEdit": True, "switch": active_switch,
                       "value": "show" if active_show else "hide"}
        }

    cd = {
        "id": item_id,
        "edit_description": "",
        "component_id": "d8b73bec-f719-11ee-b9ef-8e2f78cd4bcd",
        "name": f"拖拽物品-{letter}",
        "zIndex": 17 + idx_label,
        "base": "MSprite",
        "components": {
            "tools": {"MDraggable": {
                "layerRule": "history", "matched": [], "matcher": [],
                "placeType": "Target", "reuse": False, "tag": letter
            }},
            "source": {"MSprite": 1, "MAudio": 1},
            "lockState": {"state": False, "componentId": "", "componentName": "", "componentState": ""},
            "judgeRules": {"forbidIfCorrect": False, "inAnswerPool": True},
            "webEditorCustomInfo": {"chain": "MDraggable/MComponent/cc.Component/cc.Object",
                                    "isAnswerComponent": True, "isJudgeComponent": False}
        },
        "edit": {"lock": True, "curState": "default", "baseNotChange": False},
        "custom": [],
        "state_group": [],
        "states": [
            item_state("default", "默认", IMG["item_def"]),
            item_state("wrong", "当前组件错误", IMG["item_err"], extra_interval_y=50),
            item_state("placed", "放置", IMG["item_plc"], audio=AUDIO["placed"]),
            item_state(K_ITEM_HIDE, "隐藏", IMG["item_def"], extra_interval_y=50,
                       active_show=False),
            item_state("dragging", "拖拽中", IMG["item_def"], audio=AUDIO["dragging"]),
        ],
        "event": {
            "eventMap": [{"label": "点击", "name": "click", "sys": False}],
            "dispatchFunList": [
                {"allowEventName": ["all"], "label": "显示", "name": "onShow"},
                {"allowEventName": ["all"], "label": "隐藏", "name": "onHide"},
                {"allowEventName": ["all"], "label": "旋转", "name": "onRotated"}
            ],
            "value": [
                make_event_trigger("GAME_LEVEL_START", "system", K_ITEM_HIDE),
                make_event_trigger(K_MASK_HIDE, UUID_MASK, "default"),
            ]
        }
    }
    return {"component_data": cd,
            "component_id": "d8b73bec-f719-11ee-b9ef-8e2f78cd4bcd",
            "component_name": "拖拽物品",
            "component_url": f"{BASE}/assetboundle/MDraggbale/0.1.4/3X/MDraggbale.zip",
            "index": idx_label, "name": "MDraggbale", "version": "0.1.4"}


def make_mask_bg():
    """遮挡背景（固定UUID）"""
    cd = base_comp_data("遮挡背景", 7)
    cd["id"] = UUID_MASK
    cd["edit"]["curState"] = K_MASK_PREP
    cd["states"] = [
        state_sprite("default", "默认", 0, 0, 2048, 1152, IMG["mask_bg"], active_switch=True),
        state_sprite(K_MASK_HIDE, "隐藏", 0, 0, 2048, 1152, IMG["bg"],
                     active_switch=True, active_show=False),
        state_sprite(K_MASK_PREP, "准备隐藏", 0, 0, 2048, 1152, IMG["mask_bg"],
                     active_switch=True,
                     jump_type="countdown", jump_to=K_MASK_HIDE, jump_dur=1),
    ]
    cd["event"]["value"] = [make_event_trigger(K_SMOKE_ENTER, UUID_SMOKE, K_MASK_PREP)]
    return {"component_data": cd, "component_id": "BaseComponent",
            "component_name": "节点", "component_url": "", "index": 5, "name": "BaseComponent", "version": "0.0.0"}


def make_fin():
    """fin动效（固定UUID，MSpine）"""
    def spine_state(key, label, anim, play_time, audio="", jump_type="", jump_to="", jump_dur=0):
        src = {"MSpine": {"value": SPINE_FIN, "spineId": SPINE_FIN_ID,
                          "opacity": False, "animation": anim,
                          "playTime": play_time, "waitAudioLoop": False, "timeScale": 1}}
        if audio:
            src["MAudio"] = {"value": audio, "loop": False, "loopNum": 1, "audioType": "play_effect_2"}
        return {
            "groupKey": "", "state": key, "label": label, "notDelete": False,
            "transform": {"x": 732.57, "y": -249.3, "w": 657, "h": 664.75,
                          "scaleX": 1, "scaleY": 1, "rot": 0, "editRot": False, "anchorX": 0.5, "anchorY": 0.5},
            "source": src,
            "jump": {"canEdit": True, "opened": 1 if jump_type else 0,
                     "type": jump_type, "to": jump_to, "duration": jump_dur},
            "active": {"canEdit": True, "switch": False, "value": "show"}
        }

    cd = base_comp_data("fin动效", 2, base="MSpine")
    cd["id"] = UUID_FIN
    cd["components"]["source"] = {"MSprite": 1, "MSpine": {"h": 664.75, "w": 657}}
    cd["states"] = [
        spine_state("default", "默认", "daiji", -1),
        spine_state(K_FIN_ENTER, "入场", "fu", 1, audio=AUDIO["fin_entry"],
                    jump_type="spinePlayFinish", jump_to=K_FIN_DONE),
        spine_state(K_FIN_DONE, "入场完成", "daiji", 1,
                    jump_type="spinePlayFinish", jump_to="default"),
        spine_state(K_FIN_OK, "正确反馈", "zheng", 1, audio=AUDIO["correct"]),
        spine_state(K_FIN_WRONG, "错误反馈", "fu", 1, audio=AUDIO["wrong"],
                    jump_type="spinePlayFinish", jump_to="default"),
    ]
    cd["event"]["value"] = [
        make_event_trigger("GAME_CORRECT_ANSWER", "system", K_FIN_OK),
        make_event_trigger("GAME_WRONG_ANSWER", "system", K_FIN_WRONG),
        make_event_trigger("default", UUID_BG, K_FIN_ENTER),
    ]
    return {"component_data": cd, "component_id": "BaseComponent",
            "component_name": "节点", "component_url": "", "index": 2, "name": "BaseComponent", "version": "0.0.0"}


def make_text_fin(word_text, text_w=None, uid_override=None):
    """文本-fin：宽度按内容自适应，背景图与固定文本相同（带九宫格）"""
    if text_w is None:
        text_w = fixed_text_w(word_text)
    """文本-fin（显示完整单词，含准备隐藏状态机，每关新UUID）"""
    my_id = uid_override or uid()

    def text_state(key, label, active_show=True, active_switch=True,
                   audio="", jump_type="", jump_to="", jump_dur=0):
        src = {
            "MLabel": {"value": word_text, "color": "#BA7123", "fontFamily": "FZCuYuan-M03S",
                       "fontSize": 90, "isBold": False, "isItalic": False, "isUnderline": False,
                       "alignType": "center", "interval": [0, 40, 0, 0, 0], "closeable": True},
            "MSprite": sprite_with_nine(IMG_FIXED_TEXT_BG, NINE_GRID_FIXED)
        }
        if audio:
            src["MAudio"] = {"value": audio, "loop": False, "loopNum": 1, "audioType": "play_effect_1"}
        return {
            "groupKey": "", "state": key, "label": label, "notDelete": False,
            "transform": {"x": TEXT_CX, "y": TEXT_Y, "w": text_w, "h": TEXT_H,
                          "scaleX": 1, "scaleY": 1, "rot": 0, "editRot": False, "anchorX": 0.5, "anchorY": 0.5},
            "source": src,
            "jump": {"canEdit": True, "opened": 1 if jump_type else 0,
                     "type": jump_type, "to": jump_to, "duration": jump_dur},
            "active": {"canEdit": True, "switch": active_switch,
                       "value": "show" if active_show else "hide"}
        }

    cd = base_comp_data("文本-fin", 5)
    cd["id"] = my_id
    cd["edit"]["lock"] = False
    cd["edit"]["curState"] = "default"
    cd["states"] = [
        text_state("default", "默认"),
        text_state(K_TF_HIDE, "自定义状态1", active_show=False),
        text_state(K_TF_PREP, "准备隐藏", jump_type="countdown", jump_to=K_TF_HIDE, jump_dur=1),
    ]
    cd["event"]["value"] = [make_event_trigger(K_SMOKE_ENTER, UUID_SMOKE, K_TF_PREP)]
    return {"component_data": cd, "component_id": "BaseComponent",
            "component_name": "节点", "component_url": "", "index": 4, "name": "BaseComponent", "version": "0.0.0"}


def make_text_head():
    """文本头（固定UUID）"""
    def st(key, label, img, label_val="", active=True, jump_type="", jump_to="", jump_dur=0):
        return {
            "groupKey": "", "state": key, "label": label, "notDelete": False,
            "transform": {"x": TEXT_CX - TEXT_W/2 - 12, "y": TEXT_Y, "w": 31, "h": TEXT_H,
                          "scaleX": 1, "scaleY": 1, "rot": 0, "editRot": False, "anchorX": 0.5, "anchorY": 0.5},
            "source": {
                "MLabel": {"value": label_val, "color": "#BA7123", "fontFamily": "FZCuYuan-M03S",
                           "fontSize": 90, "isBold": False, "isItalic": False, "isUnderline": False,
                           "alignType": "center", "interval": [0, 40 if active else 50, 0, 0, 0], "closeable": True},
                "MSprite": {"key": "", "value": img},
                **({"MAudio": {"value": "", "loop": False, "loopNum": 1, "audioType": "play_effect_1"}} if not active else {})
            },
            "jump": {"canEdit": True, "opened": 1 if jump_type else 0,
                     "type": jump_type, "to": jump_to, "duration": jump_dur},
            "active": {"canEdit": True, "switch": True, "value": "show" if active else "hide"}
        }
    cd = base_comp_data("文本头", 3)
    cd["id"] = UUID_TH
    cd["edit"]["lock"] = False
    cd["states"] = [
        st("default", "默认", IMG["text_head"]),
        st(K_TH_HIDE, "自定义状态1", IMG["text_blank"], label_val="", active=False),
        st(K_TH_PREP, "准备隐藏", IMG["text_head"],
           jump_type="countdown", jump_to=K_TH_HIDE, jump_dur=1),
    ]
    cd["event"]["value"] = [make_event_trigger(K_SMOKE_ENTER, UUID_SMOKE, K_TH_PREP)]
    return {"component_data": cd, "component_id": "BaseComponent",
            "component_name": "节点", "component_url": "", "index": 3, "name": "BaseComponent", "version": "0.0.0"}


def make_text_tail():
    """文本尾（固定UUID）"""
    tail_x = TEXT_CX + TEXT_W/2 + 12
    def st(key, label, img, label_val="", active=True, jump_type="", jump_to="", jump_dur=0):
        return {
            "groupKey": "", "state": key, "label": label, "notDelete": False,
            "transform": {"x": tail_x, "y": TEXT_Y, "w": 31, "h": TEXT_H,
                          "scaleX": 1, "scaleY": 1, "rot": 0, "editRot": False, "anchorX": 0.5, "anchorY": 0.5},
            "source": {
                "MLabel": {"value": label_val, "color": "#BA7123", "fontFamily": "FZCuYuan-M03S",
                           "fontSize": 90, "isBold": False, "isItalic": False, "isUnderline": False,
                           "alignType": "center", "interval": [0, 40 if active else 50, 0, 0, 0], "closeable": True},
                "MSprite": {"key": "", "value": img},
                **({"MAudio": {"value": "", "loop": False, "loopNum": 1, "audioType": "play_effect_1"}} if not active else {})
            },
            "jump": {"canEdit": True, "opened": 1 if jump_type else 0,
                     "type": jump_type, "to": jump_to, "duration": jump_dur},
            "active": {"canEdit": True, "switch": True, "value": "show" if active else "hide"}
        }
    cd = base_comp_data("文本尾", 23)
    cd["id"] = UUID_TT
    cd["edit"]["lock"] = True
    cd["states"] = [
        st("default", "默认", IMG["text_tail"]),
        st(K_TT_HIDE, "自定义状态1", IMG["text_blank"], label_val="", active=False),
        st(K_TT_PREP, "准备隐藏", IMG["text_tail"],
           jump_type="countdown", jump_to=K_TT_HIDE, jump_dur=1),
    ]
    cd["event"]["value"] = [make_event_trigger(K_SMOKE_ENTER, UUID_SMOKE, K_TT_PREP)]
    return {"component_data": cd, "component_id": "BaseComponent",
            "component_name": "节点", "component_url": "", "index": 7, "name": "BaseComponent", "version": "0.0.0"}


def make_text_head_dynamic(head_x):
    """文本头（动态 x 坐标版，固定UUID）"""
    def st(key, label, img, label_val="", active=True, jump_type="", jump_to="", jump_dur=0):
        return {
            "groupKey": "", "state": key, "label": label, "notDelete": False,
            "transform": {"x": head_x, "y": TEXT_Y, "w": 31, "h": TEXT_H,
                          "scaleX": 1, "scaleY": 1, "rot": 0, "editRot": False, "anchorX": 0.5, "anchorY": 0.5},
            "source": {
                "MLabel": {"value": label_val, "color": "#BA7123", "fontFamily": "FZCuYuan-M03S",
                           "fontSize": 90, "isBold": False, "isItalic": False, "isUnderline": False,
                           "alignType": "center", "interval": [0, 40 if active else 50, 0, 0, 0], "closeable": True},
                "MSprite": {"key": "", "value": img},
                **({"MAudio": {"value": "", "loop": False, "loopNum": 1, "audioType": "play_effect_1"}} if not active else {})
            },
            "jump": {"canEdit": True, "opened": 1 if jump_type else 0,
                     "type": jump_type, "to": jump_to, "duration": jump_dur},
            "active": {"canEdit": True, "switch": True, "value": "show" if active else "hide"}
        }
    cd = base_comp_data("文本头", 3)
    cd["id"] = UUID_TH
    cd["edit"]["lock"] = False
    cd["states"] = [
        st("default", "默认", IMG["text_head"]),
        st(K_TH_HIDE, "自定义状态1", IMG["text_blank"], label_val="", active=False),
        st(K_TH_PREP, "准备隐藏", IMG["text_head"],
           jump_type="countdown", jump_to=K_TH_HIDE, jump_dur=1),
    ]
    cd["event"]["value"] = [make_event_trigger(K_SMOKE_ENTER, UUID_SMOKE, K_TH_PREP)]
    return {"component_data": cd, "component_id": "BaseComponent",
            "component_name": "节点", "component_url": "", "index": 3, "name": "BaseComponent", "version": "0.0.0"}


def make_text_tail_dynamic(tail_x):
    """文本尾（动态 x 坐标版，固定UUID）"""
    def st(key, label, img, label_val="", active=True, jump_type="", jump_to="", jump_dur=0):
        return {
            "groupKey": "", "state": key, "label": label, "notDelete": False,
            "transform": {"x": tail_x, "y": TEXT_Y, "w": 31, "h": TEXT_H,
                          "scaleX": 1, "scaleY": 1, "rot": 0, "editRot": False, "anchorX": 0.5, "anchorY": 0.5},
            "source": {
                "MLabel": {"value": label_val, "color": "#BA7123", "fontFamily": "FZCuYuan-M03S",
                           "fontSize": 90, "isBold": False, "isItalic": False, "isUnderline": False,
                           "alignType": "center", "interval": [0, 40 if active else 50, 0, 0, 0], "closeable": True},
                "MSprite": {"key": "", "value": img},
                **({"MAudio": {"value": "", "loop": False, "loopNum": 1, "audioType": "play_effect_1"}} if not active else {})
            },
            "jump": {"canEdit": True, "opened": 1 if jump_type else 0,
                     "type": jump_type, "to": jump_to, "duration": jump_dur},
            "active": {"canEdit": True, "switch": True, "value": "show" if active else "hide"}
        }
    cd = base_comp_data("文本尾", 23)
    cd["id"] = UUID_TT
    cd["edit"]["lock"] = True
    cd["states"] = [
        st("default", "默认", IMG["text_tail"]),
        st(K_TT_HIDE, "自定义状态1", IMG["text_blank"], label_val="", active=False),
        st(K_TT_PREP, "准备隐藏", IMG["text_tail"],
           jump_type="countdown", jump_to=K_TT_HIDE, jump_dur=1),
    ]
    cd["event"]["value"] = [make_event_trigger(K_SMOKE_ENTER, UUID_SMOKE, K_TT_PREP)]
    return {"component_data": cd, "component_id": "BaseComponent",
            "component_name": "节点", "component_url": "", "index": 7, "name": "BaseComponent", "version": "0.0.0"}


def make_node37(word_image_url):
    """节点_37（题目插图，固定UUID，每关图片不同）"""
    cd = base_comp_data("节点_37", 23)
    cd["id"] = UUID_NODE37
    cd["edit"]["lock"] = True
    cd["states"] = [{
        "groupKey": "", "state": "default", "label": "默认", "notDelete": False,
        "transform": {"x": -180.27, "y": 249.03, "w": 380, "h": 383,
                      "scaleX": 1, "scaleY": 1, "rot": 0, "editRot": False, "anchorX": 0.5, "anchorY": 0.5},
        "source": {
            "MLabel": {"value": "", "color": "#000000", "fontFamily": "FZCuYuan-M03S", "fontSize": 32,
                       "isBold": False, "isItalic": False, "isUnderline": False,
                       "alignType": "center", "interval": [0,0,0,0,0], "closeable": True},
            "MSprite": {"key": "", "value": word_image_url}
        },
        "jump": {"canEdit": True, "opened": 0, "type": "", "to": "", "duration": 0},
        "active": {"canEdit": True, "switch": False, "value": "show"}
    }]
    return {"component_data": cd, "component_id": "BaseComponent",
            "component_name": "节点", "component_url": "", "index": 8, "name": "BaseComponent", "version": "0.0.0"}


def make_level_num():
    """关卡数组件（固定UUID，LevelNumber bundle）"""
    cd = {
        "id": UUID_LVNUM,
        "edit_description": "",
        "component_id": "28545aa7-45e5-11f0-9eb3-22a96242b3de",
        "name": "关卡数组件",
        "zIndex": 17,
        "base": "MSprite",
        "components": {
            "tools": {"LevelNumber": {"subjectConfig": {"subjectChoose": "ks"}}},
            "source": {"MSprite": 2},
            "lockState": {"state": False, "componentId": "", "componentName": "", "componentState": ""},
            "judgeRules": {"forbidIfCorrect": False, "inAnswerPool": True},
            "webEditorCustomInfo": {"chain": "", "isAnswerComponent": False, "isJudgeComponent": False}
        },
        "edit": {"lock": True, "curState": "default", "baseNotChange": False, "isLvNumComponent": True},
        "custom": [],
        "state_group": [],
        "states": [{
            "groupKey": "", "state": "default", "label": "默认", "notDelete": False,
            "transform": {"x": 741.89, "y": 484.69, "w": 322, "h": 139,
                          "scaleX": 1, "scaleY": 1, "rot": 0, "editRot": False, "anchorX": 0.5, "anchorY": 0.5},
            "source": {
                "MRichText": {"value": "10/20", "color": "#000000",
                              "colorLeft": "#FF8600", "colorRight": "#7B7D8F",
                              "fontFamily": "FZCuYuan-M03S", "fontSize": 50,
                              "alignType": "center", "interval": [10, 0, 0, -100, 0], "closeable": True},
                "MSprite": {"key": "2", "value": IMG["lvnum_bg"]}
            },
            "jump": {"canEdit": True, "opened": 0, "type": "", "to": "", "duration": 0},
            "active": {"canEdit": True, "switch": False, "value": "show"}
        }],
        "event": {
            "eventMap": [{"label": "点击", "name": "click", "sys": False}],
            "dispatchFunList": [
                {"allowEventName": ["all"], "label": "显示", "name": "onShow"},
                {"allowEventName": ["all"], "label": "隐藏", "name": "onHide"},
                {"allowEventName": ["all"], "label": "旋转", "name": "onRotated"}
            ],
            "value": []
        }
    }
    return {"component_data": cd,
            "component_id": "28545aa7-45e5-11f0-9eb3-22a96242b3de",
            "component_name": "关卡数组件",
            "component_url": f"{BASE}/assetboundle/LevelNumber/0.0.3/3X/LevelNumber.zip",
            "index": 0, "name": "LevelNumber", "version": "0.0.3"}


def make_smoke():
    """遮挡烟雾动效（固定UUID，MSpine）"""
    def spine_state(key, label, anim, active_show, x=-156.84, y=-222.84,
                    audio="", jump_type="", jump_to="", jump_dur=0):
        src = {"MSpine": {"value": SPINE_FIN, "spineId": SPINE_FIN_ID,
                          "opacity": False, "animation": anim,
                          "playTime": 1, "waitAudioLoop": False, "timeScale": 1}}
        if audio:
            src["MAudio"] = {"value": audio, "loop": False, "loopNum": 1, "audioType": "play_effect_1"}
        return {
            "groupKey": "", "state": key, "label": label, "notDelete": False,
            "transform": {"x": x, "y": y, "w": 657, "h": 664.75,
                          "scaleX": 1, "scaleY": 1, "rot": 0, "editRot": False, "anchorX": 0.5, "anchorY": 0.5},
            "source": src,
            "jump": {"canEdit": True, "opened": 1 if jump_type else 0,
                     "type": jump_type, "to": jump_to, "duration": jump_dur},
            "active": {"canEdit": True, "switch": True, "value": "show" if active_show else "hide"}
        }

    cd = base_comp_data("遮挡烟雾动效", 14, base="MSpine")
    cd["id"] = UUID_SMOKE
    cd["components"]["source"] = {"MSprite": 1, "MSpine": {"h": 664.75, "w": 657}}
    cd["edit"]["curState"] = K_SMOKE_WRONG
    cd["states"] = [
        spine_state("default", "默认", "dayanwu", False,
                    jump_type="", jump_to=""),
        spine_state(K_SMOKE_ENTER, "入场", "dayanwu", True,
                    jump_type="spinePlayFinish", jump_to=K_SMOKE_DONE),
        spine_state(K_SMOKE_DONE, "自定义状态1", "dayanwu", False,
                    jump_type="countdown", jump_to="default", jump_dur=0),
        spine_state(K_SMOKE_WRONG, "错误反馈", "dayanwu", True,
                    jump_type="spinePlayFinish", jump_to="default"),
    ]
    cd["event"]["value"] = [
        make_event_trigger(K_FIN_ENTER, UUID_FIN, K_SMOKE_ENTER),
        make_event_trigger(K_FIN_WRONG, UUID_FIN, K_SMOKE_WRONG),
    ]
    return {"component_data": cd, "component_id": "BaseComponent",
            "component_name": "节点", "component_url": "", "index": 6, "name": "BaseComponent", "version": "0.0.0"}


def make_horn(word_audio_url):
    """喇叭（固定UUID，MSpine，clickDown 播放单词音频，GAME_LEVEL_START后1s自动触发）"""
    def horn_state(key, label, anim, audio=None, jump_type="", jump_to="", jump_dur=0, wait_audio=False):
        src = {"MSpine": {"value": SPINE_HORN, "spineId": SPINE_HORN_ID,
                          "opacity": False, "animation": anim,
                          "playTime": 1, "waitAudioLoop": wait_audio, "timeScale": 1}}
        if audio is not None:  # None=不加MAudio；""=加空MAudio占位
            src["MAudio"] = {"value": audio, "loop": False, "loopNum": 1,
                             "audioType": "play_audio" if wait_audio else "play_effect_1"}
        return {
            "groupKey": "", "state": key, "label": label, "notDelete": False,
            "transform": {"x": -904.61, "y": 465.78, "w": 151.89, "h": 149.27,
                          "scaleX": 1, "scaleY": 1, "rot": 0, "editRot": False, "anchorX": 0.5, "anchorY": 0.5},
            "source": src,
            "jump": {"canEdit": True, "opened": 1 if jump_type else 0,
                     "type": jump_type, "to": jump_to, "duration": jump_dur},
            "active": {"canEdit": True, "switch": False, "value": "show"}
        }
    cd = base_comp_data("喇叭", 17, base="MSpine")
    cd["id"] = UUID_HORN
    cd["components"]["source"] = {"MSprite": 1, "MSpine": {"h": 149.27, "w": 151.89}}
    cd["edit"]["curState"] = K_HORN_AUTO
    cd["states"] = [
        horn_state("default", "默认", "lan-laba2_1"),
        horn_state("clickDown", "点击按下", "lan-laba2", audio=word_audio_url,
                   jump_type="audioPlayFinish", jump_to="default", wait_audio=True),
        horn_state(K_HORN_AUTO, "自定义状态1", "lan-laba2_1",
                   audio="",  # 空音频占位，与参考配置对齐
                   jump_type="countdown", jump_to="clickDown", jump_dur=1),
    ]
    cd["event"]["value"] = [make_event_trigger("GAME_LEVEL_START", "system", K_HORN_AUTO)]
    return {"component_data": cd, "component_id": "BaseComponent",
            "component_name": "节点", "component_url": "", "index": 9, "name": "BaseComponent", "version": "0.0.0"}


def calc_answer_area_positions(answer_area):
    """计算答题区各组件的 x 坐标（中心点），以 TEXT_CX 为整体中心"""
    widths = [fixed_text_w(a["content"]) if a["type"] == "fixed" else (SLOT_W if a["type"] == "slot" else SPACE_W) for a in answer_area]
    total = sum(widths)
    cur = TEXT_CX - total / 2
    positions = []
    for w in widths:
        positions.append(cur + w / 2)
        cur += w
    return positions


def calc_text_w(answer_area):
    """答题区总宽度，用于动态 TEXT_W"""
    return sum(fixed_text_w(a["content"]) if a["type"] == "fixed" else (SLOT_W if a["type"] == "slot" else SPACE_W) for a in answer_area)


def calc_item_positions(n):
    """计算 N 个拖拽物品的 x 坐标（整体应用 ITEM_X_OFFSET 左移避免被 fin 动效遮挡）"""
    return [TEXT_CX + ITEM_X_OFFSET + (i - (n-1)/2) * ITEM_GAP for i in range(n)]


def generate_level(q):
    """生成单个关卡的 components 列表"""
    answer_area = q["answer_area"]
    items = q["items"]

    positions = calc_answer_area_positions(answer_area)
    level_text_w = calc_text_w(answer_area)
    text_head_x = TEXT_CX - level_text_w / 2 - 12
    text_tail_x = TEXT_CX + level_text_w / 2 + 12

    n_items = len(items)
    item_xs = calc_item_positions(n_items)

    comps = []
    comps.append(make_bg(q["text"]))
    comps.append(make_table())

    slot_idx = 0
    space_idx = 0
    fixed_idx = 0
    for item, x in zip(answer_area, positions):
        if item["type"] == "slot":
            slot_idx += 1
            comps.append(make_drag_slot(item["content"], x, slot_idx))
        elif item["type"] == "space":
            space_idx += 1
            comps.append(make_space(x, space_idx))
        elif item["type"] == "fixed":
            fixed_idx += 1
            comps.append(make_fixed_text(item["content"], x, fixed_idx))

    for i, (letter, x) in enumerate(zip(items, item_xs)):
        comps.append(make_drag_item(letter, x, i))

    comps.append(make_mask_bg())
    comps.append(make_fin())
    comps.append(make_text_fin(q["text"]))
    comps.append(make_node37(q.get("word_image_url", "")))
    comps.append(make_level_num())
    comps.append(make_smoke())
    comps.append(make_horn(q.get("word_audio_url", "")))
    return comps


def build_transition():
    return {
        "component_id": "c0d68b01-9045-11ef-b825-e6dfda1bc362",
        "component_url": f"{BASE}/assetboundle/Transition_2/0.0.2/3X/Transition_2.zip",
        "component_name": "通用转场2",
        "version": "0.0.2",
        "name": "Transition_2",
        "component_data": {
            "base": "MSprite",
            "component_id": "c0d68b01-9045-11ef-b825-e6dfda1bc362",
            "components": {
                "judgeRules": {"forbidIfCorrect": False, "inAnswerPool": True},
                "lockState": {"componentId": "", "componentName": "", "componentState": "", "state": False},
                "source": {"MSprite": 1},
                "tools": {}
            },
            "custom": [],
            "edit": {"baseNotChange": False, "curState": "default", "lock": True},
            "edit_description": "",
            "event": {"dispatchFunList": [], "eventMap": [], "value": []},
            "id": "gamenext_component_uuid_7f947cab-060c-4e94-bfb4-73d4ad1b9b54",
            "name": "通用转场2",
            "state_group": [],
            "states": [],
            "zIndex": 0
        }
    }


def build_config():
    cfg = {
        "common": {
            "settlement_component": {
                "component_id": "5a446ade-9049-11ef-b825-e6dfda1bc362",
                "component_url": f"{BASE}/assetboundle/OverTipsEN/0.0.5/3X/OverTipsEN.zip",
                "component_name": "英语挑战成功结算",
                "version": "0.0.5",
                "name": "OverTipsEN",
                "component_data": {
                    "base": "MSprite",
                    "component_id": "5a446ade-9049-11ef-b825-e6dfda1bc362",
                    "components": {
                        "judgeRules": {"forbidIfCorrect": False, "inAnswerPool": True},
                        "lockState": {"componentId": "", "componentName": "", "componentState": "", "state": False},
                        "source": {"MSprite": 1},
                        "tools": {"starCount": {"repeatConfig": {}}}
                    },
                    "custom": [],
                    "edit": {"baseNotChange": False, "curState": "default", "lock": True},
                    "edit_description": "",
                    "event": {"dispatchFunList": [], "eventMap": [], "value": []},
                    "id": "gamenext_component_uuid_bbfc65e5-a7bc-4315-9704-37c0166b32c8",
                    "name": "英语挑战成功结算",
                    "state_group": [],
                    "states": [],
                    "zIndex": 0
                },
                "index": 0,
                "lockState": {"componentId": "", "componentName": "", "componentState": "", "state": False},
                "webEditorCustomInfo": {"chain": "", "isAnswerComponent": False, "isJudgeComponent": False}
            },
            "additional_settlement_component": {
                "component_id": "", "component_url": "", "component_name": "",
                "version": "0.0.0", "name": "", "component_data": {}
            },
            "global_config": {
                "font_url": f"{BASE}/assets/font/xesEnglishFont_black.ttf",
                "transparent_canvas": False,
                "time_countdown": {"switch_countdown": False, "countdown_time": 30},
                "score_config": {"type": "average", "score": [], "additional_score": []}
            },
            "levels": {"component_id": "", "component_data": {}},
            "level_settlement": {"component_id": "", "component_data": {}}
        },
        "game": [],
        "additional": [],
        "components": [
            {"component_id": "3a3cba67-f961-11ee-b9ef-8e2f78cd4bcd",
             "component_url": f"{BASE}/assetboundle/OverTips/0.2.0/3X/OverTips.zip"},
            {"component_id": "f9b49402-f73d-11ee-b9ef-8e2f78cd4bcd",
             "component_url": f"{BASE}/assetboundle/LDragPlace/0.2.0/3X/LDragPlace.zip"},
            {"component_id": "d8b73bec-f719-11ee-b9ef-8e2f78cd4bcd",
             "component_url": f"{BASE}/assetboundle/MDraggbale/0.1.4/3X/MDraggbale.zip"},
            {"component_id": "5a446ade-9049-11ef-b825-e6dfda1bc362",
             "component_url": f"{BASE}/assetboundle/OverTipsEN/0.0.5/3X/OverTipsEN.zip"},
            {"component_id": "BaseComponent", "component_url": ""},
            {"component_id": "c0d68b01-9045-11ef-b825-e6dfda1bc362",
             "component_url": f"{BASE}/assetboundle/Transition_2/0.0.2/3X/Transition_2.zip"},
            {"component_id": "28545aa7-45e5-11f0-9eb3-22a96242b3de",
             "component_url": f"{BASE}/assetboundle/LevelNumber/0.0.3/3X/LevelNumber.zip"},
        ]
    }

    for q in LEVELS:
        level = {
            "id": f"gamenext_level_uuid_{uuid.uuid4()}",
            "title": {"component_id": "", "component_url": "", "component_data": {}},
            "video": {"component_id": "", "component_data": {"id": -1, "name": "过场视频", "value": ""}},
            "transition": build_transition(),
            "levelData": {
                "uiConfig": {},
                "judge": {"autoJudge": 1, "judgeRule": 1},
                "errorLimit": {"allowErrorCount": 0},
                "autoNextLevel": {"auto": True, "wait": 2.5},
                "failAutoReset": {"auto": False, "wait": 0},
                "autoStopLevel": {"auto": False, "errorCount": 1, "wait": 0},
                "selectionComponent": {"enabled": False, "selections": [], "repelCount": 0}
            },
            "components": generate_level(q)
        }
        cfg["game"].append(level)

    return cfg


def main():
    os.makedirs("output", exist_ok=True)
    cfg = build_config()

    with open("output/spelling_test_config.json", "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

    print(f"✅ 生成完成：{len(cfg['game'])} 关")
    for i, q in enumerate(LEVELS):
        aa = q["answer_area"]
        n_slots = sum(1 for a in aa if a["type"] == "slot")
        n_spaces = sum(1 for a in aa if a["type"] == "space")
        n_fixed = sum(1 for a in aa if a["type"] == "fixed")
        n_items = len(q["items"])
        n_comps = len(cfg["game"][i]["components"])
        parts = [f"{n_slots} slot"]
        if n_spaces:
            parts.append(f"{n_spaces} space")
        if n_fixed:
            parts.append(f"{n_fixed} fixed")
        parts.append(f"{n_items} 物品")
        print(f"  L{i}: {q['text']} | {' + '.join(parts)} | 共 {n_comps} 组件")
        if not q.get("word_audio_url"):
            print(f"    ⚠️  word_audio_url 未填写（喇叭无音频）")
        if not q.get("word_image_url"):
            print(f"    ⚠️  word_image_url 未填写（节点_37 无图片）")


if __name__ == "__main__":
    main()
