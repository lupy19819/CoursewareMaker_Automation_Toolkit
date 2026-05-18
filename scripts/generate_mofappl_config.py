#!/usr/bin/env python3
"""
generate_mofappl_config.py
魔法拼拼乐配置生成器 — 动态布局版

每题的句子结构和作答区排布按实际题目内容动态计算，不照搬模板坐标。
模板只用于：组件类型骨架、judgeRules、状态结构、皮肤资源URL。

画布：2048 x 1152，坐标系以画布中心为 (0, 0)

用法: python3 generate_mofappl_config.py [输出路径]
"""

import json
import copy
import uuid
import argparse
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# === 输入文件 ===
SPELLING_REF     = os.path.join(BASE, 'reference_configs', 'spelling_validation_ref.json')
MOFAPPL_REF_5    = os.path.join(BASE, 'reference_configs', 'mofappl_configs', '77cb396a-babd-11f0-885a-ba4dce53cceb.json')
MOFAPPL_REF_3    = os.path.join(BASE, 'reference_configs', 'mofappl_configs', 'c3f13451-dfc0-11f0-9165-0e324dbd00ee.json')
# 含 固定文本组件（文本a）的参考配置，用于 fixed text 模板
MOFAPPL_REF_FIXED = os.path.join(BASE, 'reference_configs', 'mofappl_configs', 'bbf611d1-bf91-11f0-9165-0e324dbd00ee.json')

# === 输出 ===
OUTPUT_DIR  = os.path.join(BASE, 'output', 'mofappl_configs')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'mofappl_test.json')

# ─────────────────────────────────────────────
# 布局常量（单词拼拼乐同款坐标系，保持视觉一致）
# ─────────────────────────────────────────────
CANVAS_W   = 2048
CANVAS_H   = 1152

# 作答区（放置区行）
SLOT_Y     = -93.97
SLOT_W     = 237        # 放置区宽度
SLOT_H     = 161
SLOT_GAP   = 8          # 放置区间隔

# 文本区（文本头 / 文本尾 / 固定字母）
TEXT_Y     = -98.13
TEXT_H     = 164
TEXT_HEAD_W = 31        # 文本头固定宽度
TEXT_TAIL_W = 31        # 文本尾固定宽度

# 英语空格宽度（type=space 组件）
SPACE_W    = 51

# 拖拽物品行
ITEM_Y     = -372.0
ITEM_W     = 239
ITEM_H     = 170
ITEM_GAP   = 275        # 物品水平间距
ITEM_X_OFFSET = -150    # 整体左移，避免被 fin 动效遮挡

# 整体作答区水平中心（与单词拼拼乐保持一致）
AREA_CX    = -163.89

# zIndex 层次（数组顺序决定渲染层级，zIndex 仅做排序参考）
ZI_NODE        = 0
ZI_BG_IMG      = 1
ZI_SHADOW      = 5
ZI_IP_CHAR     = 10
ZI_LEVEL_NUM   = 11
ZI_HORN        = 12
ZI_SLOT_BASE   = 13     # 放置区从此递增
ZI_FIXED_TEXT  = 20
ZI_FIN_TEXT    = 21
ZI_IP_SMOKE    = 22
ZI_ITEM_BASE   = 23     # 拖拽物品从此递增（最高层）


def uid():
    return f"gamenext_component_uuid_{uuid.uuid4()}"

def new_level_id():
    return str(uuid.uuid4())


# ─────────────────────────────────────────────
# 动态宽度估算
# ─────────────────────────────────────────────
def fixed_text_w(text: str) -> float:
    """估算固定文本标签宽度（FZCuYuan @90px，每字符约58px + 边距40）"""
    return max(100.0, len(text) * 58 + 40)


def syllable_slot_w(_syllable: str) -> float:
    """放置区宽度固定，保持统一手感"""
    return float(SLOT_W)


# ─────────────────────────────────────────────
# 答题区布局模型
# answer_area: list of dict, 每个元素是一个"组件槽位"
#   type = "head"   → 文本头（句子开头背景图）
#   type = "fixed"  → 固定文本（字母/单词，不可拖拽）
#   type = "slot"   → 拖拽放置区
#   type = "space"  → 英语空格（不可见占位）
#   type = "tail"   → 文本尾
# ─────────────────────────────────────────────
def build_answer_area(sentence_parts: list) -> list:
    """
    把句子结构转换为 answer_area 模型。
    sentence_parts: 顺序列表，每个元素为 dict:
      {"type": "fixed"|"slot"|"space", "content": "..."}
    自动在首尾插入 head/tail。
    """
    area = [{"type": "head", "content": ""}]
    for p in sentence_parts:
        area.append(p)
    area.append({"type": "tail", "content": ""})
    return area


