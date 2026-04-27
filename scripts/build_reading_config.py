#!/usr/bin/env python3
"""
阅读小帆船 & 阅读小火车 配置生成脚本

用法：
    python3 scripts/build_reading_config.py --type fanboat --options 4 --input question.json --output output/my_config.json
    python3 scripts/build_reading_config.py --type train   --options 3 --input question.json --output output/my_config.json

输入 question.json 格式（以4选项帆船为例）：
{
  "slots": [
    { "topic_audio": "https://...1.mp3", "option_image": "https://...1.png", "drag_audio": "https://...drag.mp3" },
    { "topic_audio": "https://...2.mp3", "option_image": "https://...2.png", "drag_audio": "https://...drag.mp3" },
    { "topic_audio": "https://...3.mp3", "option_image": "https://...3.png", "drag_audio": "https://...drag.mp3" },
    { "topic_audio": "https://...4.mp3", "option_image": "https://...4.png", "drag_audio": "https://...drag.mp3" }
  ],
  "answers": {
    "1": "b",   // 放置区1 接受 tag=b 的选项（即第2个选项）
    "2": "a",
    "3": "d",
    "4": "c"
  }
}

slots 按放置区顺序排列（slots[0] = 放置区1 的题干语音）。
answers key 为放置区序号（字符串），value 为该放置区接受的选项tag。

选项tag规则（与基准配置保持一致）：
  小帆船 4选项: a / b / c / d
  小帆船 3选项: 1 / 2 / 3
  小火车  4选项: 1 / 2 / 3 / 4
  小火车  3选项: a / b / c
"""

import json
import copy
import argparse
import os
import sys

# 基准配置路径（按游戏类型 + 选项数）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(SCRIPT_DIR, '..', 'output')

BASE_CONFIGS = {
    ('fanboat', 3): 'fanboat_configs_all',
    ('fanboat', 4): 'fanboat_configs_all',
    ('train',   3): 'train_configs_all',
    ('train',   4): 'train_configs_all',
}

# 各场景的基准游戏名（优先从这里找基准）
BASE_GAME_NAMES = {
    ('fanboat', 3): '国际启F融阅读小帆船秋8',
    ('fanboat', 4): '国际启蒙阅读小帆船秋8',
    ('train',   3): '国际starter阅读小火车秋12',
    ('train',   4): '国际F融阅读小火车暑5',
}

# 各场景的tag序列
TAGS = {
    ('fanboat', 3): ['1', '2', '3'],
    ('fanboat', 4): ['a', 'b', 'c', 'd'],
    ('train',   3): ['a', 'b', 'c'],
    ('train',   4): ['1', '2', '3', '4'],
}


def load_base_config(game_type, option_count):
    """加载基准配置"""
    dir_key = BASE_CONFIGS[(game_type, option_count)]
    dir_path = os.path.join(BASE_DIR, dir_key)
    index_path = os.path.join(dir_path, 'index.json')

    if not os.path.exists(index_path):
        raise FileNotFoundError(f"找不到索引文件: {index_path}\n请先运行抓取脚本获取基准配置。")

    with open(index_path) as f:
        index = json.load(f)

    target_name = BASE_GAME_NAMES[(game_type, option_count)]
    game_id = None
    for g in index:
        if target_name in g['game_name']:
            game_id = g['game_id']
            break

    if not game_id:
        # 退而求其次：找第一个选项数匹配的
        for g in index:
            cfg_path = os.path.join(dir_path, f"{g['game_id']}.json")
            if not os.path.exists(cfg_path):
                continue
            with open(cfg_path) as f:
                cfg = json.load(f)
            level = cfg.get('game', [{}])[0]
            draggables = sum(1 for c in level.get('components', [])
                           if 'MDraggable' in c.get('component_data', {}).get('components', {}).get('tools', {}))
            if draggables == option_count:
                game_id = g['game_id']
                print(f"  基准游戏: {g['game_name']}")
                break

    if not game_id:
        raise ValueError(f"找不到 {game_type} {option_count}选项的基准配置")

    cfg_path = os.path.join(dir_path, f"{game_id}.json")
    with open(cfg_path) as f:
        return json.load(f)


