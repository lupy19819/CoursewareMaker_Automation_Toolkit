#!/usr/bin/env python3
"""
生成 开心游乐园暑2 和 过桥大冒险暑2 游戏配置
"""
import json
import os
import sys
import uuid
import copy

# 添加 toolkit 路径
sys.path.insert(0, '/home/148139_wy/.openclaw/workspace/CoursewareMaker_Automation_Toolkit')

def generate_kaixin_config(image_urls):
    """生成开心游乐园配置 - 简化版，每关1个拖拽槽+3个选项"""
    from data.kaixin_questions import questions
    
    # 读取参考配置模板
    ref_path = '/home/148139_wy/.openclaw/workspace/CoursewareMaker_Automation_Toolkit/reference_configs/kaixin_ref.json'
    if os.path.exists(ref_path):
        with open(ref_path) as f:
            template = json.load(f)
    else:
        print(f"参考配置不存在: {ref_path}")
        return None
    
    # 简化：使用第一关作为模板，复制并修改
    levels = []
    for i, q in enumerate(questions):
        level = copy.deepcopy(template['game'][0]) if template.get('game') else None
        if not level:
            continue
            
        # 更新组件
        for comp in level['components']:
            comp_id = comp.get('id', '')
            
            # 更新题目配图
            if comp.get('name') == '题目配图':
                img_url = image_urls.get(q['image'], '')
                if img_url and comp.get('states'):
                    for state in comp['states']:
                        if state.get('source', {}).get('MSprite'):
                            state['source']['MSprite']['value'] = img_url
            
            # 更新拖拽放置区的正确答案
            if 'LDragPlace' in str(comp.get('component_data', {})):
                tools = comp.get('component_data', {}).get('components', {}).get('tools', {})
                if tools.get('LDragPlace'):
                    tools['LDragPlace']['itemList'] = [q['correct']]
            
            # 更新选项文本和tag
            if 'MDraggable' in str(comp.get('component_data', {})):
                draggable = comp.get('component_data', {}).get('components', {}).get('tools', {}).get('MDraggable', {})
                # 需要找到对应的选项索引来设置
                # 简化：这里假设选项顺序是固定的
                pass
        
        levels.append(level)
    
    template['game'] = levels
    return template


def generate_guoqiao_config(image_urls):
    """生成过桥大冒险配置 - 每关可能有多个拖拽槽"""
    from data.guoqiao_questions import questions
    
    # 读取参考配置模板
    ref_path = '/home/148139_wy/.openclaw/workspace/CoursewareMaker_Automation_Toolkit/reference_configs/guoqiao_ref.json'
    if os.path.exists(ref_path):
        with open(ref_path) as f:
            template = json.load(f)
    else:
        print(f"参考配置不存在: {ref_path}")
        return None
    
    levels = []
    for i, q in enumerate(questions):
        level = copy.deepcopy(template['game'][0]) if template.get('game') else None
        if not level:
            continue
        
        # 更新题目配图
        for comp in level['components']:
            if comp.get('name') == '题目配图':
                img_url = image_urls.get(q['image'], '')
                if img_url and comp.get('states'):
                    for state in comp['states']:
                        if state.get('source', {}).get('MSprite'):
                            state['source']['MSprite']['value'] = img_url
        
        # 需要根据句子结构动态调整拖拽放置区和选项
        # 这里简化处理，假设使用固定模板
        levels.append(level)
    
    template['game'] = levels
    return template


if __name__ == '__main__':
    # 测试生成
    print("Config generator ready")
    print(f"Images available in: /home/148139_wy/.openclaw/workspace/game_assets/batch1/1批/")