def calc_area_positions(answer_area: list) -> list:
    """
    动态计算每个组件的中心 x 坐标，整体以 AREA_CX 为中心。
    返回与 answer_area 等长的 x 坐标列表。
    """
    widths = []
    for a in answer_area:
        t = a["type"]
        if t == "head":
            widths.append(TEXT_HEAD_W)
        elif t == "tail":
            widths.append(TEXT_TAIL_W)
        elif t == "fixed":
            widths.append(fixed_text_w(a["content"]))
        elif t == "slot":
            widths.append(syllable_slot_w(a.get("content", "")))
        elif t == "space":
            widths.append(SPACE_W)
        else:
            widths.append(50.0)

    total_w = sum(widths)
    cur_x = AREA_CX - total_w / 2
    positions = []
    for w in widths:
        positions.append(cur_x + w / 2)
        cur_x += w
    return positions


def calc_item_positions(n: int) -> list:
    """计算 n 个拖拽物品的中心 x 坐标，整体居中 + ITEM_X_OFFSET 偏移"""
    return [AREA_CX + ITEM_X_OFFSET + (i - (n - 1) / 2) * ITEM_GAP for i in range(n)]


# ─────────────────────────────────────────────
# 从模板中提取"组件骨架"（只取结构，不取坐标）
# ─────────────────────────────────────────────
def get_template_comp(template_level, name_contains):
    """从模板关卡中找第一个名称含 name_contains 的组件（深拷贝）"""
    for c in template_level['components']:
        if name_contains in c['component_data']['name']:
            return copy.deepcopy(c)
    return None


def get_all_template_comps(template_level, name_contains):
    return [copy.deepcopy(c) for c in template_level['components']
            if name_contains in c['component_data']['name']]


# ─────────────────────────────────────────────
# 组件构建函数（动态坐标）
# ─────────────────────────────────────────────
def set_transform(cd, x, y, w, h, scale_x=1.0, scale_y=1.0):
    """把坐标写入 component_data 的 transform 字段（顶层 + 各 state）"""
    tf = {
        'x': round(x, 2), 'y': round(y, 2),
        'w': round(w, 2), 'h': round(h, 2),
        'scaleX': scale_x, 'scaleY': scale_y,
        'rotation': 0, 'anchorX': 0.5, 'anchorY': 0.5
    }
    cd['transform'] = tf
    # 同步更新所有 state 的 transform（游戏引擎实际读 states[i].transform）
    for st in cd.get('states', []):
        if 'transform' in st:
            st['transform'].update({'x': tf['x'], 'y': tf['y'], 'w': tf['w'], 'h': tf['h']})


def make_slot_comp(template_slot, slot_val: str, x: float, idx: int) -> dict:
    """生成一个放置区组件（坐标动态）"""
    c = copy.deepcopy(template_slot)
    cd = c['component_data']
    cd['id'] = uid()
    cd['name'] = f'拖拽放置区{idx}'
    cd['zIndex'] = ZI_SLOT_BASE + idx

    # 写入答案
    tools = cd['components'].get('tools', {})
    if 'LDragPlace' in tools:
        tools['LDragPlace']['itemList'] = [slot_val]

    # 动态坐标
    set_transform(cd, x, SLOT_Y, SLOT_W, SLOT_H)
    return c


def make_item_comp(template_item, tag: str, x: float, idx: int) -> dict:
    """生成一个拖拽物品组件（坐标动态）"""
    c = copy.deepcopy(template_item)
    cd = c['component_data']
    cd['id'] = uid()
    cd['name'] = f'拖拽物品{idx}'
    cd['zIndex'] = ZI_ITEM_BASE + idx

    tools = cd['components'].get('tools', {})
    if 'MDraggable' in tools:
        tools['MDraggable']['tag'] = tag

    # 更新显示文字（MLabel.value）
    for st in cd.get('states', []):
        src = st.get('source', {})
        if 'MLabel' in src and isinstance(src['MLabel'], dict):
            src['MLabel']['value'] = tag

    # 动态坐标
    set_transform(cd, x, ITEM_Y, ITEM_W, ITEM_H)
    return c


