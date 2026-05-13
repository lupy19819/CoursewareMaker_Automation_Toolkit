#!/usr/bin/env python3
"""
正确做法：保持原有 UUID 不变，只更新内容值
关键发现：错误配合节点通过 event.value[].source 引用拖放区UUID，必须保留ID
"""
import json, copy, uuid
from pathlib import Path

BASE = Path(__file__).parent.parent
REFS = BASE / 'reference_configs'
OUTPUT = BASE / 'output'

def new_uuid():
    return f"gamenext_component_uuid_{uuid.uuid4()}"

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
    """设置拖拽放置区答案（保持原tag格式）"""
    tools = comp.get('component_data',{}).get('components',{}).get('tools',{})
    if 'LDragPlace' in tools:
        tools['LDragPlace']['itemList'] = [answer]
    return comp

def set_draggable(comp, tag, label_text, width=300):
    """设置拖拽物品的tag、显示文本和宽度"""
    tools = comp.get('component_data',{}).get('components',{}).get('tools',{})
    if 'MDraggable' in tools:
        tools['MDraggable']['tag'] = tag
    set_label(comp, label_text)
    set_transform(comp, w=width)
    return comp

def calc_text_width(text, char_width=50, padding=40, min_w=200):
    """根据文字长度计算宽度"""
    return max(min_w, len(text) * char_width + padding)

# ==========================
# 开心游乐园暑2 v3
# ==========================

