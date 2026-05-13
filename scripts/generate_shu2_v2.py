#!/usr/bin/env python3
"""
基于正确参考配置重新生成 开心游乐园暑2 和 过桥大冒险暑2
修复以下问题：
1. 可拖拽物品间隔和长度
2. 答题区空置未连接
3. 过桥大冒险答题区文本框长度
4. 标点符号识别
5. 文本和放置区重叠
6. 砖块错误反馈
"""
import json, copy, uuid, os
from pathlib import Path

BASE = Path(__file__).parent.parent
REFS = BASE / 'reference_configs'
OUTPUT = BASE / 'output'

def new_uuid():
    return f"gamenext_component_uuid_{uuid.uuid4()}"

def get_transform(comp):
    """获取组件的transform"""
    for s in comp.get('component_data', {}).get('states', []):
        if s.get('label') == '默认':
            return s.get('transform', {})
    return {}

def set_transform(comp, **kwargs):
    """设置组件的transform"""
    for s in comp.get('component_data', {}).get('states', []):
        if s.get('label') == '默认':
            transform = s.get('transform', {})
            transform.update(kwargs)
            s['transform'] = transform
    return comp

def set_label(comp, text):
    """设置MLabel文本"""
    for s in comp.get('component_data', {}).get('states', []):
        if s.get('label') == '默认':
            if 'MLabel' not in s.get('source', {}):
                s['source']['MLabel'] = {}
            s['source']['MLabel']['value'] = text
    return comp

def get_label(comp):
    """获取MLabel文本"""
    for s in comp.get('component_data', {}).get('states', []):
        if s.get('label') == '默认':
            return s.get('source', {}).get('MLabel', {}).get('value', '')
    return ''

def set_sprite(comp, url):
    """设置MSprite图片"""
    for s in comp.get('component_data', {}).get('states', []):
        if s.get('label') == '默认':
            if 'MSprite' not in s.get('source', {}):
                s['source']['MSprite'] = {}
            s['source']['MSprite']['value'] = url
    return comp

def set_drag_answer(comp, answer_tag):
    """设置拖拽放置区的答案（用选项tag如'选项1'）"""
    tools = comp.get('component_data', {}).get('components', {}).get('tools', {})
    if 'LDragPlace' in tools:
        tools['LDragPlace']['itemList'] = [answer_tag]
    return comp

def set_draggable(comp, tag, label_text):
    """设置拖拽物品的tag和显示文本"""
    tools = comp.get('component_data', {}).get('components', {}).get('tools', {})
    if 'MDraggable' in tools:
        tools['MDraggable']['tag'] = tag
    # 设置显示文本
    for s in comp.get('component_data', {}).get('states', []):
        if s.get('label') == '默认':
            if 'MLabel' not in s.get('source', {}):
                s['source']['MLabel'] = {}
            s['source']['MLabel']['value'] = label_text
    return comp

# ========================
# 开心游乐园暑2 重新生成
# ========================

