"""
过桥大冒险配置生成器 v3 (2026-05-11)
策略：以上传的参考配置为骨架，deepcopy 关卡结构，
      仅替换以下变量部分：
        - 题目配图 MSprite URL
        - 点击选择 播放态 MAudio URL
        - 拖拽放置区 (slots): itemList / 位置 / UUID
        - 桥墩 (固定词): MLabel.value / 位置 / 宽度
        - 桥墩space (词间隔): 位置
        - 砖块掉落: event.source UUID (绑定对应 slot UUID)
        - 选项: MLabel.value / tag / 位置

固定不动：背景、关卡数组件、喇叭低层级、小鹿开车的 spine/audio、
           句号（仅调整 x）、节点、common 层结构
"""

import argparse
import json, copy, uuid, os, sys, re

# ──────────────────────────────────────────────
# 路径
# ──────────────────────────────────────────────
TOOLKIT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD_REF   = os.path.join(TOOLKIT, 'output/guoqiao_configs/87ddb0a3-ea04-11f0-9165-0e324dbd00ee.json')
OUT_DIR   = os.path.join(TOOLKIT, 'output/guoqiao_shu2')
DEFAULT_REF_PATH = '/tmp/guoqiao_ref_clean.json'   # 上传的新参考配置
DEFAULT_OUT_FILE = os.path.join(OUT_DIR, 'guoqiao_shu2.json')
parser = argparse.ArgumentParser(description='过桥大冒险配置生成脚本')
parser.add_argument('--input', help='动态题目 JSON。题目图片/音频/句子/选项必须从这里读取')
parser.add_argument('--template', default=DEFAULT_REF_PATH, help='模板/参考配置 JSON')
parser.add_argument('--output', default=DEFAULT_OUT_FILE, help='输出配置 JSON')
parser.add_argument('--meta', help='输出 build meta JSON')
ARGS = parser.parse_args()
REF_PATH = ARGS.template
OUT_FILE = ARGS.output
os.makedirs(OUT_DIR, exist_ok=True)

# ──────────────────────────────────────────────
# 题目数据（国际level2过桥大冒险暑2，6关）
# sentence: 完整句子
# parts: 顺序排列的词/组，type=fixed(固定词) 或 drag(拖拽槽)
# options: 选项文字列表（正确答案必须包含在内）
# quiz_img: 题目配图 URL
# audio: 点击选择 播放态音频 URL（暂无则留空）
# ──────────────────────────────────────────────
IMG_BASE = 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/'

LEVELS = [
    {
        'sentence': 'Kuan enjoys riding bikes.',
        'quiz_img': IMG_BASE + '1ddde668f36606fa4ea280bb2121058e.png',
        'audio': '',
        'parts': [
            {'type': 'fixed', 'text': 'Kuan'},
            {'type': 'drag',  'text': 'enjoys'},
            {'type': 'fixed', 'text': 'riding'},
            {'type': 'fixed', 'text': 'bikes.'},
        ],
        'options': ['enjoy', 'enjoys'],
    },
    {
        'sentence': 'We like playing outside.',
        'quiz_img': IMG_BASE + '32920ae7b7919ece73dc0b47f5640990.png',
        'audio': '',
        'parts': [
            {'type': 'fixed', 'text': 'We'},
            {'type': 'drag',  'text': 'like'},
            {'type': 'fixed', 'text': 'playing'},
            {'type': 'fixed', 'text': 'outside.'},
        ],
        'options': ['likes', 'like'],
    },
    {
        'sentence': 'He loves drawing films.',
        'quiz_img': IMG_BASE + '5e009a2fb621003122587940e9e2b5d4.png',
        'audio': '',
        'parts': [
            {'type': 'fixed', 'text': 'He'},
            {'type': 'drag',  'text': 'loves'},
            {'type': 'drag',  'text': 'drawing'},
            {'type': 'fixed', 'text': 'films.'},
        ],
        'options': ['loves', 'love', 'draw', 'drawing'],
    },
    {
        'sentence': "They don't enjoy staying inside.",
        'quiz_img': IMG_BASE + '8a0debb509dab581883ee51fb9cadf72.png',
        'audio': '',
        'parts': [
            {'type': 'fixed', 'text': 'They'},
            {'type': 'drag',  'text': "don't enjoy"},
            {'type': 'drag',  'text': 'staying'},
            {'type': 'fixed', 'text': 'inside.'},
        ],
        'options': ["doesn't enjoy", "don't enjoy", 'stay', 'staying'],
    },
    {
        'sentence': 'Max likes collecting stickers.',
        'quiz_img': IMG_BASE + '62fd937dde1a2a2dbabec8a8958a3aba.png',
        'audio': '',
        'parts': [
            {'type': 'drag', 'text': 'Max'},
            {'type': 'drag', 'text': 'likes'},
            {'type': 'drag', 'text': 'collecting stickers.'},
        ],
        'options': ['Max', 'likes', 'collecting stickers.', 'like'],
    },
    {
        'sentence': "They don't like staying inside.",
        'quiz_img': IMG_BASE + '63de93d3f11271b1152fa1e1ae4c18e9.png',
        'audio': '',
        'parts': [
            {'type': 'drag', 'text': 'They'},
            {'type': 'drag', 'text': "don't"},
            {'type': 'drag', 'text': 'like'},
            {'type': 'drag', 'text': 'staying inside.'},
        ],
        'options': ['They', "don't", 'like', 'staying inside.', 'likes'],
    },
]


