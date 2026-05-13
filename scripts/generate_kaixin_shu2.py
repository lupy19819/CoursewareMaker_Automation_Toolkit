#!/usr/bin/env python3
"""
generate_kaixin_shu2.py
国际level2开心游乐园暑2 — 动态布局版

从参考配置（暑2线上存档）提取固定骨架，
按 LEVELS 数据逐关替换可变部分。
"""

import json, copy, uuid, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REF  = os.path.join(BASE, 'output/kaixin_refs/57cd2b7b-4b73-11f1-b0f5-e648d636fd2c.json')
OUT  = os.path.join(BASE, 'output/kaixin_shu2/kaixin_shu2.json')
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# ── 参考配置 ────────────────────────────────────────────────────────────────
with open(REF) as f:
    ref_raw = json.load(f)
ref = ref_raw['configuration']
if isinstance(ref, str):
    ref = json.loads(ref)

# ── 关卡数据 ────────────────────────────────────────────────────────────────
# 资源图片 BASE（最新上传批次 2026-05-11）
IMG_BASE = 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-11/'

LEVELS = [
    {
        'scene_img': IMG_BASE + '7988efe4001137fd07255b5af7bd7ced.png',
        'fixed_text': 'stickers',   # 已知条件词（右侧固定名词）
        'options':    ['collect', 'draw', 'watch'],  # 第一个为正确答案
        'correct':    'collect',
        'punct':      '.',
    },
    {
        'scene_img': IMG_BASE + '146294ee56e742c24a723a6cf7454b79.png',
        'fixed_text': 'films',
        'options':    ['watch', 'stay', 'collect'],
        'correct':    'watch',
        'punct':      '.',
    },
    {
        'scene_img': IMG_BASE + 'c5d1adc336ff70a3ecedb8a328f9ca4c.png',
        'fixed_text': 'inside',
        'options':    ['stay', 'collect', 'watch'],
        'correct':    'stay',
        'punct':      '.',
    },
    {
        'scene_img': IMG_BASE + '207cafb41489a4b36ce6fa678bd56756.png',
        'fixed_text': 'cartoons',
        'options':    ['draw', 'watch', 'collect'],
        'correct':    'draw',
        'punct':      '.',
    },
]

# ── 工具函数 ────────────────────────────────────────────────────────────────
AUDIO_PLACEHOLDER = (
    'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/'
    'assets/audio/345733/2024-10-23/932e121cce9ecbce78147287a0804ced.mp3'
)

def get_comp(comps, name):
    for c in comps:
        n = c.get('component_data', {}).get('name') or c.get('component_data', {}).get('id') or ''
        if n == name:
            return c
    return None

def get_state(cd, label='默认'):
    for s in cd.get('states', []):
        if s.get('label') == label:
            return s
    return None

def set_mlabel(state, value):
    if state and 'source' in state:
        if 'MLabel' not in state['source']:
            state['source']['MLabel'] = {}
        state['source']['MLabel']['value'] = value

def set_msprite(state, url):
    if state and 'source' in state:
        if 'MSprite' not in state['source']:
            state['source']['MSprite'] = {}
        state['source']['MSprite']['value'] = url

def set_maudio(state, url):
    if state and 'source' in state:
        if 'MAudio' not in state['source']:
            state['source']['MAudio'] = {}
        state['source']['MAudio']['value'] = url

def make_option_comp(ref_comp, text, audio_url):
    """从参考选项组件复制，替换文字和音频"""
    c = copy.deepcopy(ref_comp)
    c['component_data']['name'] = c['component_data'].get('name', '选项')
    c['component_data']['id']   = str(uuid.uuid4())
    for label in ['默认', '放置', '当前组件错误']:
        st = get_state(c['component_data'], label)
        if st:
            set_mlabel(st, text)
    # 拖拽中 state → 音频
    st = get_state(c['component_data'], '拖拽中')
    if st:
        set_mlabel(st, text)
        set_maudio(st, audio_url)
    return c

# ── 提取参考关卡0的固定骨架组件 ─────────────────────────────────────────────
ref_lvl0_comps = ref['game'][0]['components']