def make_fixed_text_comp(template_fixed, text: str, x: float, idx: int) -> dict:
    """生成一个固定文本组件（坐标动态）"""
    c = copy.deepcopy(template_fixed)
    cd = c['component_data']
    cd['id'] = uid()
    cd['name'] = f'文本-{text}'
    cd['zIndex'] = ZI_FIXED_TEXT + idx
    w = fixed_text_w(text)
    set_transform(cd, x, TEXT_Y, w, TEXT_H)

    # 更新 MLabel 文本
    for st in cd.get('states', []):
        src = st.get('source', {})
        if 'MLabel' in src:
            src['MLabel']['value'] = text
    return c


def make_space_comp(template_space, x: float, idx: int) -> dict:
    """生成一个英语空格组件（坐标动态）"""
    c = copy.deepcopy(template_space)
    cd = c['component_data']
    cd['id'] = uid()
    cd['name'] = f'英语空格{idx}'
    set_transform(cd, x, TEXT_Y, SPACE_W, TEXT_H)
    return c


def make_head_comp(template_head, x: float, total_area_w: float) -> dict:
    """文本头（固定宽，坐标动态）"""
    c = copy.deepcopy(template_head)
    cd = c['component_data']
    cd['id'] = uid()
    cd['name'] = '文本头'
    cd['zIndex'] = ZI_FIXED_TEXT
    set_transform(cd, x, TEXT_Y, TEXT_HEAD_W, TEXT_H)
    return c


def make_tail_comp(template_tail, x: float) -> dict:
    """文本尾（固定宽，坐标动态）"""
    c = copy.deepcopy(template_tail)
    cd = c['component_data']
    cd['id'] = uid()
    cd['name'] = '文本尾'
    cd['zIndex'] = ZI_FIXED_TEXT
    set_transform(cd, x, TEXT_Y, TEXT_TAIL_W, TEXT_H)
    return c


def make_horn_comp(template_horn, audio_url: str) -> dict:
    """生成喇叭组件，更新音频 URL"""
    c = copy.deepcopy(template_horn)
    cd = c['component_data']
    cd['id'] = uid()
    if audio_url:
        for st in cd.get('states', []):
            if st.get('state') == 'clickDown':
                src = st.setdefault('source', {})
                if 'MAudio' not in src:
                    src['MAudio'] = {}
                if isinstance(src['MAudio'], dict):
                    src['MAudio']['value'] = audio_url
                    src['MAudio']['key'] = ''
    return c