def generate_kaixin_shu2_v2():
    """基于开心游乐园春7（正确参考）生成暑2"""
    
    with open(REFS / 'kaixin_spring7_ref.json') as f:
        ref = json.load(f)
    
    # 图片URL（已上传）
    img_urls = {
        'collect stickers': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/2be4d09ca98a19781887ae1a5b941601.png',
        'watch films': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/70b77f4aff563449eeff3ba5062482b4.png',
        'stay inside': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/c3ff13da466a922921d5a00c2eb45d9f.png',
        'draw cartoons': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/b489b31b65e2cce7b7f735985fd4a59d.png',
    }
    
    # 题目数据（暑2 - 4题）
    # 结构: 每题1个拖拽区 + 多个固定文本 + 3个选项
    questions = [
        {
            'img_key': 'collect stickers',
            'img_url': img_urls['collect stickers'],
            'draggable_answer_tag': '选项1',  # 第1个选项是正确答案
            'draggable_labels': ['collect', 'draw', 'watch'],  # 选项显示文字
            'fixed_texts': [
                {'text': 'stickers', 'pos_idx': 0},  # 拖放区后的文本
                {'text': '.', 'pos_idx': 1},  # 句号
            ]
        },
        {
            'img_key': 'watch films',
            'img_url': img_urls['watch films'],
            'draggable_answer_tag': '选项2',  # 第2个选项是正确答案
            'draggable_labels': ['stay', 'watch', 'collect'],
            'fixed_texts': [
                {'text': 'films', 'pos_idx': 0},
                {'text': '.', 'pos_idx': 1},
            ]
        },
        {
            'img_key': 'stay inside',
            'img_url': img_urls['stay inside'],
            'draggable_answer_tag': '选项1',
            'draggable_labels': ['stay', 'collect', 'watch'],
            'fixed_texts': [
                {'text': 'inside', 'pos_idx': 0},
                {'text': '.', 'pos_idx': 1},
            ]
        },
        {
            'img_key': 'draw cartoons',
            'img_url': img_urls['draw cartoons'],
            'draggable_answer_tag': '选项3',
            'draggable_labels': ['watch', 'collect', 'draw'],
            'fixed_texts': [
                {'text': 'cartoons', 'pos_idx': 0},
                {'text': '.', 'pos_idx': 1},
            ]
        },
    ]
    
    # 使用参考第1关作为模板（每关结构相同）
    ref_level = ref['game'][0]
    
    new_levels = []
    
    for q_idx, q in enumerate(questions):
        level = copy.deepcopy(ref_level)
        
        # 1. 更新题目配图（在已知条件左1位置）
        for c in level['components']:
            name = c.get('component_data', {}).get('name', '')
            if '已知条件左1' in name:
                # 这是配图位置
                set_sprite(c, q['img_url'])
        
        # 2. 更新拖拽放置区答案（只保留第1个放置区，答案用选项tag）
        drag_places = [c for c in level['components'] if c.get('component_name') == '拖拽放置区']
        # 保留第1个，删除其他（避免空置未连接问题）
        to_remove = set()
        for i, dp in enumerate(drag_places):
            if i == 0:
                set_drag_answer(dp, q['draggable_answer_tag'])
                # 更新uuid避免重复
                dp['component_data']['id'] = new_uuid()
            else:
                # 标记删除，同时删除关联的错误配合节点
                dp_uuid = dp['component_data']['id']
                to_remove.add(id(dp))  # 用id作为标记
                # 找错误配合节点
                for j, c in enumerate(level['components']):
                    if '错误配合' in c.get('component_data', {}).get('name', ''):
                        for ev in c.get('component_data', {}).get('event', {}).get('value', []):
                            if ev.get('source') == dp_uuid:
                                to_remove.add(id(c))
        
        # 3. 更新拖拽物品（选项）- 只保留3个
        draggables = [c for c in level['components'] if c.get('component_name') == '拖拽物品']
        for i, drag in enumerate(draggables):
            if i < len(q['draggable_labels']):
                tag = f'选项{i+1}'
                label = q['draggable_labels'][i]
                set_draggable(drag, tag, label)
                # 计算正确宽度（根据文字长度，参考是300）
                transform = get_transform(drag)
                transform['w'] = max(200, len(label) * 50 + 50)
                set_transform(drag, w=transform['w'])
                drag['component_data']['id'] = new_uuid()
            else:
                to_remove.add(id(drag))
        
        # 4. 更新固定文本
        text_comps = [c for c in level['components'] if c.get('component_name') == '节点' and '已知条件' in c.get('component_data', {}).get('name', '')]
        # 已知条件左2 = 主要文本，已知条件左4 = 句号，已知条件左2_xxx = 其他文本
        for c in text_comps:
            name = c.get('component_data', {}).get('name', '')
            if '左4' in name:  # 句号位置
                set_label(c, '.')
            elif '左2' in name and '_' not in name:  # 主要文本（拖放区后）
                if q['fixed_texts']:
                    text = q['fixed_texts'][0]['text']
                    set_label(c, text)
                    # 调整宽度
                    transform = get_transform(c)
                    transform['w'] = max(100, len(text) * 36 + 30)
                    set_transform(c, w=transform['w'])
            elif '左2_' in name:  # 其他位置文本（拖放区前）
                # 暑2没有前置文本，可以删除或设置为空
                set_label(c, '')
        
        # 5. 删除多余组件
        level['components'] = [c for c in level['components'] if id(c) not in to_remove]
        
        # 6. 更新所有组件uuid
        for c in level['components']:
            c['component_data']['id'] = new_uuid()
        
        new_levels.append(level)
    
    result = copy.deepcopy(ref)
    result['game'] = new_levels
    return result


# ========================
# 过桥大冒险暑2 重新生成
# ========================

