#!/usr/bin/env python3
"""
最终版：正确生成开心游乐园暑2 和 过桥大冒险暑2
关键修复：
1. 不改变 UUID（保持错误动画连接）
2. 开心游乐园 tag = 实际文字
3. 过桥大冒险 tag = "选项N"
4. 通过 x 坐标控制组件位置顺序
5. 文字宽度参考原始配置
"""
import json, copy, uuid
from pathlib import Path

BASE = Path(__file__).parent.parent
REFS = BASE / 'reference_configs'
OUTPUT = BASE / 'output'

def get_transform(comp):
    for s in comp.get('component_data',{}).get('states',[]):
        if s.get('label')=='默认': return s.get('transform',{})
    return {}

def set_transform(comp, **kw):
    for s in comp.get('component_data',{}).get('states',[]):
        if s.get('label')=='默认': s.setdefault('transform',{}).update(kw)
    return comp

def set_label(comp, text):
    for s in comp.get('component_data',{}).get('states',[]):
        if s.get('label')=='默认':
            s.setdefault('source',{}).setdefault('MLabel',{})['value'] = text
    return comp

def get_label(comp):
    for s in comp.get('component_data',{}).get('states',[]):
        if s.get('label')=='默认':
            return s.get('source',{}).get('MLabel',{}).get('value','')
    return ''

def set_sprite(comp, url):
    for s in comp.get('component_data',{}).get('states',[]):
        if s.get('label')=='默认':
            s.setdefault('source',{}).setdefault('MSprite',{})['value'] = url
    return comp

def get_sprite(comp):
    for s in comp.get('component_data',{}).get('states',[]):
        if s.get('label')=='默认':
            return s.get('source',{}).get('MSprite',{}).get('value','')
    return ''

def set_dp_answer(comp, answer):
    tools = comp.get('component_data',{}).get('components',{}).get('tools',{})
    if 'LDragPlace' in tools:
        tools['LDragPlace']['itemList'] = [answer]
    return comp

def set_drag_tag(comp, tag, label_text, width=286):
    tools = comp.get('component_data',{}).get('components',{}).get('tools',{})
    if 'MDraggable' in tools:
        tools['MDraggable']['tag'] = tag
    set_label(comp, label_text)
    set_transform(comp, w=width)
    return comp

def text_width(text, char_w=46, pad=60, min_w=200):
    return max(min_w, len(text) * char_w + pad)


# ===========================
# 开心游乐园暑2
# ===========================

