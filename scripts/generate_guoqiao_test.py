#!/usr/bin/env python3
"""
生成《过桥大冒险test》配置
基于表格数据（单词拼拼乐测试），使用过桥大冒险原始资源
"""
import json, copy, uuid, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ─── 参考配置 ───────────────────────────────────────────────────────────────
REF = os.path.join(BASE, 'output/guoqiao_configs/87ddb0a3-ea04-11f0-9165-0e324dbd00ee.json')
SPELLING_REF = os.path.join(BASE, 'reference_configs/spelling_validation_ref.json')
OUT = os.path.join(BASE, 'output/guoqiao_test/guoqiao_test.json')

os.makedirs(os.path.dirname(OUT), exist_ok=True)

with open(REF) as f: ref = json.load(f)
with open(SPELLING_REF) as f: sref = json.load(f)

COS = 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/'

# ─── 从参考配置提取原始资源 ─────────────────────────────────────────────────
def get_comp(comps, name_key):
    for c in comps:
        if name_key in c['component_data']['name']:
            return c
    return None

def get_state(cd, state='default'):
    for s in cd.get('states', []):
        if s.get('state') == state:
            return s
    return {}

ref_lvl0 = ref['game'][0]['components']

# 固定资源URL（从过桥参考）
RES = {
    'bg':        get_state(get_comp(ref_lvl0,'背景')['component_data'])['source']['MSprite']['value'],
    'slot_default': get_state(get_comp(ref_lvl0,'拖拽放置区1')['component_data'])['source']['MSprite']['value'],
    'slot_adsorb':  get_state(get_comp(ref_lvl0,'拖拽放置区1')['component_data'],'adsorb')['source']['MSprite']['value'],
    'slot_adsorbed':get_state(get_comp(ref_lvl0,'拖拽放置区1')['component_data'],'adsorbed')['source']['MSprite']['value'],
    'slot_wrong':   get_state(get_comp(ref_lvl0,'拖拽放置区1')['component_data'],'wrong')['source']['MSprite']['value'],
    'pillar':    get_state(get_comp(ref_lvl0,'桥墩2')['component_data'])['source']['MSprite']['value'],
    'option_bg': get_state(get_comp(ref_lvl0,'选项1')['component_data'])['source']['MSprite']['value'],
    'loudspeaker_default': get_state(get_comp(ref_lvl0,'喇叭低层级')['component_data'])['source']['MSprite']['value'],
    'level_num': get_state(get_comp(ref_lvl0,'关卡数组件')['component_data'])['source']['MSprite']['value'],
    'period':    get_state(get_comp(ref_lvl0,'句号')['component_data'])['source']['MSprite']['value'],
}

# Spine组件（直接从参考整体拷贝）
SPINE_NAMES = ['小鹿开车', '点击选择', '砖块掉落']

# ─── 从 spelling_validation_ref 提取每关的题目配图和音频 ─────────────────────
# 题目配图：spelling ref 中 "节点_37" 每关不同图片
# 音频：spelling ref 中 "喇叭" clickDown 状态
def _extract_spelling_resources():
    quiz_imgs = []
    audios = []
    for gi, game in enumerate(sref.get('game', [])):
        comps = game['components']
        # 题目配图
        node37 = get_comp(comps, '节点_37')
        img = ''
        if node37:
            for st in node37['component_data'].get('states', []):
                if st.get('state') == 'default':
                    img = st.get('source', {}).get('MSprite', {}).get('value', '')
                    break
        quiz_imgs.append(img)
        # 音频
        loudspeaker = get_comp(comps, '喇叭')
        audio = ''
        if loudspeaker:
            for st in loudspeaker['component_data'].get('states', []):
                if st.get('state') == 'clickDown':
                    audio = st.get('source', {}).get('MAudio', {}).get('value', '')
                    break
        audios.append(audio)
    return quiz_imgs, audios

QUIZ_IMGS, AUDIOS = _extract_spelling_resources()

def _get_img_sizes(urls):
    """获取图片原始尺寸列表，失败时返回 (448, 297) 作为默认值"""
    import urllib.request, io
    sizes = []
    try:
        from PIL import Image
    except ImportError:
        return [(448, 297)] * len(urls)
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = resp.read()
            img = Image.open(io.BytesIO(data))
            sizes.append((img.size[0], img.size[1]))
        except Exception:
            sizes.append((448, 297))
    return sizes

QUIZ_IMG_SIZES = _get_img_sizes(QUIZ_IMGS)