def generate_guoqiao_shu2_v2():
    """基于过桥大冒险秋14（正确参考）生成暑2"""
    
    with open(REFS / 'guoqiao_autumn14_ref.json') as f:
        ref = json.load(f)
    
    # 图片URL
    img_urls = {
        'ride bikes': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/1ddde668f36606fa4ea280bb2121058e.png',
        'play outside': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/32920ae7b7919ece73dc0b47f5640990.png',
        'watch films': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/5e009a2fb621003122587940e9e2b5d4.png',
        'stay inside': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/8a0debb509dab581883ee51fb9cadf72.png',
        'collect stickers': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/62fd937dde1a2a2dbabec8a8958a3aba.png',
        'stay inside 2': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/63de93d3f11271b1152fa1e1ae4c18e9.png',
    }
    
    # 题目数据（暑2 - 6题）
    # 每题结构：放置区数量不同，选项数量匹配
    questions = [
        # 关1: 1个放置区，2个选项
        {
            'img_key': 'ride bikes',
            'img_url': img_urls['ride bikes'],
            'drag_count': 1,
            'answer_tags': ['选项2'],  # 第2个选项是答案
            'draggable_labels': ['enjoy', 'enjoys'],
            'fixed_texts': ['Kuan', 'riding bikes', '.'],  # 前置、后置、句号
        },
        # 关2: 1个放置区，2个选项
        {
            'img_key': 'play outside',
            'img_url': img_urls['play outside'],
            'drag_count': 1,
            'answer_tags': ['选项2'],
            'draggable_labels': ['likes', 'like'],
            'fixed_texts': ['We', 'playing outside', '.'],
        },
        # 关3: 2个放置区，4个选项
        {
            'img_key': 'watch films',
            'img_url': img_urls['watch films'],
            'drag_count': 2,
            'answer_tags': ['选项1', '选项4'],  # loves, drawing
            'draggable_labels': ['loves', 'love', 'draw', 'drawing'],
            'fixed_texts': ['He', '', 'films', '.'],  # 中间空位是第2个放置区前
        },
        # 关4: 2个放置区，4个选项
        {
            'img_key': 'stay inside',
            'img_url': img_urls['stay inside'],
            'drag_count': 2,
            'answer_tags': ['选项2', '选项4'],  # don't enjoy, staying
            'draggable_labels': ["doesn't enjoy", "don't enjoy", 'stay', 'staying'],
            'fixed_texts': ['They', '', 'inside', '.'],
        },
        # 关5: 3个放置区，4个选项（乱序）
        {
            'img_key': 'collect stickers',
            'img_url': img_urls['collect stickers'],
            'drag_count': 3,
            'answer_tags': ['选项2', '选项1', '选项3'],  # Max, likes, collecting stickers
            'draggable_labels': ['likes', 'Max', 'collecting stickers', 'like'],
            'fixed_texts': ['', '', '', '.'],  # 全空，都是放置区
        },
        # 关6: 4个放置区，4个选项（乱序）
        {
            'img_key': 'stay inside 2',
            'img_url': img_urls['stay inside 2'],
            'drag_count': 4,
            'answer_tags': ['选项2', '选项3', '选项1', '选项4'],  # They, don't, like, staying inside
            'draggable_labels': ['staying inside', 'They', "don't", 'like'],
            'fixed_texts': ['', '', '', '', '.'],  # 全空
        },
    ]
    
    def find_ref_level_by_count(ref_game, drag_count):
        """根据放置区数量找到合适的参考关卡"""
        for level in ref_game:
            dp_count = sum(1 for c in level['components'] if c.get('component_name') == '拖拽放置区')
            if dp_count >= drag_count:
                return level
        return ref_game[0]
    
    new_levels = []
    
    for q in questions:
        ref_level = find_ref_level_by_count(ref['game'], q['drag_count'])
        level = copy.deepcopy(ref_level)
        
        # 1. 更新题目配图
        for c in level['components']:
            name = c.get('component_data', {}).get('name', '')
            if '配图' in name or '题目' in name:
                set_sprite(c, q['img_url'])
        
        # 2. 处理拖拽放置区
        drag_places = [(i, c) for i, c in enumerate(level['components']) if c.get('component_name') == '拖拽放置区']
        to_remove = set()
        
        for i, (idx, dp) in enumerate(drag_places):
            if i < q['drag_count']:
                # 保留，更新答案
                set_drag_answer(dp, q['answer_tags'][i])
                # 更新宽度（根据选项文字长度）
                # 参考：单放置区 w=534，双放置区每个 w=285
                transform = get_transform(dp)
                if q['drag_count'] == 1:
                    transform['w'] = 534
                else:
                    transform['w'] = 285
                set_transform(dp, w=transform['w'])
                dp['component_data']['id'] = new_uuid()
            else:
                # 删除多余的放置区及其关联的砖块掉落
                dp_uuid = dp['component_data']['id']
                to_remove.add(id(dp))
                # 删除关联的砖块掉落节点（紧跟在放置区后面的节点）
                if idx + 1 < len(level['components']):
                    next_c = level['components'][idx + 1]
                    if '砖块掉落' in next_c.get('component_data', {}).get('name', ''):
                        to_remove.add(id(next_c))
        
        # 3. 处理拖拽物品（选项）
        draggables = [c for c in level['components'] if c.get('component_name') == '拖拽物品']
        for i, drag in enumerate(draggables):
            if i < len(q['draggable_labels']):
                tag = f'选项{i+1}'
                label = q['draggable_labels'][i]
                set_draggable(drag, tag, label)
                # 更新宽度（根据文字长度，参考是286）
                transform = get_transform(drag)
                transform['w'] = max(200, len(label) * 40 + 40)
                set_transform(drag, w=transform['w'])
                drag['component_data']['id'] = new_uuid()
            else:
                to_remove.add(id(drag))
        
        # 4. 处理固定文本（桥墩）
        text_comps = [c for c in level['components'] if c.get('component_name') == '节点' and '桥墩' in c.get('component_data', {}).get('name', '')]
        for i, c in enumerate(text_comps):
            if i < len(q['fixed_texts']):
                text = q['fixed_texts'][i]
                set_label(c, text)
                # 更新宽度
                transform = get_transform(c)
                if text:
                    if q['drag_count'] == 1:
                        transform['w'] = 534
                    else:
                        transform['w'] = 285
                else:
                    transform['w'] = 50  # 空位占位
                set_transform(c, w=transform['w'])
            else:
                to_remove.add(id(c))
        
        # 5. 删除多余组件
        level['components'] = [c for c in level['components'] if id(c) not in to_remove]
        
        # 6. 更新所有uuid
        for c in level['components']:
            c['component_data']['id'] = new_uuid()
        
        new_levels.append(level)
    
    result = copy.deepcopy(ref)
    result['game'] = new_levels
    return result