def load_dynamic_levels(path):
    with open(path, encoding='utf-8') as f:
        payload = json.load(f)
    levels = payload.get('levels', payload.get('questions')) if isinstance(payload, dict) else payload
    if not isinstance(levels, list) or not levels:
        raise ValueError('input must be a non-empty list or an object with levels/questions')
    for index, lv in enumerate(levels, 1):
        prefix = f'L{index}'
        for key in ('sentence', 'quiz_img', 'audio', 'parts', 'options'):
            if key not in lv:
                raise ValueError(f'{prefix}: missing required field: {key}')
        if not lv.get('quiz_img'):
            raise ValueError(f'{prefix}: quiz_img is required for dynamic input')
        if not lv.get('audio'):
            raise ValueError(f'{prefix}: audio is required for dynamic input')
        drag_parts = [p for p in lv.get('parts', []) if p.get('type') == 'drag']
        if not drag_parts:
            raise ValueError(f'{prefix}: at least one drag part is required')
        if not lv.get('options'):
            raise ValueError(f'{prefix}: options cannot be empty')
        missing = sorted(set(p.get('text') for p in drag_parts) - set(lv.get('options', [])))
        if missing:
            raise ValueError(f'{prefix}: drag answers missing from options: {missing}')
    return levels


if ARGS.input:
    LEVELS = load_dynamic_levels(ARGS.input)

# ──────────────────────────────────────────────
# 辅助函数
# ──────────────────────────────────────────────
def new_uuid():
    return f'gamenext_component_uuid_{uuid.uuid4()}'

def new_level_uuid():
    return f'gamenext_level_uuid_{uuid.uuid4()}'

def get_comp(comps, name):
    for c in comps:
        if c['component_data']['name'] == name:
            return c
    return None

def get_state(comp, state='default'):
    for s in comp['component_data']['states']:
        if s['state'] == state:
            return s
    return None

def word_width(text, base_w=166):
    """根据文字长度计算组件宽度"""
    L = len(text)
    if L <= 3:  return 120
    if L <= 5:  return 166
    if L <= 8:  return 200
    if L <= 12: return 280
    if L <= 16: return 360
    return 440

def layout_row(parts, gap=8):
    """
    计算行内各部件的中心 x 坐标（居中对齐，行中心=0）。
    parts: list of (width,)
    返回: list of center_x
    """
    total = sum(w for w in parts) + gap * (len(parts) - 1)
    left = -total / 2
    xs = []
    cur = left
    for w in parts:
        xs.append(cur + w / 2)
        cur += w + gap
    return xs

# ──────────────────────────────────────────────
# 加载参考配置
# ──────────────────────────────────────────────
if not os.path.exists(REF_PATH):
    # Fallback: try to decode from RTF inline
    sys.exit(f'ERROR: 参考配置未找到: {REF_PATH}\n请先运行 RTF 解析步骤。')