# ─── 表格数据 ────────────────────────────────────────────────────────────────
# type: 'drag'=拖拽放置区, 'space'=英语空格(窄桥墩), 'fixed'=固定桥墩
LEVELS = [
    {
        'phrase': 'make a snowman',
        'positions': [
            {'type':'drag',  'text':'m'},
            {'type':'drag',  'text':'ake'},
            {'type':'space'},
            {'type':'fixed', 'text':'a'},
            {'type':'space'},
            {'type':'drag',  'text':'sn'},
            {'type':'drag',  'text':'ow'},
            {'type':'drag',  'text':'man'},
        ],
        'options': ['sn','ake','m','ow','man'],
    },
    {
        'phrase': 'clean the room',
        'positions': [
            {'type':'drag',  'text':'cl'},
            {'type':'drag',  'text':'ean'},
            {'type':'space'},
            {'type':'drag',  'text':'the'},
            {'type':'space'},
            {'type':'drag',  'text':'r'},
            {'type':'drag',  'text':'oom'},
        ],
        'options': ['ean','oom','the','cl','r'],
    },
    {
        'phrase': 'fat',
        'positions': [
            {'type':'drag',  'text':'f'},
            {'type':'drag',  'text':'a'},
            {'type':'drag',  'text':'t'},
        ],
        'options': ['t','a','f'],
    },
]

# ─── 坐标计算 ────────────────────────────────────────────────────────────────
BRIDGE_CENTER_X = -25
BRIDGE_Y = -56
SPACE_W = 70
PERIOD_W = 81

def calc_bridge_layout(positions):
    """计算每个桥位的 (x, w) 坐标"""
    n_std = sum(1 for p in positions if p['type'] in ('drag','fixed'))
    n_sp  = sum(1 for p in positions if p['type'] == 'space')
    std_w = round((1138 - n_sp * SPACE_W) / n_std)
    
    widths = []
    for p in positions:
        if p['type'] == 'space':
            widths.append(SPACE_W)
        else:
            widths.append(std_w)
    
    total = sum(widths)
    left_edge = BRIDGE_CENTER_X - total / 2
    
    centers = []
    x = left_edge
    for w in widths:
        centers.append(round(x + w / 2))
        x += w
    
    return list(zip(centers, widths)), std_w

def option_positions(n_opts, opt_w):
    """选项在桥上方居中排列，y=-440"""
    OPT_Y = -440
    GAP = 20
    total = n_opts * opt_w + (n_opts - 1) * GAP
    left = -total / 2
    pos = []
    for i in range(n_opts):
        pos.append(round(left + i * (opt_w + GAP) + opt_w / 2))
    return pos, OPT_Y

# ─── UUID helper ─────────────────────────────────────────────────────────────
def new_uuid():
    return f'gamenext_component_uuid_{uuid.uuid4()}'

# ─── 构建组件 ─────────────────────────────────────────────────────────────────
DISPATCH_FUN_LIST = [
    {'allowEventName': ['all'], 'label': '显示', 'name': 'onShow'},
    {'allowEventName': ['all'], 'label': '隐藏', 'name': 'onHide'},
    {'allowEventName': ['all'], 'label': '旋转', 'name': 'onRotated'},
]
EVENT_MAP = [{'label': '点击', 'name': 'click', 'sys': False}]

def make_jump():
    return {'canEdit': True, 'duration': 0, 'opened': 0, 'to': '', 'type': ''}

def make_active(show=True, can_edit=True):
    return {'canEdit': can_edit, 'switch': not show, 'value': 'show' if show else 'hide'}

def make_sprite_comp(name, x, y, w, h, img, zidx=1, states=None, extra_components=None):
    """创建一个基础 MSprite 组件"""
    base_state = {
        'groupKey': '', 'state': 'default', 'label': '默认', 'notDelete': False,
        'transform': {'x': x, 'y': y, 'w': w, 'h': h, 'scaleX':1,'scaleY':1,'rot':0,'editRot':False,'anchorX':0.5,'anchorY':0.5},
        'source': {'MSprite': {'key':'','value': img}},
        'jump': make_jump(),
        'active': make_active(show=True),
    }
    if states is None:
        states = [base_state]
    
    comps = {
        'tools': {},
        'source': {'MSprite': 1},
        'lockState': {'state':False,'componentId':'','componentName':'','componentState':''},
        'judgeRules': {'forbidIfCorrect':False,'inAnswerPool':True},
        'webEditorCustomInfo': {'chain':'','isAnswerComponent':False,'isJudgeComponent':False},
    }
    if extra_components:
        comps.update(extra_components)
    
    return {
        'component_data': {
            'id': new_uuid(),
            'edit_description': '',
            'component_id': '',
            'name': name,
            'zIndex': zidx,
            'base': 'MSprite',
            'components': comps,
            'custom': [],
            'edit': {'baseNotChange':False,'curState':'default','lock':False},
            'event': {'dispatchFunList': DISPATCH_FUN_LIST, 'eventMap': EVENT_MAP, 'value':[]},
            'state_group': [],
            'states': states,
        },
        'component_id': '',
        'component_name': '节点',
        'component_url': '',
        'index': 0,
        'name': 'BaseComponent',
        'version': '0.0.0',
    }

