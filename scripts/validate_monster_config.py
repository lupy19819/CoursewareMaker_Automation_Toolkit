#!/usr/bin/env python3
"""
贪吃小怪兽配置校验脚本 v3
基于真实参考配置结构：
  - 图片在 节点/节点_103/节点_104（底图组件），不在 点击选择
  - 点击选择 MSprite.value 保持为空
  - 音频在 音频播放按钮 的 clickEnd 状态
  - 正确答案由 点击选择N.anwserRadio=1 决定
  - compLoadFinish jump.type = countdown（不要求 audioPlayFinish）
用法: python3 scripts/validate_monster_config.py <output.json> [expected_levels=8]
"""
import json, sys

IMG_NODE_NAMES = {'节点', '节点_102', '节点_103', '节点_104'}
CHOICE_NAMES = {'点击选择1', '点击选择2', '点击选择3'}

def load_config(path):
    with open(path) as f:
        raw = json.load(f)
    if 'result' in raw and 'configuration' in raw.get('result', {}):
        cfg_str = raw['result']['configuration']
        return json.loads(cfg_str) if isinstance(cfg_str, str) else cfg_str
    elif 'game' in raw:
        return raw
    else:
        raise ValueError(f"无法识别文件结构，顶层 keys: {list(raw.keys())}")

def validate(path, expected_levels=8):
    errors = []
    warnings = []

    cfg = load_config(path)
    game = cfg.get('game', [])

    if len(game) != expected_levels:
        errors.append(f"关卡数应为 {expected_levels}，实际 {len(game)}")

    for gi, g in enumerate(game):
        level = gi + 1
        comps = g.get('components', [])

        # ── 音频播放按钮 ──
        audio_comps = [c for c in comps if c.get('component_name') == '音频播放按钮']
        if not audio_comps:
            errors.append(f"关{level}: 缺少 音频播放按钮 组件")
        else:
            ac = audio_comps[0]
            states = {s['state']: s for s in ac['component_data'].get('states', [])}

            # clickEnd 必须有 MAudio.value
            ce = states.get('clickEnd', {})
            audio_url = ce.get('source', {}).get('MAudio', {}).get('value', '')
            if not audio_url:
                errors.append(f"关{level}: clickEnd 音频 URL 为空")

        # ── 底图节点（图片在节点组件的 default state）──
        # 找 x 坐标从小到大的3个含图片的节点
        img_nodes = []
        for c in comps:
            cname = c.get('component_name', '')
            cd = c['component_data']
            name = cd.get('name', '')
            if cname in ('点击选择', '关卡数组件', '音频播放按钮'):
                continue
            for s in cd.get('states', []):
                if s['state'] == 'default':
                    v = s.get('source', {}).get('MSprite', {}).get('value', '')
                    if v and '/image/' in v and '/345733/' in v:
                        x = s.get('transform', {}).get('x', 0)
                        img_nodes.append((name, x, v))
        img_nodes.sort(key=lambda n: n[1])

        if len(img_nodes) != 3:
            errors.append(f"关{level}: 含图片的底图节点数应为 3，实际 {len(img_nodes)}")
        else:
            for i, (name, x, url) in enumerate(img_nodes):
                if not url:
                    errors.append(f"关{level} 底图节点{i+1}({name}): 图片 URL 为空")

        # ── 点击选择：正确项数量 ──
        choices = [c for c in comps if c.get('component_name') == '点击选择']
        if len(choices) != 3:
            errors.append(f"关{level}: 点击选择 组件数应为 3，实际 {len(choices)}")
        else:
            correct_count = 0
            for comp in choices:
                cd = comp['component_data']
                ar = cd.get('components', {}).get('tools', {}).get('AloneClickChoice', {}).get('anwserConfig', {}).get('anwserRadio')
                if ar == 1:
                    correct_count += 1
                elif ar != 2:
                    errors.append(f"关{level} {cd.get('name','')}: anwserRadio={ar!r}，应为 1 或 2")
            if correct_count != 1:
                errors.append(f"关{level}: 正确选项数量应为 1，实际 {correct_count}")

    # 结果
    if errors:
        print(f"❌ INVALID — {path}")
        for e in errors:
            print(f"  ERROR: {e}")
        for w in warnings:
            print(f"  WARN:  {w}")
        sys.exit(1)
    else:
        print(f"✅ VALID — {path}")
        if warnings:
            for w in warnings:
                print(f"  WARN: {w}")
        sys.exit(0)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 scripts/validate_monster_config.py <output.json> [expected_levels=8]")
        sys.exit(1)
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    validate(sys.argv[1], n)