with open(REF_PATH) as f:
    ref = json.load(f)

ref_lvl0 = ref['game'][0]['components']   # 参考关卡0（5槽）的组件列表

# 获取固定骨架组件的模板
tmpl_bg          = get_comp(ref_lvl0, '背景')
tmpl_quiz_img    = get_comp(ref_lvl0, '题目配图')
tmpl_level_num   = get_comp(ref_lvl0, '关卡数组件')
tmpl_speaker     = get_comp(ref_lvl0, '喇叭低层级')
tmpl_deer        = get_comp(ref_lvl0, '小鹿开车')
tmpl_click       = get_comp(ref_lvl0, '点击选择')
tmpl_juhao       = get_comp(ref_lvl0, '句号')
tmpl_jiedian     = get_comp(ref_lvl0, '节点')

# 拖拽放置区模板（用于 clone）
tmpl_slot  = get_comp(ref_lvl0, '拖拽放置区 1')
if not tmpl_slot:
    tmpl_slot = next(c for c in ref_lvl0 if '拖拽放置区' in c['component_data']['name'])

# 桥墩（带文字）模板
tmpl_pillar       = next((c for c in ref_lvl0 if '桥墩' in c['component_data']['name']
                          and 'space' not in c['component_data']['name']
                          and get_state(c) and get_state(c)['source'].get('MLabel')), None)
# 桥墩space模板
tmpl_space        = next((c for c in ref_lvl0 if '桥墩 space' in c['component_data']['name']
                          or ('桥墩' in c['component_data']['name'] and 'space' in c['component_data']['name'])), None)

# 砖块掉落模板
tmpl_brick        = next((c for c in ref_lvl0 if '砖块掉落' in c['component_data']['name']), None)

# 选项模板
tmpl_option       = next((c for c in ref_lvl0 if c['component_data']['name'].startswith('选项')), None)

# ──────────────────────────────────────────────
# 组件生成函数
# ──────────────────────────────────────────────
BRIDGE_Y      = -56    # 桥面行 Y
OPTION_Y      = -440   # 选项行 Y
JUHAO_W       = 81
JUHAO_H       = 128

# 悬崖桥区固定边界（横向填满）
BRIDGE_LEFT   = -643   # 桥区最左端（组件左边缘）
BRIDGE_RIGHT  =  548   # 桥区最右端（组件右边缘）
BRIDGE_TOTAL  = BRIDGE_RIGHT - BRIDGE_LEFT  # 1191

# 选项区：总宽（选项均匀分布在此范围内）
OPTION_AREA_W = 1200   # 选项行可用总宽

# 题目配图 Y 坐标（固定）
QUIZ_IMG_Y      = 355
QUIZ_IMG_X_WITH_AUDIO = 91.49  # 有音频时偏右，给喇叭留空间
QUIZ_IMG_X_NO_AUDIO   = 0.0    # 无音频时居中

def make_slot(name, x, w, answer_tag, zidx=5):
    """生成拖拽放置区组件（deepcopy 模板，替换变量）"""
    c = copy.deepcopy(tmpl_slot)
    c['component_data']['id']     = new_uuid()
    c['component_data']['name']   = name
    c['component_data']['zIndex'] = zidx
    # 更新 itemList（正确答案）
    c['component_data']['components']['tools']['LDragPlace']['itemList'] = [answer_tag]
    # 更新所有 state 的 transform
    for st in c['component_data']['states']:
        t = st['transform']
        t['x'] = x; t['w'] = w
    return c

def make_pillar(name, x, w, text, zidx=4, font_size=None):
    """生成桥墩（固定词）组件"""
    if tmpl_pillar:
        c = copy.deepcopy(tmpl_pillar)
    else:
        c = copy.deepcopy(tmpl_space)
    c['component_data']['id']     = new_uuid()
    c['component_data']['name']   = name
    c['component_data']['zIndex'] = zidx
    for st in c['component_data']['states']:
        t = st['transform']
        t['x'] = x; t['w'] = w
        if 'MLabel' in st.get('source', {}):
            st['source']['MLabel']['value'] = text.rstrip('.')  # 句号由独立句号组件承担
            if font_size is not None:
                st['source']['MLabel']['fontSize'] = font_size
    return c