# ─────────────────────────────────────────────
# 关卡生成（核心）
# ─────────────────────────────────────────────
def build_level(template_level, question: dict, level_idx: int) -> dict:
    """
    根据题目数据动态生成一个关卡。
    question 字段:
      sentence_parts: list of {"type": "fixed"|"slot"|"space", "content": "..."}
      slots: ["syllable1", "syllable2", ...]   正确答案列表（与 slot 类型一一对应）
      items: ["tag1", "tag2", ...]             拖拽物品 tag 列表
      audio_url: str
      sentence: str   完整句子文本（用于文本-fin）
    """
    sentence_parts = question.get('sentence_parts', [])
    slots = question.get('slots', [])
    items = question.get('items', [])
    audio_url = question.get('audio_url', '')
    sentence_text = question.get('sentence', ' '.join(slots))

    # 构建 answer_area 模型
    answer_area = build_answer_area(sentence_parts)

    # 动态计算坐标
    positions = calc_area_positions(answer_area)
    total_area_w = sum(
        TEXT_HEAD_W if a['type'] == 'head' else
        TEXT_TAIL_W if a['type'] == 'tail' else
        fixed_text_w(a['content']) if a['type'] == 'fixed' else
        syllable_slot_w(a.get('content', '')) if a['type'] == 'slot' else
        SPACE_W
        for a in answer_area
    )
    item_xs = calc_item_positions(len(items))

    # 从模板提取骨架组件
    tmpl_slot  = get_template_comp(template_level, '拖拽放置区')
    tmpl_item  = get_template_comp(template_level, '拖拽物品')
    tmpl_fixed = get_template_comp(template_level, '文本-')   # 固定字母
    tmpl_head  = get_template_comp(template_level, '文本头')
    tmpl_tail  = get_template_comp(template_level, '文本尾')
    tmpl_horn  = get_template_comp(template_level, '喇叭')

    # 如果模板缺某类组件，用 fallback
    if tmpl_fixed is None:
        tmpl_fixed = tmpl_slot   # 以放置区作 fallback，后续会覆盖 base
    if tmpl_head is None:
        tmpl_head = copy.deepcopy(tmpl_slot)
    if tmpl_tail is None:
        tmpl_tail = copy.deepcopy(tmpl_slot)

    # ── 组装组件列表（顺序即层级，靠后 = 更高层）──
    comps = []

    # 1. 保留非作答区的"装饰性"组件（背景、IP、喇叭等）
    skip_names = {'拖拽放置区', '拖拽物品', '文本头', '文本尾', '文本-', '英语空格'}
    for c in template_level['components']:
        name = c['component_data']['name']
        if not any(k in name for k in skip_names):
            kept = copy.deepcopy(c)
            kept['component_data']['id'] = uid()
            comps.append(kept)

    # 2. 作答区：按 answer_area 顺序生成组件
    slot_answer_idx = 0  # 当前是第几个 slot（对应 slots 列表）
    slot_comp_idx   = 0
    space_idx       = 0
    fixed_idx       = 0

    for a, x in zip(answer_area, positions):
        t = a['type']
        if t == 'head':
            comps.append(make_head_comp(tmpl_head, x, total_area_w))
        elif t == 'tail':
            comps.append(make_tail_comp(tmpl_tail, x))
        elif t == 'slot':
            slot_comp_idx += 1
            slot_val = slots[slot_answer_idx] if slot_answer_idx < len(slots) else ''
            slot_answer_idx += 1
            comps.append(make_slot_comp(tmpl_slot, slot_val, x, slot_comp_idx))
        elif t == 'space':
            space_idx += 1
            if tmpl_fixed:
                comps.append(make_space_comp(tmpl_fixed, x, space_idx))
        elif t == 'fixed':
            fixed_idx += 1
            if tmpl_fixed:
                comps.append(make_fixed_text_comp(tmpl_fixed, a['content'], x, fixed_idx))

    # 3. 文本-fin（句子展示，最高层之前）
    fin_comp = get_template_comp(template_level, '文本-')
    if fin_comp is None:
        # 3槽模板里叫 文本drop，也可用来作为句子展示
        fin_comp = get_template_comp(template_level, '文本drop')
    if fin_comp is None:
        fin_comp = copy.deepcopy(tmpl_fixed)
    if fin_comp:
        cd = fin_comp['component_data']
        cd['id'] = uid()
        cd['name'] = f'文本-{sentence_text}'
        cd['zIndex'] = ZI_FIN_TEXT
        set_transform(cd, AREA_CX, TEXT_Y, max(total_area_w, 300), TEXT_H)
        for st in cd.get('states', []):
            src = st.get('source', {})
            if 'MLabel' in src:
                src['MLabel']['value'] = sentence_text
        comps.append(fin_comp)

    # 4. 喇叭（音频，放在作答区之上）
    if tmpl_horn:
        comps.append(make_horn_comp(tmpl_horn, audio_url))

    # 5. 拖拽物品（最高层）
    if tmpl_item:
        for i, (tag, x) in enumerate(zip(items, item_xs)):
            comps.append(make_item_comp(tmpl_item, tag, x, i + 1))

    # 组装关卡
    level = copy.deepcopy(template_level)
    level['id'] = new_level_id()
    level['components'] = comps
    return level


# ─────────────────────────────────────────────
# 从单词拼拼乐校验文件提取题目数据
# ─────────────────────────────────────────────
def extract_spelling_level_data(spell_level):
    """从单词拼拼乐关卡提取 slots / items / audio_url"""
    comps_raw = spell_level['components']
    slots, items = [], []
    audio_url = None
    loudspeaker_raw = None

    for raw in comps_raw:
        cd = raw['component_data']
        name = cd['name']
        tools = cd['components'].get('tools', {})

        if '英语空格' in name:
            continue

        if 'LDragPlace' in tools:
            ldp = tools['LDragPlace']
            slots.append(ldp.get('itemList', [''])[0])

        if 'MDraggbale' in tools or 'MDraggable' in tools:
            tag = name.replace('拖拽物品-', '').replace('拖拽物品', '').strip()
            items.append(tag)

        if '喇叭' in name and cd.get('base') == 'MSpine':
            loudspeaker_raw = raw
            for s in cd.get('states', []):
                if s.get('state') == 'clickDown':
                    audio = s.get('source', {}).get('MAudio', {})
                    if isinstance(audio, dict):
                        audio_url = audio.get('value') or audio.get('key')
                    elif isinstance(audio, str):
                        audio_url = audio

    return slots, items, audio_url, loudspeaker_raw