def make_drag_slot(name, x, y, w, h, item_text, zidx=5):
    """创建拖拽放置区"""
    def mk_st(state, img, lbl='默认'):
        return {
            'groupKey':'','state':state,'label':lbl,'notDelete':False,
            'transform':{'x':x,'y':y,'w':w,'h':h,'scaleX':1,'scaleY':1,'rot':0,'editRot':False,'anchorX':0.5,'anchorY':0.5},
            'source':{'MSprite':{'key':'','value':img}},
            'jump': make_jump(),
            'active': make_active(show=True)
        }
    states = [
        mk_st('default',  RES['slot_default'], '默认'),
        mk_st('adsorb',   RES['slot_adsorb'],  '吸附中'),
        mk_st('adsorbed', RES['slot_adsorbed'],'已吸附'),
        mk_st('wrong',    RES['slot_wrong'],   '错误'),
    ]
    extra = {
        'tools': {
            'LDragPlace': {
                'allowRepeat': False,
                'itemList': [item_text],
                'needSamePosition': False,
                'returnWhenWrong': True,
            }
        }
    }
    c = make_sprite_comp(name, x, y, w, h, RES['slot_default'], zidx, states, extra)
    c['component_data']['components']['tools'] = extra['tools']
    return c

def make_pillar(name, x, y, w, h, text='', zidx=5):
    """创建固定桥墩（可选显示文字）"""
    def mk_st(state):
        st = {
            'groupKey':'','state':state,'label':'默认','notDelete':False,
            'transform':{'x':x,'y':y,'w':w,'h':h,'scaleX':1,'scaleY':1,'rot':0,'editRot':False,'anchorX':0.5,'anchorY':0.5},
            'source':{'MSprite':{'key':'','value':RES['pillar']}},
            'jump': make_jump(),
            'active': make_active(show=True)
        }
        if text:
            st['source']['MLabel'] = {
                'alignType':'center','closeable':True,'color':'#FFFFFF',
                'fontFamily':'FZCuYuan-M03S','fontSize':51,'interval':[0,0,0,0,0],
                'isBold':False,'isItalic':False,'isUnderline':False,'value':text,'string':text
            }
        return st
    return make_sprite_comp(name, x, y, w, h, RES['pillar'], zidx, [mk_st('default')])

def make_space_pillar(name, x, y, zidx=5):
    """创建空格桥墩（窄，透明/装饰）"""
    w, h = SPACE_W, 129
    return make_pillar(name, x, y, w, h, '', zidx)

def make_option(name, x, y, opt_w, text, zidx=10):
    """创建选项（拖拽物品）"""
    def mk_st(state, lbl):
        return {
            'groupKey':'','state':state,'label':lbl,'notDelete':False,
            'transform':{'x':x,'y':y,'w':opt_w,'h':129,'scaleX':1,'scaleY':1,'rot':0,'editRot':False,'anchorX':0.5,'anchorY':0.5},
            'source':{
                'MSprite':{'key':'','value':RES['option_bg']},
                'MLabel':{
                    'alignType':'center','closeable':True,'color':'#FFFFFF',
                    'fontFamily':'FZCuYuan-M03S','fontSize':51,'interval':[0,0,0,0,0],
                    'isBold':False,'isItalic':False,'isUnderline':False,
                    'value':text,'string':text
                }
            },
            'jump': make_jump(),
            'active': make_active(show=True)
        }
    states = [mk_st('default','默认'), mk_st('placed','已放置'), mk_st('dragging','拖拽中')]
    extra = {
        'tools': {
            'MDraggable': {
                'adsorptionDistance': 60,
                'canDragBack': True,
                'returnWhenWrong': True,
                'tag': text,
            }
        }
    }
    c = make_sprite_comp(name, x, y, opt_w, 129, RES['option_bg'], zidx, states, extra)
    c['component_data']['components']['tools'] = extra['tools']
    return c