def make_space_pillar(name, x, zidx=4):
    """生成桥墩space（词间隔）"""
    c = copy.deepcopy(tmpl_space if tmpl_space else tmpl_pillar)
    c['component_data']['id']     = new_uuid()
    c['component_data']['name']   = name
    c['component_data']['zIndex'] = zidx
    for st in c['component_data']['states']:
        t = st['transform']
        t['x'] = x; t['w'] = 16   # 窄间隔
        if 'MLabel' in st.get('source', {}):
            st['source']['MLabel']['value'] = ''
    return c

def make_brick(name, x, slot_id, zidx=17):
    """生成砖块掉落，event 绑定到对应 slot 的 UUID"""
    c = copy.deepcopy(tmpl_brick)
    c['component_data']['id']     = new_uuid()
    c['component_data']['name']   = name
    c['component_data']['zIndex'] = zidx
    # 更新位置
    for st in c['component_data']['states']:
        st['transform']['x'] = x
    # 更新 event.value source
    for ev in c['component_data']['event']['value']:
        if ev.get('action') == 'changeState' and ev.get('event') == 'wrong':
            ev['source'] = slot_id
    return c

def make_option(name, x, w, text, tag, zidx=10, font_size=None):
    """生成选项（可拖拽）"""
    c = copy.deepcopy(tmpl_option)
    c['component_data']['id']     = new_uuid()
    c['component_data']['name']   = name
    c['component_data']['zIndex'] = zidx
    c['component_data']['components']['tools']['MDraggable']['tag'] = tag
    for st in c['component_data']['states']:
        t = st['transform']
        t['x'] = x; t['w'] = w
        if 'MLabel' in st.get('source', {}):
            display_text = text.rstrip('.')   # 桥墩已带句号，选项显示时去掉末尾句点
            st['source']['MLabel']['value'] = display_text
            if 'string' in st['source']['MLabel']:
                st['source']['MLabel']['string'] = display_text
            if font_size is not None:
                st['source']['MLabel']['fontSize'] = font_size
    return c