def infer_sentence_parts(slots: list, sentence: str) -> list:
    """
    根据句子文本和 slots 推断 sentence_parts（answer_area 的原始输入）。
    策略：把 sentence 按 slots 内容拆分，不在 slots 里的片段作为 fixed 文本。

    例:
      sentence = "make a snowman"
      slots    = ["m", "ake", "sn", "ow", "man"]
      → 所有内容都是 slots，无固定文本
    如果 sentence 中有不在 slots 中的单词，作为 fixed。
    """
    # 简单策略：把 sentence 拆成 token，每个 token 判断是否匹配 slot
    parts = []
    remaining = sentence.strip()
    slot_idx = 0

    # 逐字符匹配 slots
    i = 0
    while i < len(remaining) and slot_idx < len(slots):
        # 跳过空格 → 作为 space
        if remaining[i] == ' ':
            parts.append({"type": "space", "content": " "})
            i += 1
            continue

        # 尝试匹配下一个 slot
        sl = slots[slot_idx]
        if remaining[i:i+len(sl)].lower() == sl.lower():
            parts.append({"type": "slot", "content": sl})
            slot_idx += 1
            i += len(sl)
        else:
            # 不匹配 slot，收集到下一个空格或 slot 边界作为 fixed 文本
            j = i + 1
            while j < len(remaining) and remaining[j] != ' ':
                # 检查是否到 slot 起点
                if slot_idx < len(slots) and remaining[j:j+len(slots[slot_idx])].lower() == slots[slot_idx].lower():
                    break
                j += 1
            parts.append({"type": "fixed", "content": remaining[i:j]})
            i = j

    # 剩余尾部文本（固定）
    if i < len(remaining):
        tail = remaining[i:].strip()
        if tail:
            parts.append({"type": "fixed", "content": tail})

    # 如果完全没有匹配到 slots（sentence 不可用），fallback 全 slot
    if slot_idx == 0 and slots:
        parts = [{"type": "slot", "content": s} for s in slots]

    return parts


def find_template_level(ref_data, n_slots):
    """在参考配置中找与 n_slots 数量相同的关卡模板"""
    for level in ref_data['game']:
        cnt = sum(1 for c in level['components'] if '拖拽放置区' in c['component_data']['name'])
        if cnt == n_slots:
            return level
    return ref_data['game'][0]  # fallback


