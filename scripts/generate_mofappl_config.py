#!/usr/bin/env python3
"""
generate_mofappl_config.py
从单词拼拼乐校验文件提取题目数据，生成魔法拼拼乐配置
用法: python3 generate_mofappl_config.py [输出路径]
"""

import json
import copy
import uuid
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# === 输入文件 ===
SPELLING_REF = os.path.join(BASE, 'reference_configs', 'spelling_validation_ref.json')
MOFAPPL_REF_5SLOT = os.path.join(BASE, 'output', 'mofappl_configs', '77cb396a-babd-11f0-885a-ba4dce53cceb.json')
MOFAPPL_REF_3SLOT = os.path.join(BASE, 'output', 'mofappl_configs', 'c3f13451-dfc0-11f0-9165-0e324dbd00ee.json')

# === 输出路径 ===
OUTPUT_DIR = os.path.join(BASE, 'output', 'mofappl_configs')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'mofappl_test.json')

def new_uuid():
    return f"gamenext_component_uuid_{uuid.uuid4()}"

def new_level_id():
    return str(uuid.uuid4())

def get_default_source(cd):
    for s in cd.get('states', []):
        if s.get('state') == 'default':
            return s.get('source', {})
    return {}


def extract_spelling_level_data(spell_level):
    """从单词拼拼乐关卡提取: slots, items, audio_url, loudspeaker_comp, sentence"""
    comps_raw = spell_level['components']
    comps = [c['component_data'] for c in comps_raw]

    slots = []  # correct syllables in order
    items = []  # drag item tags
    audio_url = None
    loudspeaker_raw = None  # 原始喇叭component wrapper
    sentence = ''  # e.g. 'make a snowman'

    # 先找文本-fin或title来提取sentence
    # 实际从slots拼接，后面再整理
    for raw, cd in zip(comps_raw, comps):
        name = cd['name']
        base = cd['base']
        tools = cd['components'].get('tools', {})

        # 跳过 英语空格 和 文本(固定，不是文本-fin也不是文本头/尾)
        if '英语空格' in name:
            continue

        if 'LDragPlace' in tools:
            ldp = tools['LDragPlace']
            slots.append(ldp.get('itemList', [''])[0])

        if 'MDraggbale' in tools or 'MDraggable' in tools:
            tag = name.replace('拖拽物品-', '')
            items.append(tag)

        # 喇叭 audio
        if '喇叭' in name and base == 'MSpine':
            loudspeaker_raw = raw
            for s in cd.get('states', []):
                if s.get('state') == 'clickDown':
                    audio = s.get('source', {}).get('MAudio', {})
                    if isinstance(audio, dict):
                        audio_url = audio.get('value') or audio.get('key')
                    elif isinstance(audio, str):
                        audio_url = audio

    return slots, items, audio_url, loudspeaker_raw


def find_level_with_n_slots(game_data, n):
    """在游戏列表中找第一个有n个slot的关卡"""
    for level in game_data:
        comps = level['components']
        slots = [c for c in comps if '拖拽放置区' in c['component_data']['name']]
        if len(slots) == n:
            return level
    return None