# ──────────────────────────────────────────────
# 关卡构建
# ──────────────────────────────────────────────
def build_level(lvl_data, level_idx, total_levels):
    """构建单个关卡 JSON"""
    parts       = lvl_data['parts']
    options     = lvl_data['options']
    quiz_img    = lvl_data.get('quiz_img', '')
    audio_url   = lvl_data.get('audio', '')

    drag_parts  = [p for p in parts if p['type'] == 'drag']
    n_slots     = len(drag_parts)
    n_opts      = len(options)

    # 1. 计算桥面各部件宽度，然后等比拉伸填满桥区（BRIDGE_LEFT ~ BRIDGE_RIGHT）
    # 1. 统一宽度策略：
    #    - 固定词（桥墩）按自然宽度，再等比缩放填满桥区
    #    - 拖拽放置区（槽）全部取同一宽度 = 所有槽自然宽度的最大值（缩放后），避免提示
    GAP_BRIDGE = 0   # 桥墩/槽之间紧贴，无间隔
    raw_widths = [word_width(p['text']) for p in parts]
    n_parts = len(raw_widths)

    # 先确定"统一槽宽"：取所有 drag part 自然宽度的最大值
    raw_slot_w = max((raw_widths[i] for i, p in enumerate(parts) if p['type'] == 'drag'), default=166)
    # 用统一槽宽替换所有 drag part 的原始宽度
    raw_widths_unified = [raw_slot_w if p['type'] == 'drag' else raw_widths[i]
                          for i, p in enumerate(parts)]

    # 等比整体缩放填满桥区（gap=0，直接按总宽比例）
    raw_total = sum(raw_widths_unified)
    scale = BRIDGE_TOTAL / raw_total if raw_total > 0 else 1.0
    part_widths = [max(60, w * scale) for w in raw_widths_unified]

    # 桥面行 x 坐标（紧贴布局，从 BRIDGE_LEFT 开始）
    part_xs = []
    cur = BRIDGE_LEFT
    for w in part_widths:
        part_xs.append(cur + w / 2)
        cur += w  # gap=0 紧贴

    # 2. 选项宽度 = 缩放后的统一槽宽（所有选项等宽，不暴露哪个选项对应哪个槽）
    unified_slot_w = next((part_widths[i] for i, p in enumerate(parts) if p['type'] == 'drag'), 166)
    opt_widths = [unified_slot_w] * len(options)

    # 3. 自适应字号：让最长文本在 unified_slot_w 内不换行
    #    英文粗体字符宽度 ≈ fontSize * 0.55（保守估计）
    FONT_DEFAULT = 51
    FONT_MIN     = 35
    CHAR_W_FACTOR = 0.55   # 每字符宽度系数
    all_texts = [p['text'] for p in parts] + list(options)
    max_chars = max(len(t) for t in all_texts) if all_texts else 1
    computed_font = int(unified_slot_w / (max_chars * CHAR_W_FACTOR))
    level_font_size = max(FONT_MIN, min(FONT_DEFAULT, computed_font))

    # 选项间距自适应
    n_opts_actual = len(opt_widths)
    if n_opts_actual <= 1:
        opt_gap = 16
    else:
        total_opt_w = sum(opt_widths)
        opt_gap = max(16, min(100, (OPTION_AREA_W - total_opt_w) / (n_opts_actual - 1)))
    opt_xs = layout_row(opt_widths, gap=opt_gap)

    # 3. 构建桥面组件列表
    bridge_comps = []
    slot_comps   = []   # (slot_component, x) for brick binding
    drag_idx     = 0
    for i, (p, x, w) in enumerate(zip(parts, part_xs, part_widths)):
        if p['type'] == 'fixed':
            bridge_comps.append(make_pillar(f'桥墩{i+1}', x, w, p['text'], font_size=level_font_size))
        else:
            slot = make_slot(f'拖拽放置区 {drag_idx+1}', x, w, p['text'])
            bridge_comps.append(slot)
            slot_comps.append((slot, x))
            drag_idx += 1

    # 4. 砖块掉落（每个 slot 对应一个）
    brick_comps = []
    for i, (slot, x) in enumerate(slot_comps):
        slot_id = slot['component_data']['id']
        brick_comps.append(make_brick(f'砖块掉落 {i+1}', x, slot_id))

    # 5. 选项
    opt_comps = []
    for i, (text, x, w) in enumerate(zip(options, opt_xs, opt_widths)):
        opt_comps.append(make_option(f'选项{i+1}', x, w, text, text, font_size=level_font_size))

    # 6. 固定组件（deepcopy + 更新 id）
    def clone_fixed(tmpl, new_name=None):
        if tmpl is None:
            return None
        c = copy.deepcopy(tmpl)
        c['component_data']['id'] = new_uuid()
        if new_name:
            c['component_data']['name'] = new_name
        return c

    bg_c      = clone_fixed(tmpl_bg)
    quiz_c    = clone_fixed(tmpl_quiz_img)
    lvnum_c   = clone_fixed(tmpl_level_num)
    speaker_c = clone_fixed(tmpl_speaker) if audio_url else None
    deer_c    = clone_fixed(tmpl_deer)
    click_c   = clone_fixed(tmpl_click) if audio_url else None
    juhao_c   = clone_fixed(tmpl_juhao)
    jiedian_c = clone_fixed(tmpl_jiedian)

    # 更新题目配图 URL、尺寸（447×297）和 x 坐标（无音频时居中）
    QUIZ_IMG_W, QUIZ_IMG_H = 447, 297
    quiz_x = QUIZ_IMG_X_NO_AUDIO if not audio_url else QUIZ_IMG_X_WITH_AUDIO
    if quiz_c and quiz_img:
        for st in quiz_c['component_data']['states']:
            if 'MSprite' in st.get('source', {}):
                st['source']['MSprite']['value'] = quiz_img
            t = st.get('transform', {})
            t['w'] = QUIZ_IMG_W
            t['h'] = QUIZ_IMG_H
            t['x'] = quiz_x
            t['y'] = QUIZ_IMG_Y

    # 更新关卡数显示
    if lvnum_c:
        for st in lvnum_c['component_data']['states']:
            if 'MRichText' in st.get('source', {}):
                st['source']['MRichText']['value'] = f'{level_idx+1}/{total_levels}'

    # 更新点击选择音频
    if click_c and audio_url:
        for st in click_c['component_data']['states']:
            if 'MAudio' in st.get('source', {}):
                st['source']['MAudio']['value'] = audio_url

    # 7. 拼装组件列表（顺序：背景 → 题目配图 → 关卡数 → 喇叭 → 小鹿 → 点击选择
    #                   → 拖拽放置区 → 桥墩（fixed） → 砖块掉落 → 句号 → 节点 → 选项）
    all_comps = []
    for c in [bg_c, quiz_c, lvnum_c, speaker_c, deer_c, click_c]:
        if c: all_comps.append(c)
    # 桥面组件（slot + fixed pillar 混合，已按顺序）
    all_comps.extend(bridge_comps)
    # 砖块掉落
    all_comps.extend(brick_comps)
    # 句号（放在最后一个桥面组件右侧）
    if juhao_c:
        last_x = part_xs[-1] + part_widths[-1] / 2
        for st in juhao_c['component_data']['states']:
            st['transform']['x'] = last_x + JUHAO_W / 2 + 8
        all_comps.append(juhao_c)
    # 节点
    if jiedian_c:
        all_comps.append(jiedian_c)
    # 选项
    all_comps.extend(opt_comps)

    # 8. 构建 level 骨架（直接 deepcopy 参考关卡，替换 components 和 id）
    level = copy.deepcopy(ref['game'][0])
    level['id']         = new_level_uuid()
    level['components'] = all_comps
    # title/video/transition/levelData 原样保留（deepcopy 已处理）

    return level