def gen_kaixin():
    with open(REFS / 'kaixin_spring7_ref.json') as f:
        ref = json.load(f)
    
    IMG = {
        'cs': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/2be4d09ca98a19781887ae1a5b941601.png',
        'wf': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/70b77f4aff563449eeff3ba5062482b4.png',
        'si': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/c3ff13da466a922921d5a00c2eb45d9f.png',
        'dc': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/b489b31b65e2cce7b7f735985fd4a59d.png',
    }
    
    questions = [
        # 句子：[collect] stickers .  tag=实际文字（如春7格式）
        {'img': IMG['cs'], 'answer': 'collect', 'fixed': 'stickers', 'opts': ['collect', 'draw',    'watch']},
        {'img': IMG['wf'], 'answer': 'watch',   'fixed': 'films',    'opts': ['stay',    'watch',   'collect']},
        {'img': IMG['si'], 'answer': 'stay',    'fixed': 'inside',   'opts': ['stay',    'collect', 'watch']},
        {'img': IMG['dc'], 'answer': 'draw',    'fixed': 'cartoons', 'opts': ['watch',   'collect', 'draw']},
    ]
    
    # 关4：2放置区+3选项（2放置区1个用作固定文本位置）
    ref_lv = ref['game'][3]
    
    new_levels = []
    for q in questions:
        lv = copy.deepcopy(ref_lv)
        
        # 找组件
        dps = [c for c in lv['components'] if c.get('component_name')=='拖拽放置区']
        drags = [c for c in lv['components'] if c.get('component_name')=='拖拽物品']
        
        # 找配图节点（"节点"且有图片但不是背景的）
        for c in lv['components']:
            name = c.get('component_data',{}).get('name','')
            if name == '节点' and get_sprite(c):
                sprite = get_sprite(c)
                if 'V0056779' in sprite or 'assets/image' in sprite:
                    set_sprite(c, q['img'])
        
        # 找固定文本节点
        text_right = None  # 拖放区右侧（已知条件左2，无后缀）
        text_before = None  # 拖放区左侧（已知条件左2_xxx）
        text_dot = None  # 句号（已知条件左4）
        for c in lv['components']:
            name = c.get('component_data',{}).get('name','')
            if '已知条件左4' in name:
                text_dot = c
            elif '已知条件左2' in name and '_' not in name.split('左2')[1] if '左2' in name else False:
                text_right = c
            elif '已知条件左2_' in name:
                text_before = c
        
        # 更新固定文本
        if text_right:
            fw = text_width(q['fixed'])
            set_label(text_right, q['fixed'])
            set_transform(text_right, w=fw)
        if text_before:
            set_label(text_before, '')  # 暑2没有前置文本
        if text_dot:
            set_label(text_dot, '.')
        
        # 删除第二个放置区及其错误配合节点（保留UUID关系）
        to_remove_cids = set()
        if len(dps) >= 2:
            dp2_id = dps[1].get('component_data',{}).get('id','')
            to_remove_cids.add(dp2_id)
        
        # 找与第二放置区关联的错误配合节点
        filtered = []
        for c in lv['components']:
            cid = c.get('component_data',{}).get('id','')
            if cid in to_remove_cids:
                continue
            name = c.get('component_data',{}).get('name','')
            if '错误配合' in name:
                sources = {ev.get('source','') for ev in c.get('component_data',{}).get('event',{}).get('value',[])}
                if sources & to_remove_cids:
                    continue  # 删除与第2放置区关联的错误配合
            filtered.append(c)
        lv['components'] = filtered
        
        # 更新第一个放置区答案（保留UUID）
        first_dp = next(c for c in lv['components'] if c.get('component_name')=='拖拽放置区')
        set_dp_answer(first_dp, q['answer'])
        
        # 更新3个选项（保留UUID，只改tag和文字）
        drags = [c for c in lv['components'] if c.get('component_name')=='拖拽物品']
        for i, drag in enumerate(drags[:3]):
            opt_text = q['opts'][i]
            set_drag_tag(drag, opt_text, opt_text, text_width(opt_text, 44, 60, 200))
        
        new_levels.append(lv)
    
    result = copy.deepcopy(ref)
    result['game'] = new_levels
    return result


# ===========================
# 过桥大冒险暑2
# ===========================

