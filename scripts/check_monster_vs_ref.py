#!/usr/bin/env python3
"""
上传前强制结构校验：对比生成配置与参考配置的结构一致性
用法: python3 check_monster_vs_ref.py <generated.json> <ref.json> <level_count>
"""
import json, sys

def fail(msg):
    print(f"❌ STRUCT_CHECK FAILED: {msg}")
    sys.exit(1)

gen_path, ref_path, level_count = sys.argv[1], sys.argv[2], int(sys.argv[3])

with open(gen_path) as f: raw = json.load(f)
with open(ref_path) as f: ref = json.load(f)

# 解包生成配置
if 'result' in raw and 'configuration' in raw.get('result', {}):
    gen = json.loads(raw['result']['configuration'])
else:
    gen = raw

ref_level = ref['game'][0]
ref_comps = ref_level['components']

errors = []
for li, level in enumerate(gen['game']):
    comps = level['components']
    if len(comps) != len(ref_comps):
        errors.append(f"L{li+1}: components数量 {len(comps)} != 参考 {len(ref_comps)}")
        continue

    # 1. comp[3] compLoadFinish MAudio 必须为空
    c3 = comps[3]['component_data']
    for s in c3.get('states', []):
        if s['state'] == 'compLoadFinish':
            v = s.get('source', {}).get('MAudio', {}).get('value', '')
            if v:
                errors.append(f"L{li+1}: comp[3] compLoadFinish MAudio 非空: {v[-40:]}")

    # 2. comp[7,8,9] 点击选择 MSprite 必须为空
    for idx in [7, 8, 9]:
        cd = comps[idx]['component_data']
        for s in cd.get('states', []):
            sprite_val = s.get('source', {}).get('MSprite', {}).get('value', '')
            if sprite_val:
                errors.append(f"L{li+1}: comp[{idx}]({cd['name']}) state={s['state']} MSprite非空")

    # 3. comp[7,8,9] 必须有且仅有一个 anwserRadio=1
    radios = []
    for idx in [7, 8, 9]:
        cd = comps[idx]['component_data']
        v = cd['components']['tools']['AloneClickChoice']['anwserConfig']['anwserRadio']
        radios.append(v)
    if radios.count(1) != 1:
        errors.append(f"L{li+1}: anwserRadio=1 数量={radios.count(1)}, 应为1 (radios={radios})")

    # 4. comp[4,5,6] default state MSprite 必须有图片 URL
    for idx in [4, 5, 6]:
        cd = comps[idx]['component_data']
        for s in cd.get('states', []):
            if s['state'] == 'default':
                v = s.get('source', {}).get('MSprite', {}).get('value', '')
                if not v:
                    errors.append(f"L{li+1}: comp[{idx}]({cd['name']}) default MSprite 为空")

    # 5. comp[3] clickEnd MAudio 必须有音频 URL
    for s in c3.get('states', []):
        if s['state'] == 'clickEnd':
            v = s.get('source', {}).get('MAudio', {}).get('value', '')
            if not v:
                errors.append(f"L{li+1}: comp[3] clickEnd MAudio 为空")

if len(gen['game']) != level_count:
    errors.append(f"关卡数 {len(gen['game'])} != 期望 {level_count}")

if errors:
    for e in errors:
        print(f"  ❌ {e}")
    fail(f"{len(errors)} 个结构错误")
else:
    print(f"✅ STRUCT_CHECK PASSED — {level_count}关全部通过")