# ──────────────────────────────────────────────
# 生成完整配置
# ──────────────────────────────────────────────
total = len(LEVELS)
game_levels = [build_level(lvl, i, total) for i, lvl in enumerate(LEVELS)]

result = {
    'meta': copy.deepcopy(ref.get('meta', {})),
    'additional': copy.deepcopy(ref.get('additional', [])),
    'common': copy.deepcopy(ref['common']),
    'components': copy.deepcopy(ref.get('components', [])),
    'game': game_levels
}

with open(OUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f'✅ 生成完成: {OUT_FILE}')
print(f'   关卡数: {len(game_levels)}')
if ARGS.meta:
    meta = {
        'schema': 'coursewaremaker.bridge.build_meta.v1',
        'generator': 'scripts/generate_guoqiao_shu2.py',
        'template': REF_PATH,
        'output': OUT_FILE,
        'question_count': len(LEVELS),
        'levels': [
            {
                'index': i,
                'sentence': lv.get('sentence'),
                'drag_count': sum(1 for p in lv.get('parts', []) if p.get('type') == 'drag'),
                'option_count': len(lv.get('options', [])),
                'quiz_img': lv.get('quiz_img', ''),
                'audio': lv.get('audio', ''),
            }
            for i, lv in enumerate(LEVELS, 1)
        ],
    }
    os.makedirs(os.path.dirname(os.path.abspath(ARGS.meta)), exist_ok=True)
    with open(ARGS.meta, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
for i, lvl in enumerate(game_levels):
    comps = lvl['components']
    n_slots  = sum(1 for c in comps if '拖拽放置区' in c['component_data']['name'])
    n_bricks = sum(1 for c in comps if '砖块掉落'   in c['component_data']['name'])
    n_opts   = sum(1 for c in comps if c['component_data']['name'].startswith('选项'))
    # Verify text
    texts = []
    for c in comps:
        if '桥墩' in c['component_data']['name'] and 'space' not in c['component_data']['name']:
            s = next((st for st in c['component_data']['states'] if st['state']=='default'), None)
            if s and s['source'].get('MLabel', {}).get('value'):
                texts.append(f"[桥墩]{s['source']['MLabel']['value']!r}")
        if '拖拽放置区' in c['component_data']['name']:
            items = c['component_data']['components']['tools']['LDragPlace']['itemList']
            texts.append(f"[槽]{items}")
    print(f'   L{i+1}: {n_slots}槽, {n_bricks}砖块, {n_opts}选项 | {texts}')