def generate_kaixin_shu2():
    """
    结构：每题 [drag_zone] fixed_text .
    参考：kaixin_spring7_ref.json 的各关卡
    
    关键：不改变任何UUID，只更新值
    """
    with open(REFS / 'kaixin_spring7_ref.json') as f:
        ref = json.load(f)
    
    IMG = {
        'cs': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/2be4d09ca98a19781887ae1a5b941601.png',
        'wf': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/70b77f4aff563449eeff3ba5062482b4.png',
        'si': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/c3ff13da466a922921d5a00c2eb45d9f.png',
        'dc': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/b489b31b65e2cce7b7f735985fd4a59d.png',
    }
    
    # 每题：answer=放置区答案(与选项tag一致), fixed=右侧固定词, options=3个选项
    questions = [
        {'img': IMG['cs'], 'answer': 'collect', 'fixed': 'stickers', 'options': ['collect', 'draw',    'watch']},
        {'img': IMG['wf'], 'answer': 'watch',   'fixed': 'films',    'options': ['stay',    'watch',   'collect']},
        {'img': IMG['si'], 'answer': 'stay',    'fixed': 'inside',   'options': ['stay',    'collect', 'watch']},
        {'img': IMG['dc'], 'answer': 'draw',    'fixed': 'cartoons', 'options': ['watch',   'collect', 'draw']},
    ]
    
    # 用关1作为基础模板（1放置区2选项），暑2需要1放置区3选项
    # 关4有1放置区3选项 - 检查第一个放置区的位置（单放置区的参考）
    # 实际上：任何1放置区的关卡都可以作为模板，加上第3选项
    
    # 找参考级（1放置区）
    # 关1: 1放置区2选项
    # 关2: 1放置区2选项
    # 找有3选项的关卡
    ref_level_3opt = None
    for lv in ref['game']:
        dps = [c for c in lv['components'] if c.get('component_name')=='拖拽放置区']
        drags = [c for c in lv['components'] if c.get('component_name')=='拖拽物品']
        if len(dps) == 1 and len(drags) >= 3:
            ref_level_3opt = lv
            break
    
    # 如果没有单放置区+3选项，使用关4（2放置区3选项），删除一个放置区
    if ref_level_3opt is None:
        # 关4 (index 3) 有 2放置区 3选项
        ref_level_3opt = ref['game'][3]
    
    print(f'使用参考关卡: {sum(1 for c in ref_level_3opt["components"] if c.get("component_name")=="拖拽放置区")}放置区 '
          f'{sum(1 for c in ref_level_3opt["components"] if c.get("component_name")=="拖拽物品")}选项')
    
    # 打印参考关卡组件列表
    print('参考关卡组件:')
    for i, c in enumerate(ref_level_3opt['components']):
        name = c.get('component_data',{}).get('name','')
        cname = c.get('component_name','')
        t = get_transform(c)
        pos = f"({t.get('x',0):.0f},{t.get('y',0):.0f}) w={t.get('w',0):.0f}"
        if cname == '拖拽放置区':
            dp = c.get('component_data',{}).get('components',{}).get('tools',{}).get('LDragPlace',{})
            print(f'  [{i}] {cname} | {name} | {pos} | answer={dp.get("itemList")}')
        elif cname == '拖拽物品':
            drag = c.get('component_data',{}).get('components',{}).get('tools',{}).get('MDraggable',{})
            label = get_label(c)
            print(f'  [{i}] {cname} | {name} | {pos} | tag={drag.get("tag")} label={label}')
        elif get_label(c):
            print(f'  [{i}] {cname} | {name} | {pos} | text={get_label(c)}')
        elif get_sprite(c) and 'V0056779' in get_sprite(c):
            print(f'  [{i}] {cname} | {name} | {pos} | [活动图片]')
        else:
            print(f'  [{i}] {cname} | {name} | {pos}')
    
    new_levels = []
    for q in questions:
        level = copy.deepcopy(ref_level_3opt)
        
        # 找到各类组件
        dps = [c for c in level['components'] if c.get('component_name')=='拖拽放置区']
        drags = [c for c in level['components'] if c.get('component_name')=='拖拽物品']
        
        # 找配图节点（节点且有COS图片的）
        pic_nodes = [c for c in level['components']
                     if c.get('component_name')=='节点'
                     and c.get('component_data',{}).get('name') not in ['背景','小鹿动效','物理遮盖','小鹿动效结算正确']
                     and get_sprite(c)
                     and 'background' not in get_sprite(c)
                     and 'background' not in c.get('component_data',{}).get('name','').lower()
                     and '背景' not in c.get('component_data',{}).get('name','')]
        
        # 找固定文本节点（已知条件左2，不含_的是主要位置）
        text_right = None
        text_before = None
        text_dot = None
        for c in level['components']:
            name = c.get('component_data',{}).get('name','')
            if '已知条件左4' in name:
                text_dot = c
            elif '已知条件左2' in name and '_' not in name:
                text_right = c  # 放置区右侧文本
            elif '已知条件左2_' in name:
                text_before = c  # 放置区左侧文本（暑2不需要）
        
        # 1. 更新配图
        if pic_nodes:
            set_sprite(pic_nodes[0], q['img'])
        
        # 2. 处理放置区 - 只保留第一个，更新答案
        # 注意：答案tag用选项tag（和选项的MDraggable.tag一致）
        # 这里答案tag就是正确选项的显示文字本身（开心游乐园用文字tag）
        to_remove = set()
        for i, dp in enumerate(dps):
            if i == 0:
                set_dp_answer(dp, q['answer'])
            else:
                # 删除多余放置区及其错误配合节点
                dp_id = dp.get('component_data',{}).get('id','')
                to_remove.add(dp_id)
        
        # 删除与多余放置区绑定的错误配合节点
        filtered = []
        for c in level['components']:
            cid = c.get('component_data',{}).get('id','')
            name = c.get('component_data',{}).get('name','')
            if cid in to_remove:
                continue
            # 错误配合节点通过event.source连接放置区
            if '错误配合' in name:
                sources = [ev.get('source','') for ev in c.get('component_data',{}).get('event',{}).get('value',[])]
                if any(s in to_remove for s in sources):
                    continue
            filtered.append(c)
        level['components'] = filtered
        
        # 3. 更新选项
        for i, drag in enumerate(drags[:3]):
            opt_text = q['options'][i]
            set_draggable(drag, opt_text, opt_text, calc_text_width(opt_text, 45, 50, 200))
        
        # 4. 更新固定文本
        if text_right:
            fw = calc_text_width(q['fixed'], 45, 50, 150)
            set_label(text_right, q['fixed'])
            set_transform(text_right, w=fw)
        if text_before:
            # 暑2不需要前置文本
            set_label(text_before, '')
        if text_dot:
            set_label(text_dot, '.')
        
        new_levels.append(level)
    
    result = copy.deepcopy(ref)
    result['game'] = new_levels
    return result


# ==========================
# 过桥大冒险暑2 v3
# ==========================