ref_bg          = get_comp(ref_lvl0_comps, '背景')
ref_node10      = get_comp(ref_lvl0_comps, '节点_10')
ref_node        = get_comp(ref_lvl0_comps, '节点')
ref_deer        = get_comp(ref_lvl0_comps, '小鹿动效')
ref_deer_ok     = get_comp(ref_lvl0_comps, '小鹿动效结算正确')
ref_cover       = get_comp(ref_lvl0_comps, '物理遮盖')
ref_levelnum    = get_comp(ref_lvl0_comps, '关卡数组件')
ref_known5      = get_comp(ref_lvl0_comps, '已知条件左5')
ref_known5_2    = get_comp(ref_lvl0_comps, '已知条件左5_323182')
ref_known5_3    = get_comp(ref_lvl0_comps, '已知条件左5_5323184')
ref_slot        = get_comp(ref_lvl0_comps, '拖拽放置区2')
ref_slot_err    = get_comp(ref_lvl0_comps, '放置区2错误配合')
# 选项模板（从关卡0取一个）
ref_opt1        = get_comp(ref_lvl0_comps, '选项1')

# ── 构建关卡 ────────────────────────────────────────────────────────────────
def build_level(lvl_data, lvl_idx):
    scene_img   = lvl_data['scene_img']
    fixed_text  = lvl_data['fixed_text']
    options     = lvl_data['options']
    correct     = lvl_data['correct']
    punct       = lvl_data['punct']

    comps = []

    # 1. 背景 & 装饰
    comps.append(copy.deepcopy(ref_bg))
    comps.append(copy.deepcopy(ref_node10))

    # 2. 场景图（节点）
    node = copy.deepcopy(ref_node)
    st = get_state(node['component_data'])
    if st:
        set_msprite(st, scene_img)
    comps.append(node)

    # 3. 已知条件左5（固定名词）
    k5 = copy.deepcopy(ref_known5)
    st = get_state(k5['component_data'])
    if st:
        set_mlabel(st, fixed_text)
    comps.append(k5)

    # 4. 装饰性已知条件（无文字）
    if ref_known5_2:
        comps.append(copy.deepcopy(ref_known5_2))
    if ref_known5_3:
        comps.append(copy.deepcopy(ref_known5_3))

    # 5. 拖拽放置区（1个槽）
    slot = copy.deepcopy(ref_slot)
    slot['component_data']['id'] = str(uuid.uuid4())
    comps.append(slot)

    # 6. 放置区错误配合
    comps.append(copy.deepcopy(ref_slot_err))

    # 7. 关卡数组件
    comps.append(copy.deepcopy(ref_levelnum))

    # 8. 小鹿动效 & 遮盖（在选项之前，渲染在选项下层）
    comps.append(copy.deepcopy(ref_deer))
    comps.append(copy.deepcopy(ref_deer_ok))
    comps.append(copy.deepcopy(ref_cover))

    # 9. 选项（3个）—— 最后 = 最顶层，保证可拖拽交互
    for i, opt_text in enumerate(options):
        opt = make_option_comp(ref_opt1, opt_text, AUDIO_PLACEHOLDER)
        opt['component_data']['name'] = f'选项{i+1}'
        comps.append(opt)

    # 关卡答案配置（正确选项 index）
    correct_idx = options.index(correct) if correct in options else 0

    return {
        'id':     f'gamenext_level_uuid_{uuid.uuid4()}',
        'title':  {'component_data': {}, 'component_id': '', 'component_url': ''},
        'transition': ref['game'][0].get('transition', {}),
        'video':  ref['game'][0].get('video', {}),
        'levelData': {
            'autoNextLevel':   {'auto': True,  'wait': 4},
            'autoStopLevel':   {'auto': False, 'errorCount': 1, 'wait': 0},
            'errorLimit':      {'allowErrorCount': 0},
            'failAutoReset':   {'auto': False, 'wait': 0},
            'judge':           {'autoJudge': 1, 'judgeRule': 1},
            'selectionComponent': {'enabled': False, 'repelCount': 0, 'selections': []},
            'uiConfig': {},
        },
        'components': comps,
    }

# ── 组装最终配置 ─────────────────────────────────────────────────────────────
result = {
    'additional':  copy.deepcopy(ref.get('additional', {})),
    'common':      copy.deepcopy(ref.get('common', {})),
    'components':  copy.deepcopy(ref.get('components', [])),
    'game': [],
}

for i, lv in enumerate(LEVELS):
    level = build_level(lv, i)
    result['game'].append(level)
    n_slots = 1
    print(f'  关卡{i+1} [{lv["correct"]} {lv["fixed_text"]}...]: {n_slots}槽, {len(lv["options"])}选项')

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f'\n✅ 已生成: {OUT}')
print(f'   关卡数: {len(result["game"])}')
print(f'   顶层keys: {list(result.keys())}')