# ========================
# 主程序
# ========================

if __name__ == '__main__':
    print('重新生成开心游乐园暑2配置（v2）...')
    kaixin_cfg = generate_kaixin_shu2_v2()
    kaixin_out = OUTPUT / 'kaixin_shu2_config_v2.json'
    with open(kaixin_out, 'w', encoding='utf-8') as f:
        json.dump(kaixin_cfg, f, ensure_ascii=False, indent=2)
    print(f'✅ 已保存: {kaixin_out}')
    
    print('\n重新生成过桥大冒险暑2配置（v2）...')
    guoqiao_cfg = generate_guoqiao_shu2_v2()
    guoqiao_out = OUTPUT / 'guoqiao_shu2_config_v2.json'
    with open(guoqiao_out, 'w', encoding='utf-8') as f:
        json.dump(guoqiao_cfg, f, ensure_ascii=False, indent=2)
    print(f'✅ 已保存: {guoqiao_out}')
    
    # 验证
    print('\n验证开心游乐园暑2 v2...')
    for i, lv in enumerate(kaixin_cfg['game']):
        dps = [c for c in lv['components'] if c.get('component_name') == '拖拽放置区']
        drags = [c for c in lv['components'] if c.get('component_name') == '拖拽物品']
        answers = [dp.get('component_data', {}).get('components', {}).get('tools', {}).get('LDragPlace', {}).get('itemList', []) for dp in dps]
        opts = [(c.get('component_data', {}).get('components', {}).get('tools', {}).get('MDraggable', {}).get('tag'), 
                 get_label(c)) for c in drags]
        print(f'  关{i+1}: 放置区{len(dps)}个 答案={answers} | 选项={opts}')
    
    print('\n验证过桥大冒险暑2 v2...')
    for i, lv in enumerate(guoqiao_cfg['game']):
        dps = [c for c in lv['components'] if c.get('component_name') == '拖拽放置区']
        drags = [c for c in lv['components'] if c.get('component_name') == '拖拽物品']
        answers = [dp.get('component_data', {}).get('components', {}).get('tools', {}).get('LDragPlace', {}).get('itemList', []) for dp in dps]
        print(f'  关{i+1}: 放置区{len(dps)}个 答案={answers} | 选项数={len(drags)}')