def generate_guoqiao_shu2():
    """
    结构：每关 text [drag] text [drag] text...
    参考：guoqiao_autumn14_ref.json
    
    关键：不改变任何UUID，只更新值
    """
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
    
    # 暑2 6题
    # drag_count: 放置区数量
    # answers: 正确答案列表（与选项的tag对应）
    # options: 选项显示文字列表
    # fixed_texts: 固定文本列表（桥墩/纯文本，None或空时不显示）
    questions = [
        # 关1: Kuan [enjoys] riding bikes .  1放置区2选项
        {
            'img': IMG['rb'], 'drag_count': 1,
            'answers': ['enjoys'],
            'options': ['enjoy', 'enjoys'],
            'fixed_texts': ['Kuan', 'riding bikes', '.'],
        },
        # 关2: We [like] playing outside .  1放置区2选项
        {
            'img': IMG['po'], 'drag_count': 1,
            'answers': ['like'],
            'options': ['likes', 'like'],
            'fixed_texts': ['We', 'playing outside', '.'],
        },
        # 关3: He [loves] [drawing] films .  2放置区4选项
        {
            'img': IMG['wf'], 'drag_count': 2,
            'answers': ['loves', 'drawing'],
            'options': ['loves', 'love', 'draw', 'drawing'],
            'fixed_texts': ['He', 'films', '.'],
        },
        # 关4: They [don't enjoy] [staying] inside .  2放置区4选项
        {
            'img': IMG['si'], 'drag_count': 2,
            'answers': ["don't enjoy", 'staying'],
            'options': ["doesn't enjoy", "don't enjoy", 'stay', 'staying'],
            'fixed_texts': ['They', 'inside', '.'],
        },
        # 关5: [Max] [likes] [collecting stickers] .  3放置区4选项(乱序)
        {
            'img': IMG['cs'], 'drag_count': 3,
            'answers': ['Max', 'likes', 'collecting stickers'],
            'options': ['likes', 'Max', 'collecting stickers', 'like'],
            'fixed_texts': ['.'],
        },
        # 关6: [They] [don't] [like] [staying inside] .  3放置区4选项(乱序，暂用3放置区模板)
        {
            'img': IMG['si2'], 'drag_count': 3,
            'answers': ['They', "don't", 'like'],  # 先用3个，staying inside单独处理
            'options': ['staying inside', 'They', "don't", 'like'],
            'fixed_texts': ['.'],
        },
    ]
    
    def find_ref_level(drag_count, opt_count):
        """找合适的参考关卡（放置区数>=drag_count，选项数>=opt_count）"""
        best = None
        for lv in ref['game']:
            dps = sum(1 for c in lv['components'] if c.get('component_name')=='拖拽放置区')
            drags = sum(1 for c in lv['components'] if c.get('component_name')=='拖拽物品')
            if dps >= drag_count and drags >= opt_count:
                if best is None or dps <= sum(1 for c in best['components'] if c.get('component_name')=='拖拽放置区'):
                    best = lv
        return best or ref['game'][0]
    
    print('\n过桥大冒险参考选择:')
    for i, q in enumerate(questions):
        ref_lv = find_ref_level(q['drag_count'], len(q['options']))
        dp = sum(1 for c in ref_lv['components'] if c.get('component_name')=='拖拽放置区')
        dr = sum(1 for c in ref_lv['components'] if c.get('component_name')=='拖拽物品')
        # 找关号
        for j, lv in enumerate(ref['game']):
            if lv is ref_lv:
                print(f'  关{i+1}(需{q["drag_count"]}放置区{len(q["options"])}选项) -> 参考关{j+1}({dp}放置区{dr}选项)')
    
    new_levels = []
    for q in questions:
        ref_lv = find_ref_level(q['drag_count'], len(q['options']))
        level = copy.deepcopy(ref_lv)
        
        dps = [c for c in level['components'] if c.get('component_name')=='拖拽放置区']
        drags = [c for c in level['components'] if c.get('component_name')=='拖拽物品']
        bridges = [c for c in level['components'] if c.get('component_name')=='节点'
                   and '桥墩' in c.get('component_data',{}).get('name','')]
        
        # 1. 更新配图
        for c in level['components']:
            name = c.get('component_data',{}).get('name','')
            if '配图' in name or name == '题目配图':
                set_sprite(c, q['img'])
        
        # 2. 处理放置区
        to_remove = set()
        for i, dp in enumerate(dps):
            if i < q['drag_count']:
                # 保留，更新答案
                set_dp_answer(dp, q['answers'][i])
                # 宽度：单放置区=534，多放置区=285
                w = 534 if q['drag_count'] == 1 else 285
                set_transform(dp, w=w)
            else:
                # 删除多余放置区
                dp_id = dp.get('component_data',{}).get('id','')
                to_remove.add(dp_id)
        
        # 删除多余放置区及关联的砖块掉落
        filtered = []
        prev_is_dp_removed = False
        for c in level['components']:
            cid = c.get('component_data',{}).get('id','')
            name = c.get('component_data',{}).get('name','')
            if cid in to_remove:
                prev_is_dp_removed = True
                continue
            if prev_is_dp_removed and '砖块掉落' in name:
                prev_is_dp_removed = False
                continue
            prev_is_dp_removed = False
            filtered.append(c)
        level['components'] = filtered
        
        # 3. 处理选项
        drags = [c for c in level['components'] if c.get('component_name')=='拖拽物品']
        for i, drag in enumerate(drags):
            if i < len(q['options']):
                opt = q['options'][i]
                w = calc_text_width(opt, 40, 50, 200)
                set_draggable(drag, opt, opt, w)
            else:
                to_remove.add(drag.get('component_data',{}).get('id',''))
        level['components'] = [c for c in level['components']
                               if c.get('component_data',{}).get('id','') not in to_remove]
        
        # 4. 处理固定文本（桥墩）
        bridges = [c for c in level['components'] if c.get('component_name')=='节点'
                   and '桥墩' in c.get('component_data',{}).get('name','')]
        for i, c in enumerate(bridges):
            if i < len(q['fixed_texts']):
                text = q['fixed_texts'][i]
                set_label(c, text)
                w = 534 if q['drag_count'] == 1 else calc_text_width(text, 40, 50, 100)
                set_transform(c, w=w)
            else:
                to_remove.add(c.get('component_data',{}).get('id',''))
        level['components'] = [c for c in level['components']
                               if c.get('component_data',{}).get('id','') not in to_remove]
        
        new_levels.append(level)
    
    result = copy.deepcopy(ref)
    result['game'] = new_levels
    return result


