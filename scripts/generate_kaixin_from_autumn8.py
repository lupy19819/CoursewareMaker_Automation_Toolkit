#!/usr/bin/env python3
"""
以国际starter开心游乐园秋8为模板，生成国际level2开心游乐园暑2
关键：
- tag = 数字 '1','2','3','4'
- 放置区 answer = ['N']（匹配数字tag）
- 选项宽度统一 w=300
- 空tag选项用于展示固定文字（如"I like to"）
"""
import json, copy
from pathlib import Path

BASE = Path(__file__).parent.parent
REFS = BASE / 'reference_configs'
OUTPUT = BASE / 'output'

def get_label(c):
    for s in c.get('component_data',{}).get('states',[]):
        if s.get('label')=='默认': return s.get('source',{}).get('MLabel',{}).get('value','')
    return ''

def set_label(c, text):
    for s in c.get('component_data',{}).get('states',[]):
        if s.get('label')=='默认': s.setdefault('source',{}).setdefault('MLabel',{})['value'] = text
    return c

def get_sprite(c):
    for s in c.get('component_data',{}).get('states',[]):
        if s.get('label')=='默认': return s.get('source',{}).get('MSprite',{}).get('value','')
    return ''

def set_sprite(c, url):
    for s in c.get('component_data',{}).get('states',[]):
        if s.get('label')=='默认': s.setdefault('source',{}).setdefault('MSprite',{})['value'] = url
    return c

def set_transform(c, **kw):
    for s in c.get('component_data',{}).get('states',[]):
        if s.get('label')=='默认': s.setdefault('transform',{}).update(kw)
    return c

def get_tag(c):
    return c.get('component_data',{}).get('components',{}).get('tools',{}).get('MDraggable',{}).get('tag','')

def set_tag(c, tag):
    c.get('component_data',{}).get('components',{}).get('tools',{}).setdefault('MDraggable',{})['tag'] = tag
    return c

def set_dp_answer(c, answer):
    c.get('component_data',{}).get('components',{}).get('tools',{}).setdefault('LDragPlace',{})['itemList'] = [answer]
    return c

# =====================
# 暑2 题目数据
# =====================
# 句型：I like to [verb] noun.
# opts: 4个选项文字，correct_idx: 正确答案在opts中的0-index位置（→ tag = str(correct_idx+1)）

IMG = {
    'cs': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-11/7988efe4001137fd07255b5af7bd7ced.png',
    'wf': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-11/146294ee56e742c24a723a6cf7454b79.png',
    'si': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-11/c5d1adc336ff70a3ecedb8a328f9ca4c.png',
    'dc': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-11/207cafb41489a4b36ce6fa678bd56756.png',
}

# 按文档「国际level2开心游乐园暑2」严格对应，每题3个选项
questions = [
    # 关1: I like to [collect] stickers.  选项: collect, draw, watch
    {'img': IMG['cs'], 'noun': 'stickers.', 'opts': ['collect', 'draw',    'watch'],  'correct_idx': 0},
    # 关2: I like to [watch] films.        选项: stay, watch, collect
    {'img': IMG['wf'], 'noun': 'films.',    'opts': ['stay',    'watch',   'collect'], 'correct_idx': 1},
    # 关3: I like to [stay] inside.        选项: stay, collect, watch
    {'img': IMG['si'], 'noun': 'inside.',   'opts': ['stay',    'collect', 'watch'],   'correct_idx': 0},
    # 关4: I like to [draw] cartoons.      选项: watch, collect, draw
    {'img': IMG['dc'], 'noun': 'cartoons.', 'opts': ['watch',   'collect', 'draw'],    'correct_idx': 2},
]

