#!/usr/bin/env python3
"""开心游乐园配置测试 — 从表格数据生成"""
import json, copy, uuid, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF  = os.path.join(BASE, 'output/kaixin_refs/57cd2b7b-4b73-11f1-b0f5-e648d636fd2c.json')
OUT  = os.path.join(BASE, 'output/kaixin_test/kaixin_test.json')
os.makedirs(os.path.dirname(OUT), exist_ok=True)

with open(REF) as f:
    ref_raw = json.load(f)
ref = ref_raw['configuration']
if isinstance(ref, str):
    ref = json.loads(ref)

# 题目数据 — 来自表格 国际level2开心游乐园暑2
IMG_BASE = 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-11/'

LEVELS = [
    {
        'scene_img': IMG_BASE + '7988efe4001137fd07255b5af7bd7ced.png',
        'fixed_text': 'stickers',
        'options': ['collect', 'draw', 'watch'],
        'correct': 'collect',
        'punct': '.',
    },
    {
        'scene_img': IMG_BASE + '146294ee56e742c24a723a6cf7454b79.png',
        'fixed_text': 'films',
        'options': ['stay', 'watch', 'collect'],
        'correct': 'watch',
        'punct': '.',
    },
    {
        'scene_img': IMG_BASE + 'c5d1adc336ff70a3ecedb8a328f9ca4c.png',
        'fixed_text': 'inside',
        'options': ['stay', 'collect', 'watch'],
        'correct': 'stay',
        'punct': '.',
    },
    {
        'scene_img': IMG_BASE + '207cafb41489a4b36ce6fa678bd56756.png',
        'fixed_text': 'cartoons',
        'options': ['watch', 'collect', 'draw'],
        'correct': 'draw',
        'punct': '.',
    },
]

AUDIO_PLACEHOLDER = (
    'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/'
    'assets/audio/345733/2024-10-23/932e121cce9ecbce78147287a0804ced.mp3'
)

def get_comp(comps, name):
    for c in comps:
        n = c.get('component_data', {}).get('name') or ''
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
        state['source'].setdefault('MLabel', {})['value'] = value

def set_msprite(state, url):
    if state and 'source' in state:
        state['source'].setdefault('MSprite', {})['value'] = url

def set_maudio(state, url):
    if state and 'source' in state:
        state['source'].setdefault('MAudio', {})['value'] = url

def set_mdraggable_tag(cd, tag):
    tools = cd.get('components', {}).get('tools', {})
    if 'MDraggable' in tools:
        tools['MDraggable']['tag'] = tag

def make_option_comp(ref_comp, text, audio_url):
    c = copy.deepcopy(ref_comp)
    cd = c['component_data']
    cd['id'] = str(uuid.uuid4())
    cd['name'] = f'选项-{text}'
    for label in ['默认', '放置', '当前组件错误', '拖拽中']:
        st = get_state(cd, label)
        if st:
            set_mlabel(st, text)
    st = get_state(cd, '拖拽中')
    if st:
        set_mlabel(st, text)
        set_maudio(st, audio_url)
    set_mdraggable_tag(cd, text)
    return c

# ── 提取参考组件 ──
ref_lvl0_comps = ref['game'][0]['components']
ref_bg       = get_comp(ref_lvl0_comps, '背景')
ref_node10   = get_comp(ref_lvl0_comps, '节点_10')
ref_node     = get_comp(ref_lvl0_comps, '节点')
ref_deer     = get_comp(ref_lvl0_comps, '小鹿动效')
ref_deer_ok  = get_comp(ref_lvl0_comps, '小鹿动效结算正确')
ref_cover    = get_comp(ref_lvl0_comps, '物理遮盖')
ref_levelnum = get_comp(ref_lvl0_comps, '关卡数组件')
ref_known5   = get_comp(ref_lvl0_comps, '已知条件左5')
ref_known5_2 = get_comp(ref_lvl0_comps, '已知条件左5_323182')
ref_known5_3 = get_comp(ref_lvl0_comps, '已知条件左5_5323184')
ref_slot     = get_comp(ref_lvl0_comps, '拖拽放置区2')
ref_slot_err = get_comp(ref_lvl0_comps, '放置区2错误配合')
ref_opt1     = get_comp(ref_lvl0_comps, '选项1')

def build_level(lvl_data, lvl_idx):
    scene_img  = lvl_data['scene_img']
    fixed_text = lvl_data['fixed_text']
    options    = lvl_data['options']
    correct    = lvl_data['correct']
    punct      = lvl_data['punct']

    # ⚠️ 渲染层级 = components[] 数组顺序（越靠后越在上层）
    comps = []

    # 1. 背景/装饰
    comps.append(copy.deepcopy(ref_bg))
    comps.append(copy.deepcopy(ref_node10))

    # 2. 场景图
    node = copy.deepcopy(ref_node)
    st = get_state(node['component_data'])
    if st:
        set_msprite(st, scene_img)
    comps.append(node)

    # 3. 固定文本（已知条件）
    k5 = copy.deepcopy(ref_known5)
    st = get_state(k5['component_data'])
    if st:
        set_mlabel(st, fixed_text)
    comps.append(k5)

    if ref_known5_2:
        comps.append(copy.deepcopy(ref_known5_2))
    if ref_known5_3:
        comps.append(copy.deepcopy(ref_known5_3))

    # 4. 拖拽放置区 + 错误配合
    slot = copy.deepcopy(ref_slot)
    slot['component_data']['id'] = str(uuid.uuid4())
    comps.append(slot)
    comps.append(copy.deepcopy(ref_slot_err))

    # 5. 关卡数组件
    comps.append(copy.deepcopy(ref_levelnum))

    # 6. 小鹿动效 + 遮盖
    comps.append(copy.deepcopy(ref_deer))
    comps.append(copy.deepcopy(ref_deer_ok))
    comps.append(copy.deepcopy(ref_cover))

    # 7. 选项（最后 = 最顶层，保证可拖拽）
    for i, opt_text in enumerate(options):
        opt = make_option_comp(ref_opt1, opt_text, AUDIO_PLACEHOLDER)
        opt['component_data']['name'] = f'选项{i+1}'
        comps.append(opt)

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

result = {
    'additional':  copy.deepcopy(ref.get('additional', {})),
    'common':      copy.deepcopy(ref.get('common', {})),
    'components':  copy.deepcopy(ref.get('components', [])),
    'game': [],
}

for i, lv in enumerate(LEVELS):
    level = build_level(lv, i)
    result['game'].append(level)
    opts_str = ', '.join(lv['options'])
    print(f'  Q{i+1}: {lv["correct"]} {lv["fixed_text"]} | 选项=[{opts_str}] | correct={lv["correct"]}')

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

size = os.path.getsize(OUT)
print(f'\n✅ 生成: {OUT} ({size} bytes, {len(result["game"])}关)')

# 校验
for i, lvl in enumerate(result['game']):
    comps = lvl['components']
    names = [c['component_data'].get('name','?') for c in comps]
    opts = [n for n in names if n.startswith('选项')]
    # 检查选项是否在数组最后
    last_opts_idx = max(i for i, n in enumerate(names) if n.startswith('选项'))
    total = len(names)
    print(f'  关卡{i+1}: {total}组件, 选项从索引{names.index(opts[0])}到{last_opts_idx}(共{len(opts)}项)')
    if last_opts_idx == total - 1:
        print(f'    ✅ 选项在数组末尾（最顶层）')
    else:
        print(f'    ⚠️ 选项不在末尾！index={last_opts_idx}/{total-1}')