if __name__ == '__main__':
    print('=== 生成开心游乐园暑2 v3 ===')
    k = generate_kaixin_shu2()
    out_k = OUTPUT / 'kaixin_shu2_v3.json'
    with open(out_k, 'w', encoding='utf-8') as f:
        json.dump(k, f, ensure_ascii=False, indent=2)
    print(f'✅ {out_k}')
    
    print('\n=== 生成过桥大冒险暑2 v3 ===')
    g = generate_guoqiao_shu2()
    out_g = OUTPUT / 'guoqiao_shu2_v3.json'
    with open(out_g, 'w', encoding='utf-8') as f:
        json.dump(g, f, ensure_ascii=False, indent=2)
    print(f'✅ {out_g}')
    
    # 验证
    print('\n=== 验证 ===')
    print('开心游乐园暑2:')
    for i, lv in enumerate(k['game']):
        dps = [c for c in lv['components'] if c.get('component_name')=='拖拽放置区']
        drags = [c for c in lv['components'] if c.get('component_name')=='拖拽物品']
        answers = [c.get('component_data',{}).get('components',{}).get('tools',{}).get('LDragPlace',{}).get('itemList') for c in dps]
        opts = [get_label(c) for c in drags]
        print(f'  关{i+1}: {len(dps)}放置区 answers={answers} | 选项={opts}')
    
    print('过桥大冒险暑2:')
    for i, lv in enumerate(g['game']):
        dps = [c for c in lv['components'] if c.get('component_name')=='拖拽放置区']
        drags = [c for c in lv['components'] if c.get('component_name')=='拖拽物品']
        bridges = [c for c in lv['components'] if c.get('component_name')=='节点' and '桥墩' in c.get('component_data',{}).get('name','')]
        answers = [c.get('component_data',{}).get('components',{}).get('tools',{}).get('LDragPlace',{}).get('itemList') for c in dps]
        texts = [get_label(c) for c in bridges if get_label(c)]
        opts = [get_label(c) for c in drags]
        print(f'  关{i+1}: {len(dps)}放置区 answers={answers} | 选项={opts} | 固定={texts}')