def gen_guoqiao():
    with open(REFS / 'guoqiao_autumn14_ref.json') as f:
        ref = json.load(f)
    
    IMG = {
        'rb': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/1ddde668f36606fa4ea280bb2121058e.png',
        'po': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/32920ae7b7919ece73dc0b47f5640990.png',
        'wf': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/5e009a2fb621003122587940e9e2b5d4.png',
        'si': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/8a0debb509dab581883ee51fb9cadf72.png',
        'cs': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/62fd937dde1a2a2dbabec8a8958a3aba.png',
        'si2': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/63de93d3f11271b1152fa1e1ae4c18e9.png',
    }
    
    # 暑2 6题 - tag格式 = "选项N"
    # answer_idx: 正确答案在 opts 中的0-indexed位置
    questions = [
        # 关1: Kuan [enjoys] riding bikes .  1放置区，2选项
        # opts: enjoy, enjoys  answer: enjoys(idx=1) → 选项2
        {
            'img': IMG['rb'], 'ref_idx': 0,  # 参考关1（2放置区）→ 删掉1个
            'dp_count': 1,
            'dp_answers': ['选项2'],
            'opts': ['enjoy', 'enjoys'],
            'bridge_layout': [
                {'text': 'Kuan',          'x': -540, 'w': 286},
                {'text': 'riding bikes.', 'x': 200,  'w': 450},
            ],
        },
        # 关2: We [like] playing outside .  1放置区，2选项
        # opts: likes, like  answer: like(idx=1) → 选项2
        {
            'img': IMG['po'], 'ref_idx': 0,
            'dp_count': 1,
            'dp_answers': ['选项2'],
            'opts': ['likes', 'like'],
            'bridge_layout': [
                {'text': 'We',              'x': -540, 'w': 180},
                {'text': 'playing outside.','x': 200,  'w': 560},
            ],
        },
        # 关3: He [loves] [drawing] films .  2放置区，4选项
        # opts: loves, love, draw, drawing  answers: loves(idx=0)→选项1, drawing(idx=3)→选项4
        {
            'img': IMG['wf'], 'ref_idx': 0,
            'dp_count': 2,
            'dp_answers': ['选项1', '选项4'],
            'opts': ['loves', 'love', 'draw', 'drawing'],
            'bridge_layout': [
                {'text': 'He',     'x': -540, 'w': 180},
                {'text': 'films.', 'x': 560,  'w': 320},
            ],
        },
        # 关4: They [don't enjoy] [staying] inside .  2放置区，4选项
        # opts: doesn't enjoy, don't enjoy, stay, staying  answers: don't enjoy(idx=1)→选项2, staying(idx=3)→选项4
        {
            'img': IMG['si'], 'ref_idx': 0,
            'dp_count': 2,
            'dp_answers': ['选项2', '选项4'],
            'opts': ["doesn't enjoy", "don't enjoy", 'stay', 'staying'],
            'bridge_layout': [
                {'text': 'They',    'x': -540, 'w': 200},
                {'text': 'inside.', 'x': 560,  'w': 340},
            ],
        },
        # 关5: [Max] [likes] [collecting stickers] .  3放置区，4选项（乱序）
        # opts: likes, Max, collecting stickers, like  answers: Max(idx=1)→选项2, likes(idx=0)→选项1, collecting stickers(idx=2)→选项3
        {
            'img': IMG['cs'], 'ref_idx': 2,  # 参考关3（3放置区）
            'dp_count': 3,
            'dp_answers': ['选项2', '选项1', '选项3'],
            'opts': ['likes', 'Max', 'collecting stickers', 'like'],
            'bridge_layout': [
                {'text': '.', 'x': 450, 'w': 60},
            ],
        },
        # 关6: [They] [don't] [like] [staying inside] .  3放置区4选项（暂用3放置区，4选项乱序）
        # opts: staying inside, They, don't, like  answers: They(idx=1)→选项2, don't(idx=2)→选项3, like(idx=3)→选项4
        {
            'img': IMG['si2'], 'ref_idx': 2,  # 参考关3（3放置区）
            'dp_count': 3,
            'dp_answers': ["选项2", '选项3', '选项4'],
            'opts': ['staying inside', 'They', "don't", 'like'],
            'bridge_layout': [
                {'text': '.', 'x': 450, 'w': 60},
            ],
        },
    ]
    
    new_levels = []
    
    for q in questions:
        ref_lv = ref['game'][q['ref_idx']]
        lv = copy.deepcopy(ref_lv)
        
        # 1. 更新配图
        for c in lv['components']:
            name = c.get('component_data',{}).get('name','')
            if '配图' in name or name == '题目配图':
                set_sprite(c, q['img'])
        
        # 2. 处理放置区
        dps = [c for c in lv['components'] if c.get('component_name')=='拖拽放置区']
        to_remove = set()
        
        # 按 x 坐标排序放置区（从左到右）
        def x_of(c):
            for s in c.get('component_data',{}).get('states',[]):
                if s.get('label')=='默认': return s.get('transform',{}).get('x',0)
            return 0
        
        dps_sorted = sorted(dps, key=x_of)
        
        for i, dp in enumerate(dps_sorted):
            if i < q['dp_count']:
                set_dp_answer(dp, q['dp_answers'][i])
                dp_w = 534 if q['dp_count'] == 1 else 285
                set_transform(dp, w=dp_w)
            else:
                dp_id = dp.get('component_data',{}).get('id','')
                to_remove.add(dp_id)
        
        # 删除多余放置区和关联砖块掉落
        filtered = []
        prev_removed = False
        for c in lv['components']:
            cid = c.get('component_data',{}).get('id','')
            name = c.get('component_data',{}).get('name','')
            if cid in to_remove:
                prev_removed = True
                continue
            if prev_removed and '砖块掉落' in name:
                prev_removed = False
                continue
            prev_removed = False
            filtered.append(c)
        lv['components'] = filtered
        
        # 3. 处理选项
        drags = [c for c in lv['components'] if c.get('component_name')=='拖拽物品']
        extra_remove = set()
        for i, drag in enumerate(drags):
            if i < len(q['opts']):
                tag = f'选项{i+1}'
                opt_text = q['opts'][i]
                opt_w = text_width(opt_text, 42, 60, 200)
                set_drag_tag(drag, tag, opt_text, opt_w)
            else:
                extra_remove.add(drag.get('component_data',{}).get('id',''))
        lv['components'] = [c for c in lv['components'] if c.get('component_data',{}).get('id','') not in extra_remove]
        
        # 4. 处理桥墩文本
        bridges = [c for c in lv['components'] if c.get('component_name')=='节点' and '桥墩' in c.get('component_data',{}).get('name','')]
        bridge_layout = q['bridge_layout']
        
        # 先删除多余桥墩
        extra_bridge_remove = set()
        for i, b in enumerate(bridges):
            if i >= len(bridge_layout):
                extra_bridge_remove.add(b.get('component_data',{}).get('id',''))
        lv['components'] = [c for c in lv['components'] if c.get('component_data',{}).get('id','') not in extra_bridge_remove]
        
        # 如果需要更多桥墩，克隆最后一个
        bridges = [c for c in lv['components'] if c.get('component_name')=='节点' and '桥墩' in c.get('component_data',{}).get('name','')]
        while len(bridges) < len(bridge_layout):
            new_b = copy.deepcopy(bridges[-1] if bridges else bridges[0])
            new_b['component_data']['id'] = f'gamenext_component_uuid_{uuid.uuid4()}'
            lv['components'].append(new_b)
            bridges.append(new_b)
        
        # 更新桥墩内容和位置
        bridges = [c for c in lv['components'] if c.get('component_name')=='节点' and '桥墩' in c.get('component_data',{}).get('name','')]
        for i, (b, layout) in enumerate(zip(bridges, bridge_layout)):
            set_label(b, layout['text'])
            set_transform(b, x=layout['x'], w=layout['w'])
        
        new_levels.append(lv)
    
    result = copy.deepcopy(ref)
    result['game'] = new_levels
    return result