def copy_spine_comp(ref_comps, name_key):
    """从参考配置复制Spine组件"""
    c = get_comp(ref_comps, name_key)
    if c:
        return copy.deepcopy(c)
    return None

# ─── 砖块掉落（每个拖拽槽对应一个）────────────────────────────────────────────
def make_brick_fall(name, x, y, ref_comps):
    """复制砖块掉落Spine，更新坐标"""
    c = copy.deepcopy(get_comp(ref_comps, '砖块掉落'))
    if not c:
        return None
    cd = c['component_data']
    cd['name'] = name
    cd['id'] = new_uuid()
    # 更新所有state的坐标
    for st in cd.get('states', []):
        t = st.get('transform', {})
        t['x'] = x
        t['y'] = y
    return c

# ─── 构建每个关卡 ─────────────────────────────────────────────────────────────
def build_level(lvl_data, lvl_idx, ref_comps):
    phrase = lvl_data['phrase']
    positions = lvl_data['positions']
    options = lvl_data['options']
    audio_url = AUDIOS[lvl_idx]
    
    layout, std_w = calc_bridge_layout(positions)
    opt_w = min(std_w, 286)
    opt_xs, opt_y = option_positions(len(options), opt_w)
    
    comps = []
    
    # 1. 背景
    bg = make_sprite_comp('背景', 0, 0, 2048, 1152, RES['bg'], zidx=0)
    comps.append(bg)
    
    # 2. 题目配图（从 spelling_validation_ref 按关卡取对应图片，使用图片原始尺寸）
    quiz_img_url = QUIZ_IMGS[lvl_idx] if lvl_idx < len(QUIZ_IMGS) else ''
    quiz_w, quiz_h = QUIZ_IMG_SIZES[lvl_idx] if lvl_idx < len(QUIZ_IMG_SIZES) else (448, 297)
    qimg = make_sprite_comp('题目配图', 91, 355, quiz_w, quiz_h, quiz_img_url, zidx=2)
    comps.append(qimg)
    
    # 3. 关卡数组件
    total_levels = 3  # 总关卡数（后续可从参数传入）
    lvl_num = make_sprite_comp('关卡数组件', 744, 484, 322, 139, RES['level_num'], zidx=3)
    # 补充 MRichText 富文本配置（显示 "当前关/总关" 的关卡数字）
    for st in lvl_num['component_data']['states']:
        if st.get('state') == 'default':
            st['source']['MRichText'] = {
                'alignType': 'center',
                'closeable': True,
                'color': '#000000',
                'colorLeft': '#FF8600',
                'colorRight': '#7B7D8F',
                'fontFamily': 'FZCuYuan-M03S',
                'fontSize': 50,
                'interval': [10, 0, 0, -100, 0],
                'value': f'{lvl_idx + 1}/{total_levels}'
            }
            st['source']['MSprite']['key'] = '2'
    # 关卡数组件专属字段
    lvl_num['component_data']['components']['tools'] = {
        'LevelNumber': {'subjectConfig': {'subjectChoose': 'gs'}}
    }
    lvl_num['component_data']['edit'] = {
        'baseNotChange': False,
        'curState': 'default',
        'isLvNumComponent': True,
        'lock': True
    }
    comps.append(lvl_num)
    
    # 4. 喇叭
    loudspeaker_ref = get_comp(ref_comps, '喇叭低层级')
    if loudspeaker_ref:
        loudspeaker = copy.deepcopy(loudspeaker_ref)
        loudspeaker['component_data']['id'] = new_uuid()
        loudspeaker['component_data']['name'] = '喇叭低层级'
        # 替换音频
        if audio_url:
            for st in loudspeaker['component_data'].get('states', []):
                if st.get('state') == 'clickDown':
                    if 'MAudio' in st.get('source', {}):
                        st['source']['MAudio']['value'] = audio_url
        comps.append(loudspeaker)
    
    # 5. 小鹿开车 (Spine)
    deer = copy_spine_comp(ref_comps, '小鹿开车')
    if deer:
        deer['component_data']['id'] = new_uuid()
        comps.append(deer)
    
    # 6. 点击选择 (Spine)
    click = copy_spine_comp(ref_comps, '点击选择')
    if click:
        click['component_data']['id'] = new_uuid()
        comps.append(click)
    
    # 7. 桥面组件
    drag_idx = 1
    pillar_idx = 1
    space_idx = 1
    brick_comps = []
    
    for i, (pos, (x, w)) in enumerate(zip(positions, layout)):
        if pos['type'] == 'drag':
            slot = make_drag_slot(f'拖拽放置区{drag_idx}', x, BRIDGE_Y, w, 129, pos['text'], zidx=5)
            comps.append(slot)
            # 砖块掉落
            brick = copy_spine_comp(ref_comps, '砖块掉落')
            if brick:
                brick['component_data']['id'] = new_uuid()
                brick['component_data']['name'] = f'砖块掉落{drag_idx}'
                for st in brick['component_data'].get('states',[]):
                    t = st.get('transform',{})
                    t['x'] = x - 4
                    t['y'] = BRIDGE_Y + 1
                brick_comps.append(brick)
            drag_idx += 1
        elif pos['type'] == 'fixed':
            pillar = make_pillar(f'桥墩{pillar_idx}', x, BRIDGE_Y, w, 129, pos['text'], zidx=5)
            comps.append(pillar)
            pillar_idx += 1
        elif pos['type'] == 'space':
            space = make_space_pillar(f'桥墩space{space_idx}', x, BRIDGE_Y, zidx=4)
            comps.append(space)
            space_idx += 1
    
    comps.extend(brick_comps)
    
    # 8. 句号（最右侧桥板右边，仅多词短语才显示）
    is_sentence = len(phrase.split()) > 1
    rightmost_x = layout[-1][0]
    rightmost_w = layout[-1][1]
    period_x = rightmost_x + rightmost_w / 2 + PERIOD_W / 2 + 5
    period = make_sprite_comp('句号', round(period_x), BRIDGE_Y, PERIOD_W, 128, RES['period'], zidx=5)
    # 句号：多词短语显示，单词隐藏
    for st in period['component_data']['states']:
        if st.get('state') == 'default':
            st['active'] = make_active(show=is_sentence)
    comps.append(period)
    
    # 9. 选项
    node_total_w = len(options) * opt_w + (len(options) - 1) * 20
    node_x = round(-node_total_w/2 + node_total_w/2)  # center=0 + offset
    # 先算节点范围
    node_left = opt_xs[0] - opt_w/2 - 10
    node_right = opt_xs[-1] + opt_w/2 + 10
    node_w = round(node_right - node_left)
    node_cx = round((node_left + node_right) / 2)
    
    node = make_sprite_comp('节点', node_cx, opt_y - 10, node_w, 272, '', zidx=4)
    node['component_data']['base'] = 'MSprite'
    # 节点无图片，source清空
    for st in node['component_data']['states']:
        st['source'] = {}
    comps.append(node)
    
    for i, (text, ox) in enumerate(zip(options, opt_xs)):
        opt = make_option(f'选项{i+1}', ox, opt_y, opt_w, text, zidx=10)
        comps.append(opt)
    
    return {
        'id': f'gamenext_level_uuid_{uuid.uuid4()}',
        'title': {'component_data': {}, 'component_id': '', 'component_url': ''},
        'video': {},
        'transition': {'in': {'name': 'none'}, 'out': {'name': 'none'}},
        'levelData': {
            'autoNextLevel': {'auto': True, 'wait': 4},
            'autoStopLevel': {'auto': False, 'errorCount': 1, 'wait': 0},
            'errorLimit': {'allowErrorCount': 0},
            'failAutoReset': {'auto': False, 'wait': 0},
            'judge': {'autoJudge': 1, 'judgeRule': 1},
            'selectionComponent': {'enabled': False, 'repelCount': 0, 'selections': []},
            'uiConfig': {},
        },
        'components': comps,
    }

# ─── 组装完整配置 ─────────────────────────────────────────────────────────────
ref_comps = ref['game'][0]['components']

result = copy.deepcopy(ref)
result['meta'] = result.get('meta', {})
# 移除多余的 base_info 字段
result['common'].pop('base_info', None)
result['game'] = [
    build_level(lvl, i, ref_comps) for i, lvl in enumerate(LEVELS)
]

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f'✅ 生成完成: {OUT}')
print(f'   关卡数: {len(result["game"])}')
for i, lvl in enumerate(result['game']):
    n_comps = len(lvl['components'])
    n_slots = sum(1 for c in lvl['components'] if '拖拽放置区' in c['component_data']['name'])
    n_opts  = sum(1 for c in lvl['components'] if c['component_data']['name'].startswith('选项'))
    print(f'   关卡{i+1} [{lvl["title"]}]: {n_comps}个组件, {n_slots}槽, {n_opts}选项')