def generate():
    with open(REFS / 'kaixin_autumn8_starter_ref.json') as f:
        ref = json.load(f)
    
    # 分析秋8关1的结构（作为模板）
    ref_lv1 = ref['game'][0]
    
    print('=== 秋8关1组件 (x排序) ===')
    for c in sorted(ref_lv1['components'], key=lambda c: [s.get('transform',{}).get('x',0) for s in c.get('component_data',{}).get('states',[]) if s.get('label')=='默认'][0] if c.get('component_data',{}).get('states') else 0):
        name = c.get('component_data',{}).get('name','')
        cname = c.get('component_name','')
        x = [s.get('transform',{}).get('x',0) for s in c.get('component_data',{}).get('states',[]) if s.get('label')=='默认']
        x = x[0] if x else 0
        if cname == '拖拽放置区':
            ans = c.get('component_data',{}).get('components',{}).get('tools',{}).get('LDragPlace',{}).get('itemList')
            print(f'  [{x:>6.0f}] DP  answer={ans}')
        elif cname == '拖拽物品':
            tag = get_tag(c)
            print(f'  [{x:>6.0f}] drag tag={tag!r} text={get_label(c)!r}')
        elif get_label(c) and name not in ['背景','小鹿动效','小鹿动效结算正确','物理遮盖']:
            print(f'  [{x:>6.0f}] node name={name} text={get_label(c)!r}')
    
    new_levels = []
    for q in questions:
        # 以关1为模板（所有题都是1放置区）
        lv = copy.deepcopy(ref_lv1)
        
        # 1. 更新配图（name='节点' cname='节点' 的那个场景图组件）
        for c in lv['components']:
            name = c.get('component_data',{}).get('name','')
            cname = c.get('component_name','')
            if name == '节点' and cname == '节点':
                set_sprite(c, q['img'])
                break
        
        # 2. 找到已知条件节点（句号/名词短语）
        for c in lv['components']:
            name = c.get('component_data',{}).get('name','')
            if '已知条件左5' in name or '已知条件左4' in name:
                set_label(c, q['noun'])
                # 根据文字长度设置宽度
                w = max(50, len(q['noun']) * 44 + 40)
                set_transform(c, w=w)
                break
        
        # 3. 更新拖拽物品（有数字tag的）
        tagged_drags = [c for c in lv['components'] 
                        if c.get('component_name')=='拖拽物品' and get_tag(c) in ['1','2','3','4']]
        
        # 按现有tag排序（1→2→3→4）
        tagged_drags.sort(key=lambda c: get_tag(c))
        
        n_opts = len(q['opts'])
        for i, drag in enumerate(tagged_drags[:4]):
            if i < n_opts:
                opt_text = q['opts'][i]
                set_label(drag, opt_text)
                set_transform(drag, w=300)
                # 确保 tag 正确（1-based）
                set_tag(drag, str(i + 1))
            else:
                # 多余的拖拽物品：隐藏（移出画布）
                set_label(drag, '')
                set_tag(drag, '')
                set_transform(drag, x=3000, y=3000)
        
        # 4. 更新空tag的展示选项（把"She's"改为相应文字）
        empty_drags = [c for c in lv['components']
                       if c.get('component_name')=='拖拽物品' and get_tag(c) == '']
        
        # 找主要的展示文字（位置靠近放置区的那个）
        def x_of(c):
            for s in c.get('component_data',{}).get('states',[]):
                if s.get('label')=='默认': return s.get('transform',{}).get('x',0)
            return 0
        
        # 按x坐标找最靠近中心的空tag选项（用于显示"I like to"）
        near_center = sorted(empty_drags, key=lambda c: abs(x_of(c)))
        if near_center:
            # 最近放置区的空选项设为"I like to"
            set_label(near_center[0], 'I like to')
            set_transform(near_center[0], w=340)
            # 其他空选项清空
            for c in near_center[1:]:
                set_label(c, '')
        
        # 5. 更新放置区答案
        dp = next(c for c in lv['components'] if c.get('component_name')=='拖拽放置区')
        correct_tag = str(q['correct_idx'] + 1)
        set_dp_answer(dp, correct_tag)
        
        new_levels.append(lv)
    
    result = copy.deepcopy(ref)
    result['game'] = new_levels
    return result


if __name__ == '__main__':
    cfg = generate()
    out = OUTPUT / 'kaixin_shu2_from_autumn8.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print(f'\n✅ {out}')
    
    print('\n=== 验证 ===')
    for i, lv in enumerate(cfg['game']):
        dp = next(c for c in lv['components'] if c.get('component_name')=='拖拽放置区')
        ans = dp.get('component_data',{}).get('components',{}).get('tools',{}).get('LDragPlace',{}).get('itemList')
        drags = [c for c in lv['components'] if c.get('component_name')=='拖拽物品']
        tagged = [(get_tag(c), get_label(c)) for c in drags if get_tag(c)]
        display = [(get_tag(c), get_label(c)) for c in drags if not get_tag(c) and get_label(c)]
        nodes = [(c.get('component_data',{}).get('name',''), get_label(c)) for c in lv['components']
                 if c.get('component_name')=='节点' and get_label(c) and '已知条件' in c.get('component_data',{}).get('name','')]
        print(f'  关{i+1}: answer={ans} | 选项={tagged} | 展示={display} | 固定={nodes}')