# ===========================
# 主程序
# ===========================

if __name__ == '__main__':
    print('=== 开心游乐园暑2 (final) ===')
    k = gen_kaixin()
    out_k = OUTPUT / 'kaixin_shu2_final.json'
    with open(out_k, 'w', encoding='utf-8') as f:
        json.dump(k, f, ensure_ascii=False, indent=2)
    print(f'✅ {out_k}')
    
    print('\n=== 过桥大冒险暑2 (final) ===')
    g = gen_guoqiao()
    out_g = OUTPUT / 'guoqiao_shu2_final.json'
    with open(out_g, 'w', encoding='utf-8') as f:
        json.dump(g, f, ensure_ascii=False, indent=2)
    print(f'✅ {out_g}')
    
    print('\n=== 验证 ===')
    print('开心游乐园暑2:')
    for i, lv in enumerate(k['game']):
        dps = [c for c in lv['components'] if c.get('component_name')=='拖拽放置区']
        drags = [c for c in lv['components'] if c.get('component_name')=='拖拽物品']
        errors = [c for c in lv['components'] if '错误配合' in c.get('component_data',{}).get('name','')]
        answers = [c.get('component_data',{}).get('components',{}).get('tools',{}).get('LDragPlace',{}).get('itemList') for c in dps]
        opts = [get_label(c) for c in drags]
        print(f'  关{i+1}: {len(dps)}放置区 answers={answers} | 选项={opts} | {len(errors)}个错误动画')
    
    print('过桥大冒险暑2:')
    for i, lv in enumerate(g['game']):
        dps = [c for c in lv['components'] if c.get('component_name')=='拖拽放置区']
        drags = [c for c in lv['components'] if c.get('component_name')=='拖拽物品']
        bridges = [c for c in lv['components'] if c.get('component_name')=='节点' and '桥墩' in c.get('component_data',{}).get('name','')]
        answers = [c.get('component_data',{}).get('components',{}).get('tools',{}).get('LDragPlace',{}).get('itemList') for c in dps]
        opts = [(c.get('component_data',{}).get('components',{}).get('tools',{}).get('MDraggable',{}).get('tag'), get_label(c)) for c in drags]
        texts = [get_label(c) for c in bridges]
        print(f'  关{i+1}: {len(dps)}放置区 answers={answers} | 选项={opts} | 桥墩={texts}')