def build_mofappl_level(template_level, slots, items, audio_url, level_idx, loudspeaker_raw=None, sentence=''):
    """
    基于模板关卡，替换slot/item数据，返回新关卡数据
    slots: ['m', 'ake', 'sn', 'ow', 'man']
    items: ['sn', 'ake', 'm', 'ow', 'man']
    audio_url: 喇叭 clickDown 音频URL
    """
    level = copy.deepcopy(template_level)
    # 新id
    level['id'] = new_level_id()

    # 收集需要改的组件
    slot_comps = []
    item_comps = []
    loudspeaker_comp = None
    wen_ben_comp = None  # 文本-xxx

    for c in level['components']:
        cd = c['component_data']
        name = cd['name']
        tools = cd['components'].get('tools', {})

        if '拖拽放置区' in name:
            slot_comps.append(c)
        elif '拖拽物品' in name:
            item_comps.append(c)
        elif '喇叭' in name:
            loudspeaker_comp = c
        elif name.startswith('文本-') and name not in ['文本头', '文本尾']:
            wen_ben_comp = c

    # 按zIndex或原始顺序排序slot（从左到右）
    slot_comps.sort(key=lambda c: c['component_data']['zIndex'])

    # --- 更新 slots ---
    # 魔法拼拼乐 slot数目可能与模板不符，需要裁剪或扩展
    # 这里假设模板slot数 == len(slots)，若不符则只处理min
    n_slots = min(len(slot_comps), len(slots))
    for i, (sc, slot_val) in enumerate(zip(slot_comps, slots)):
        cd = sc['component_data']
        tools = cd['components'].get('tools', {})
        if 'LDragPlace' in tools:
            tools['LDragPlace']['itemList'] = [slot_val]
        # 重命名
        cd['name'] = f'拖拽放置区{i+1}'
        cd['id'] = new_uuid()

    # 若slot_comps多余，移除多出的
    if len(slot_comps) > len(slots):
        to_remove = set(id(c) for c in slot_comps[len(slots):])
        level['components'] = [c for c in level['components'] if id(c) not in to_remove]

    # --- 更新 items ---
    n_items = min(len(item_comps), len(items))
    for i, (ic, item_val) in enumerate(zip(item_comps, items)):
        cd = ic['component_data']
        cd['name'] = f'拖拽物品{i+1}'
        cd['id'] = new_uuid()
        # tag 通常为空，直接更新 MDraggable.tag (如果有)
        tools = cd['components'].get('tools', {})
        if 'MDraggable' in tools:
            tools['MDraggable']['tag'] = item_val

    # 若item_comps多余，移除
    if len(item_comps) > len(items):
        to_remove = set(id(c) for c in item_comps[len(items):])
        level['components'] = [c for c in level['components'] if id(c) not in to_remove]

    # --- 更新 喇叭 audio ---
    if loudspeaker_comp and audio_url:
        cd = loudspeaker_comp['component_data']
        for s in cd.get('states', []):
            if s.get('state') == 'clickDown':
                if 'MAudio' not in s['source']:
                    s['source']['MAudio'] = {}
                if isinstance(s['source']['MAudio'], dict):
                    s['source']['MAudio']['value'] = audio_url
                    s['source']['MAudio']['key'] = ''

    # --- 更新 文本-xxx ---
    # 名称改为文本-make a snowman 等，图片保持模板中的URL（占位图）
    if wen_ben_comp:
        cd = wen_ben_comp['component_data']
        display = sentence if sentence else ' '.join(slots)
        cd['name'] = f'文本-{display}'

    # --- 补充 喇叭（若模板中没有，从拼拼乐校验文件复制）---
    if loudspeaker_raw:
        has_loudspeaker = any('喇叭' in c['component_data']['name'] for c in level['components'])
        if not has_loudspeaker:
            ls_copy = copy.deepcopy(loudspeaker_raw)
            ls_copy['component_data']['id'] = new_uuid()
            # 更新audio URL
            if audio_url:
                for s in ls_copy['component_data'].get('states', []):
                    if s.get('state') == 'clickDown':
                        if 'MAudio' not in s['source']:
                            s['source']['MAudio'] = {}
                        if isinstance(s['source']['MAudio'], dict):
                            s['source']['MAudio']['value'] = audio_url
            level['components'].append(ls_copy)

    return level


def generate():
    # 加载数据
    with open(SPELLING_REF) as f:
        spell_data = json.load(f)
    with open(MOFAPPL_REF_5SLOT) as f:
        ref5 = json.load(f)
    with open(MOFAPPL_REF_3SLOT) as f:
        ref3 = json.load(f)

    spell_levels = spell_data['game']  # 3个关卡

    # 题目句子（手动对应，后续可从配置/表格中读）
    sentences = ['make a snowman', 'clean the room', 'fat']

    # 提取题目数据
    questions = []
    for i, spell_level in enumerate(spell_levels):
        slots, items, audio_url, loudspeaker_raw = extract_spelling_level_data(spell_level)
        questions.append({
            'slots': slots,
            'items': items,
            'audio_url': audio_url,
            'loudspeaker_raw': loudspeaker_raw,
            'sentence': sentences[i] if i < len(sentences) else ' '.join(slots)
        })

    print("提取的题目数据:")
    for i, q in enumerate(questions):
        print(f"  Q{i+1}: slots={q['slots']}, items={q['items']}, audio={q['audio_url']}")

    # 为每道题选模板
    output_levels = []
    for i, q in enumerate(questions):
        n = len(q['slots'])
        if n <= 3:
            template_level = find_level_with_n_slots(ref3['game'], 3)
            if not template_level:
                template_level = find_level_with_n_slots(ref5['game'], n) or ref5['game'][0]
        elif n <= 5:
            template_level = find_level_with_n_slots(ref5['game'], n)
            if not template_level:
                template_level = ref5['game'][0]
        else:
            # 6+slot: 用ref5最接近的
            template_level = ref5['game'][0]

        level = build_mofappl_level(
            template_level,
            q['slots'],
            q['items'],
            q['audio_url'],
            level_idx=i,
            loudspeaker_raw=q.get('loudspeaker_raw'),
            sentence=q.get('sentence', '')
        )
        output_levels.append(level)
        print(f"  关卡{i+1} 生成完毕: {len(q['slots'])}槽, {len(q['items'])}物品")

    # 用5-slot ref的common/additional/components作基础
    output = {
        'common': ref5['common'],
        'game': output_levels,
        'additional': ref5['additional'],
        'components': ref5.get('components', [])
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    size = os.path.getsize(OUTPUT_FILE)
    print(f"\n✅ 生成完毕: {OUTPUT_FILE} ({size} bytes)")
    return OUTPUT_FILE


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else None
    if out:
        OUTPUT_FILE = out
    generate()