def get_draggable_components(level, option_count):
    """返回所有 MDraggable 组件，按 tag 排序"""
    comps = []
    for c in level.get('components', []):
        cd = c.get('component_data', {})
        tools = cd.get('components', {}).get('tools', {})
        if 'MDraggable' in tools:
            comps.append(c)
    return comps


def get_place_components(level):
    """返回所有 LDragPlace 组件，按名称中的数字排序"""
    comps = []
    for c in level.get('components', []):
        cd = c.get('component_data', {})
        tools = cd.get('components', {}).get('tools', {})
        if 'LDragPlace' in tools:
            comps.append(c)
    return comps


def get_topic_audio_components(level, game_type):
    """返回题干语音组件（按顺序）"""
    comps = []
    for c in level.get('components', []):
        cd = c.get('component_data', {})
        nm = cd.get('name', '')
        tools = cd.get('components', {}).get('tools', {})
        if game_type == 'fanboat':
            # 语音1 / 语音2 / ... → 在states[点击按下]中有MAudio
            if nm.startswith('语音'):
                comps.append(c)
        else:  # train
            # 音频播放按钮N → MTouchable
            if '音频播放按钮' in nm and 'MTouchable' in tools:
                comps.append(c)
    # 按名称尾部数字排序
    def sort_key(c):
        nm = c['component_data']['name']
        digits = ''.join(filter(str.isdigit, nm))
        return int(digits) if digits else 0
    comps.sort(key=sort_key)
    return comps


def set_audio_in_states(cd, state_label, audio_url):
    """在指定 state 里设置 MAudio.value"""
    for st in cd.get('states', []):
        if st.get('label') == state_label:
            st.setdefault('source', {}).setdefault('MAudio', {})['value'] = audio_url
            return True
    return False


def set_image_in_states(cd, state_labels, image_url):
    """在指定多个 state 里设置 MSprite.value"""
    for st in cd.get('states', []):
        if st.get('label') in state_labels:
            st.setdefault('source', {}).setdefault('MSprite', {})['value'] = image_url


def generate_config(game_type, option_count, question_data):
    """
    生成配置。
    question_data: {
      "slots": [ { "topic_audio": "...", "option_image": "...", "drag_audio": "..." }, ... ],
      "answers": { "1": "b", "2": "a", ... }  // 放置区N → 正确tag
    }
    """
    slots = question_data['slots']
    answers = question_data['answers']

    if len(slots) != option_count:
        raise ValueError(f"slots数量({len(slots)}) 与 option_count({option_count}) 不符")

    tags = TAGS[(game_type, option_count)]

    # 加载并深拷贝基准配置
    base = load_base_config(game_type, option_count)
    cfg = copy.deepcopy(base)
    level = cfg['game'][0]

    draggables = get_draggable_components(level, option_count)
    places = get_place_components(level)
    topic_comps = get_topic_audio_components(level, game_type)

    print(f"  找到拖拽选项: {len(draggables)}个 放置区: {len(places)}个 题干语音: {len(topic_comps)}个")

    if len(draggables) != option_count:
        raise ValueError(f"基准配置拖拽选项数({len(draggables)}) 与目标({option_count}) 不符")

    # 按 tag 排序 draggables（tag顺序 = slots顺序）
    tag_order = {t: i for i, t in enumerate(tags)}
    draggables.sort(key=lambda c: tag_order.get(
        c['component_data']['components']['tools']['MDraggable'].get('tag', ''), 99))

    # 1. 替换选项图片和拖拽音效
    for i, comp in enumerate(draggables):
        slot = slots[i]
        cd = comp['component_data']

        # 图片：默认 / 拖拽中 / 放置 三态均相同
        set_image_in_states(cd, ['默认', '拖拽中', '放置'], slot['option_image'])

        # 拖拽音效
        if slot.get('drag_audio'):
            set_audio_in_states(cd, '拖拽中', slot['drag_audio'])
            set_audio_in_states(cd, '放置', slot['drag_audio'])

    # 2. 替换题干语音
    for i, comp in enumerate(topic_comps):
        if i >= len(slots):
            break
        slot = slots[i]
        cd = comp['component_data']
        if game_type == 'fanboat':
            set_audio_in_states(cd, '点击按下', slot['topic_audio'])
        else:  # train
            set_audio_in_states(cd, '按下', slot['topic_audio'])

    # 3. 更新放置区 itemList（正确答案）
    places_sorted = sorted(places, key=lambda c: c['component_data']['name'])
    for idx_p, comp in enumerate(places_sorted):
        place_num = str(idx_p + 1)
        if place_num in answers:
            cd = comp['component_data']
            cd['components']['tools']['LDragPlace']['itemList'] = [answers[place_num]]

    return cfg