def build_level_keep_positions(template_level, question: dict, level_idx: int) -> dict:
    """
    用模板原始位置布局，只替换内容（槽位itemList、物品tag/MLabel、文本值）。
    避免动态计算坐标导致的重叠问题。
    slots: 从左到右的音节列表
    items: 选项列表（保持原顺序）
    audio_url: 音频 URL（可空）
    """
    slots    = question.get('slots', [])
    items    = question.get('items', [])
    audio_url = question.get('audio_url', '')
    sentence = question.get('sentence', ' '.join(slots))

    level = copy.deepcopy(template_level)
    level['id'] = new_level_id()

    comps = level['components']

    # 按 x 坐标从左到右排序拖拽放置区
    slot_comps = sorted(
        [c for c in comps if '拖拽放置区' in c['component_data'].get('name', '')],
        key=lambda c: c['component_data']['states'][0].get('transform', {}).get('x', 0)
    )
    # 按 x 坐标排序拖拽物品
    item_comps = sorted(
        [c for c in comps if '拖拽物品' in c['component_data'].get('name', '')],
        key=lambda c: c['component_data']['states'][0].get('transform', {}).get('x', 0)
    )

    # ── 重算槽位 x 坐标：相邻槽位恰好无缝挨着（x = 中心坐标）──
    # 槽宽从第一个模板槽位取
    slot_w = slot_comps[0]['component_data']['states'][0].get('transform', {}).get('w', 280) if slot_comps else 280
    n = len(slot_comps)
    # 中心点：所有槽位 x 的平均值（模板已定义的画布中心）
    cx = sum(c['component_data']['states'][0].get('transform', {}).get('x', 0) for c in slot_comps) / n if n else 0
    for i, sc in enumerate(slot_comps):
        new_x = cx + (i - (n - 1) / 2) * slot_w
        for st in sc['component_data'].get('states', []):
            tf = st.get('transform', {})
            if 'x' in tf:
                tf['x'] = new_x

    # 更新槽位内容
    for i, sc in enumerate(slot_comps):
        sc['component_data']['id'] = uid()
        if i < len(slots):
            tools = sc['component_data'].get('components', {}).get('tools', {})
            if 'LDragPlace' in tools:
                tools['LDragPlace']['itemList'] = [slots[i]]

    # 更新物品内容
    for i, ic in enumerate(item_comps):
        ic['component_data']['id'] = uid()
        if i < len(items):
            tag = items[i]
            tools = ic['component_data'].get('components', {}).get('tools', {})
            if 'MDraggable' in tools:
                tools['MDraggable']['tag'] = tag
            for st in ic['component_data'].get('states', []):
                src = st.get('source', {})
                if 'MLabel' in src and isinstance(src['MLabel'], dict):
                    src['MLabel']['value'] = tag

    # 更新文本组件（文本-xxx 或 文本drop）
    for c in comps:
        cd = c['component_data']
        name = cd.get('name', '')
        if (name.startswith('文本-') and name not in ('文本头', '文本尾')) or name == '文本drop':
            cd['id'] = uid()
            cd['name'] = f'文本-{sentence}'
            for st in cd.get('states', []):
                src = st.get('source', {})
                if 'MLabel' in src and isinstance(src['MLabel'], dict):
                    src['MLabel']['value'] = sentence

    # 更新音频
    for c in comps:
        cd = c['component_data']
        if cd.get('name') == '喇叭' or '喇叭' in cd.get('name', ''):
            cd['id'] = uid()
            for st in cd.get('states', []):
                src = st.get('source', {})
                if 'MAudio' in src and isinstance(src['MAudio'], dict):
                    src['MAudio']['value'] = audio_url

    # ── 插入 sentence_parts 里的 fixed 文本（如 grown-up 中的 "-"）──
    sentence_parts = question.get('sentence_parts', [])
    fixed_texts = [(i, p['content']) for i, p in enumerate(sentence_parts) if p['type'] == 'fixed']
    if fixed_texts and slot_comps:
        # 从含固定文本组件的参考配置中找 文本a 作为模板
        _tmpl_fixed_text = None
        try:
            with open(MOFAPPL_REF_FIXED) as _f:
                _ref_fixed = json.load(_f)
            for _lvl in _ref_fixed.get('game', []):
                for _c in _lvl.get('components', []):
                    _name = _c['component_data'].get('name', '')
                    if _name.startswith('文本') and _name not in ('文本头', '文本尾') and 'drop' not in _name:
                        # Check MSprite has nineGrid (the purple background style)
                        for _st in _c['component_data'].get('states', []):
                            _sp = _st.get('source', {}).get('MSprite', {})
                            if isinstance(_sp, dict) and _sp.get('nineGrid', {}).get('enable'):
                                _tmpl_fixed_text = _c
                                break
                    if _tmpl_fixed_text:
                        break
                if _tmpl_fixed_text:
                    break
        except Exception:
            pass

        if _tmpl_fixed_text:
            slot_part_indices = [i for i, p in enumerate(sentence_parts) if p['type'] == 'slot']
            for part_idx, text_content in fixed_texts:
                left_slot_order = sum(1 for i in slot_part_indices if i < part_idx)  # 0-based
                left_sc = slot_comps[left_slot_order - 1] if left_slot_order > 0 else None
                right_sc = slot_comps[left_slot_order] if left_slot_order < len(slot_comps) else None
                if left_sc and right_sc:
                    left_x = left_sc['component_data']['states'][0].get('transform', {}).get('x', 0)
                    right_x = right_sc['component_data']['states'][0].get('transform', {}).get('x', 0)
                    fix_x = (left_x + right_x) / 2
                elif right_sc:
                    right_x = right_sc['component_data']['states'][0].get('transform', {}).get('x', 0)
                    fix_x = right_x - slot_w * 0.7
                else:
                    continue
                fix_w = max(50, len(text_content) * 40 + 30)
                fix_comp = copy.deepcopy(_tmpl_fixed_text)
                fix_comp['component_data']['id'] = uid()
                fix_comp['component_data']['name'] = f'固定文本-{text_content}'
                for st in fix_comp['component_data'].get('states', []):
                    tf = st.get('transform', {})
                    if tf:
                        tf['x'] = fix_x
                        tf['w'] = fix_w
                        tf['h'] = SLOT_H
                        tf['y'] = SLOT_Y
                    src = st.get('source', {})
                    if 'MLabel' in src and isinstance(src['MLabel'], dict):
                        src['MLabel']['value'] = text_content
                        src['MLabel']['fontSize'] = 100
                        src['MLabel']['color'] = '#5f5cd7'
                level['components'].append(fix_comp)

    return level