def validate_config(cfg, game_type, option_count):
    """校验生成的配置"""
    errors = []
    level = cfg['game'][0]

    draggables = get_draggable_components(level, option_count)
    places = get_place_components(level)
    tags = TAGS[(game_type, option_count)]

    # 选项数量
    if len(draggables) != option_count:
        errors.append(f"拖拽选项数量异常: {len(draggables)} ≠ {option_count}")
    if len(places) != option_count:
        errors.append(f"放置区数量异常: {len(places)} ≠ {option_count}")

    # 每个选项都有图片
    for comp in draggables:
        cd = comp['component_data']
        nm = cd.get('name', '')
        for st in cd.get('states', []):
            if st.get('label') == '默认':
                val = st.get('source', {}).get('MSprite', {}).get('value', '')
                if not val:
                    errors.append(f"选项{nm} 默认图片为空")

    # 每个放置区都有 itemList
    for comp in places:
        cd = comp['component_data']
        nm = cd.get('name', '')
        item_list = cd.get('components', {}).get('tools', {}).get('LDragPlace', {}).get('itemList', [])
        if not item_list:
            errors.append(f"放置区{nm} itemList为空（未设置正确答案）")

    # 题干语音非空（从 topic 组件检查）
    topic_comps = get_topic_audio_components(level, game_type)
    for comp in topic_comps:
        cd = comp['component_data']
        nm = cd.get('name', '')
        has_audio = False
        label = '点击按下' if game_type == 'fanboat' else '按下'
        for st in cd.get('states', []):
            if st.get('label') == label:
                if st.get('source', {}).get('MAudio', {}).get('value'):
                    has_audio = True
        if not has_audio:
            errors.append(f"题干语音{nm} [{label}] 音频为空")

    return errors


def main():
    parser = argparse.ArgumentParser(description='阅读小帆船/小火车配置生成脚本')
    parser.add_argument('--type', required=True, choices=['fanboat', 'train'], help='游戏类型: fanboat=小帆船 train=小火车')
    parser.add_argument('--options', required=True, type=int, choices=[2, 3, 4], help='选项数量')
    parser.add_argument('--input', required=True, help='题目数据JSON文件路径')
    parser.add_argument('--output', required=True, help='输出配置JSON文件路径')
    args = parser.parse_args()

    print(f"[配置生成] 游戏类型={args.type} 选项数={args.options}")

    with open(args.input) as f:
        question_data = json.load(f)

    print(f"  生成配置...")
    cfg = generate_config(args.type, args.options, question_data)

    print(f"  校验配置...")
    errors = validate_config(cfg, args.type, args.options)
    if errors:
        print("❌ 校验失败：")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

    print(f"✅ 配置已生成: {args.output}")


if __name__ == '__main__':
    main()