# ─────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────
def generate(output_file=None):
    global OUTPUT_FILE
    if output_file:
        OUTPUT_FILE = output_file

    with open(MOFAPPL_REF_5) as f:
        ref5 = json.load(f)
    with open(MOFAPPL_REF_3) as f:
        ref3 = json.load(f)

    # ── 读取题目来源 ──
    # 优先从单词拼拼乐校验文件提取（兼容旧流程）
    # 也可直接传入 questions 列表（新流程）
    questions = _load_questions_from_spelling_ref(ref3, ref5)

    print("题目数据:")
    for i, q in enumerate(questions):
        print(f"  Q{i+1}: slots={q['slots']} items={q['items']} sentence='{q['sentence']}'")
        print(f"        sentence_parts={q['sentence_parts']}")

    # ── 生成关卡 ──
    output_levels = []
    for i, q in enumerate(questions):
        n = len(q['slots'])
        # 选最接近槽数的模板（只作为骨架）
        if n <= 3:
            tmpl = find_template_level(ref3, n) or find_template_level(ref5, n)
        else:
            tmpl = find_template_level(ref5, n) or find_template_level(ref3, n)
        if tmpl is None:
            tmpl = ref5['game'][0]

        level = build_level(tmpl, q, level_idx=i)
        output_levels.append(level)
        print(f"  关卡{i+1} 生成完毕: {n}槽, {len(q['items'])}物品, "
              f"{sum(1 for p in q['sentence_parts'] if p['type']=='fixed')}固定文本")

    output = {
        'common':     ref5['common'],
        'game':       output_levels,
        'additional': ref5['additional'],
        'components': ref5.get('components', [])
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    size = os.path.getsize(OUTPUT_FILE)
    print(f"\n✅ 生成完毕: {OUTPUT_FILE} ({size} bytes)")

    _run_resource_validation(output, ref5, questions)
    return OUTPUT_FILE


def _load_questions_from_spelling_ref(ref3, ref5):
    """从单词拼拼乐校验文件提取题目（兼容旧流程）"""
    if not os.path.exists(SPELLING_REF):
        print(f"[WARN] 未找到校验文件: {SPELLING_REF}，使用示例数据")
        return _sample_questions()

    with open(SPELLING_REF) as f:
        content = f.read().strip()
    if not content or content in ('null', '{}', '[]'):
        print("[WARN] 校验文件为空，使用示例数据")
        return _sample_questions()

    try:
        spell_data = json.loads(content)
    except Exception:
        print("[WARN] 校验文件解析失败，使用示例数据")
        return _sample_questions()

    spell_levels = spell_data.get('game', [])

    sentences = ['make a snowman', 'clean the room', 'fat']  # 可从外部传入

    questions = []
    for i, spell_level in enumerate(spell_levels):
        slots, items, audio_url, _ = extract_spelling_level_data(spell_level)
        sentence = sentences[i] if i < len(sentences) else ' '.join(slots)
        parts = infer_sentence_parts(slots, sentence)
        questions.append({
            'slots':          slots,
            'items':          items,
            'audio_url':      audio_url or '',
            'sentence':       sentence,
            'sentence_parts': parts,
        })
    return questions


def _sample_questions():
    """示例数据，当无校验文件时使用"""
    return [
        {
            'slots':          ['m', 'ake'],
            'items':          ['ake', 'm'],
            'audio_url':      '',
            'sentence':       'make',
            'sentence_parts': [{'type': 'slot', 'content': 'm'},
                                {'type': 'slot', 'content': 'ake'}],
        }
    ]


# ─────────────────────────────────────────────
# 对外接口：直接传入 questions 列表（新流程）
# ─────────────────────────────────────────────
def generate_from_questions(questions: list, output_file: str = None) -> str:
    """
    直接传入题目数据生成配置。
    questions: list of dict, 每个 dict 包含:
      sentence_parts: [{"type": "fixed"|"slot"|"space", "content": "..."}]
      slots:   ["syllable1", ...]
      items:   ["tag1", ...]
      audio_url: str
      sentence:  str（完整句子，用于 文本-fin）
    """
    global OUTPUT_FILE
    if output_file:
        OUTPUT_FILE = output_file

    with open(MOFAPPL_REF_5) as f:
        ref5 = json.load(f)
    with open(MOFAPPL_REF_3) as f:
        ref3 = json.load(f)

    output_levels = []
    for i, q in enumerate(questions):
        n = len(q['slots'])
        tmpl = (find_template_level(ref3, n) if n <= 3 else find_template_level(ref5, n)) or ref5['game'][0]
        level = build_level(tmpl, q, level_idx=i)
        output_levels.append(level)

    output = {
        'common':     ref5['common'],
        'game':       output_levels,
        'additional': ref5['additional'],
        'components': ref5.get('components', [])
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = OUTPUT_FILE
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✅ 生成完毕: {out_path} ({os.path.getsize(out_path)} bytes)")

    _run_resource_validation(output, ref5, questions)
    return out_path


def load_questions(path: str) -> list:
    """Load dynamic question data. Template skeleton/skin still comes from fixed refs."""
    with open(path, encoding='utf-8') as f:
        payload = json.load(f)
    questions = payload.get('questions', payload.get('levels')) if isinstance(payload, dict) else payload
    if not isinstance(questions, list) or not questions:
        raise ValueError('input must be a non-empty list or an object with questions/levels')
    validate_questions(questions)
    return questions


def validate_questions(questions: list) -> None:
    for index, q in enumerate(questions, 1):
        prefix = f'L{index}'
        for key in ('slots', 'items', 'sentence', 'sentence_parts'):
            if key not in q:
                raise ValueError(f'{prefix}: missing required field: {key}')
        slots = q.get('slots') or []
        items = q.get('items') or []
        parts = q.get('sentence_parts') or []
        if not slots:
            raise ValueError(f'{prefix}: slots cannot be empty')
        if not items:
            raise ValueError(f'{prefix}: items cannot be empty')
        if sorted(map(str, slots)) != sorted(map(str, [p.get('content') for p in parts if p.get('type') == 'slot'])):
            raise ValueError(f'{prefix}: slots must match slot entries in sentence_parts')
        missing_items = sorted(set(map(str, slots)) - set(map(str, items)))
        if missing_items:
            raise ValueError(f'{prefix}: slot answers missing from items: {missing_items}')
        for part in parts:
            part_type = part.get('type')
            if part_type not in {'fixed', 'slot', 'space'}:
                raise ValueError(f'{prefix}: unsupported sentence_parts type: {part_type}')
            if part_type in {'fixed', 'slot'} and not str(part.get('content', '')).strip():
                raise ValueError(f'{prefix}: {part_type} content cannot be empty')
        if not q.get('audio_url'):
            raise ValueError(f'{prefix}: audio_url is required for dynamic input')


def write_meta(path: str, questions: list, output_path: str) -> None:
    if not path:
        return
    meta = {
        'schema': 'coursewaremaker.magic_spelling.build_meta.v1',
        'generator': 'scripts/generate_mofappl_config.py',
        'output': output_path,
        'question_count': len(questions),
        'levels': [
            {
                'index': i,
                'sentence': q.get('sentence'),
                'slot_count': len(q.get('slots', [])),
                'item_count': len(q.get('items', [])),
                'audio_url': q.get('audio_url', ''),
                'fixed_parts': [p.get('content', '') for p in q.get('sentence_parts', []) if p.get('type') == 'fixed'],
            }
            for i, q in enumerate(questions, 1)
        ],
    }
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def _run_resource_validation(generated_cfg, ref_cfg, questions):
    """
    生成后自动调用资源校验。
    白名单：题目配图（用户上传）、喇叭音频（题目音频）— 这两类每次都会换，不需要跟参考对上。
    """
    try:
        from validate_resources import validate, print_report
    except ImportError:
        import importlib.util, pathlib
        spec = importlib.util.spec_from_file_location(
            'validate_resources',
            pathlib.Path(__file__).parent / 'validate_resources.py'
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        validate = mod.validate
        print_report = mod.print_report

    # 收集白名单：题目配图 & 题目音频
    whitelist = set()
    for q in questions:
        if q.get('image'):
            whitelist.add(q['image'])
        if q.get('audio'):
            whitelist.add(q['audio'])
        if q.get('image_url'):
            whitelist.add(q['image_url'])
        if q.get('audio_url'):
            whitelist.add(q['audio_url'])

    print("\n🔍 开始资源校验...")
    result = validate(generated_cfg, ref_cfg, whitelist_urls=whitelist)
    print_report(result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='魔法拼拼乐配置生成脚本')
    parser.add_argument('legacy_output', nargs='?', help='兼容旧用法：仅传输出路径')
    parser.add_argument('--input', help='动态题目 JSON。题目相关字段必须从这里读取')
    parser.add_argument('--output', help='输出配置 JSON')
    parser.add_argument('--meta', help='输出 build meta JSON')
    args = parser.parse_args()

    output = args.output or args.legacy_output
    if args.input:
        qs = load_questions(args.input)
        out_path = generate_from_questions(qs, output)
        write_meta(args.meta, qs, out_path)
    else:
        generate(output)
