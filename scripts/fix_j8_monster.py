#!/usr/bin/env python3
"""
Fix J8 Monster config: grandma/grandpa/family content
Structure (from reference): images in 节点 comp[4,5,6], 点击选择 comp[7,8,9] has anwserRadio only (MSprite EMPTY)
level_correct hide state goes on the 节点 whose image matches the AUDIO word
"""
import json
import copy
import uuid

AUDIO_URLS = {
    'grandma': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/audio/345733/2026-04-28/44e084a16490793a402cc2741e8c49e4.mp3',
    'grandpa': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/audio/345733/2026-04-28/2ffa14dcba1d1490ea9599764414683e.mp3',
    'family':  'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/audio/345733/2026-04-28/e2b5423a022cd90d3b75425766a1aa4b.mp3',
}
IMAGE_URLS = {
    'grandma': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-28/89ba4589a07f7b249b3d647fed229499.png',
    'grandpa': 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-28/2547993eae810e417d60f0e9994b6fb2.png',
    'family':  'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-28/a13f187ca89d2551b48b072cc40e50dd.png',
}

# 10 levels: (audio_word, opt_left, opt_center, opt_right, correct_pos_1based)
# Positions by x-coordinate:
#   LEFT(1):   节点(comp[4])      ↔ 点击选择1(comp[9])
#   CENTER(2): 节点_104(comp[6])  ↔ 点击选择2(comp[8])
#   RIGHT(3):  节点_103(comp[5])  ↔ 点击选择3(comp[7])
# correct_pos: 1=left, 2=center, 3=right
LEVELS = [
    ('grandma', 'grandma', 'grandpa', 'family', 1),
    ('grandpa', 'family',  'grandpa', 'grandma', 2),
    ('family',  'grandma', 'grandpa', 'family',  3),
    ('family',  'grandma', 'family',  'grandpa', 2),
    ('grandma', 'grandpa', 'family',  'grandma', 3),
    ('grandpa', 'family',  'grandma', 'grandpa', 3),
    ('grandma', 'grandma', 'grandpa', 'family',  1),
    ('family',  'grandpa', 'family',  'grandma', 2),
    ('grandpa', 'grandma', 'family',  'grandpa', 3),
    ('grandma', 'grandma', 'grandpa', 'family',  1),
]

with open('output/j8_monster_current.json') as f:
    data = json.load(f)

config = json.loads(data['result']['configuration'])
games = config['game']

# Ensure 10 levels
while len(games) < 10:
    new_game = copy.deepcopy(games[-1])
    new_game['id'] = f'gamenext_level_uuid_{uuid.uuid4()}'
    games.append(new_game)

print(f'Total levels: {len(games)}')

for game_idx, (audio_word, opt1, opt2, opt3, correct_idx) in enumerate(LEVELS):
    game = games[game_idx]
    opts = [opt1, opt2, opt3]  # maps to comp[4], comp[5], comp[6] / comp[7], comp[8], comp[9]

    comps = game.get('components', [])

    # Position → (节点 comp_idx, 点击选择 comp_idx)
    # LEFT(1)=节点(4)↔点击选择1(9), CENTER(2)=节点_104(6)↔点击选择2(8), RIGHT(3)=节点_103(5)↔点击选择3(7)
    POS_NODE  = {1: 4, 2: 6, 3: 5}   # position → 节点 comp index
    POS_CLICK = {1: 9, 2: 8, 3: 7}   # position → 点击选择 comp index
    opts_by_pos = {1: opt1, 2: opt2, 3: opt3}  # opts passed as (left, center, right)

    # ── comp[3]: 音频播放按钮 ──────────────────────────────────
    audio_btn = comps[3]
    audio_url = AUDIO_URLS[audio_word]
    states = audio_btn['component_data']['states']

    for s in states:
        if s['state'] == 'clickEnd':
            s.setdefault('source', {})['MAudio'] = {
                'audioType': 'play_audio', 'loop': False, 'loopNum': 1, 'value': audio_url
            }
        elif s['state'] == 'compLoadFinish':
            # 参考配置：所有关卡 compLoadFinish 的 MAudio 均为空
            if 'MAudio' in s.get('source', {}):
                s['source']['MAudio']['value'] = ''
            # 不设置自动跳转
            if 'jump' in s:
                s['jump']['type'] = ''
                s['jump']['to'] = ''
                s['jump']['opened'] = 0

    # ── 节点（底图）: 按视觉位置写入图片 ──────────────────────────
    for pos, opt_word in opts_by_pos.items():
        node_comp = comps[POS_NODE[pos]]
        img_url = IMAGE_URLS[opt_word]
        node_states = node_comp['component_data']['states']

        # Remove existing level_correct
        node_comp['component_data']['states'] = [s for s in node_states if s['state'] != 'level_correct']
        node_states = node_comp['component_data']['states']

        for s in node_states:
            if s['state'] in ('default', 'compLoadFinish'):
                s.setdefault('source', {}).setdefault('MSprite', {})['value'] = img_url

        # Audio-word node gets level_correct hide
        if opt_word == audio_word:
            default_state = next((s for s in node_states if s['state'] == 'default'), {})
            lc_state = {
                "active": {"canEdit": True, "switch": True, "value": "hide"},
                "groupKey": "",
                "jump": {"canEdit": True, "duration": 0, "opened": 0, "to": "", "type": ""},
                "label": "全局正确",
                "notDelete": False,
                "source": {"MSprite": {"key": "", "value": img_url}},
                "state": "level_correct",
                "transform": copy.deepcopy(default_state.get("transform", {}))
            }
            node_comp['component_data']['states'].append(lc_state)

    # ── 点击选择: 按视觉位置写 anwserRadio，清空 MSprite ─────────
    for pos, opt_word in opts_by_pos.items():
        choice_comp = comps[POS_CLICK[pos]]
        is_correct = (pos == correct_idx)
        cd = choice_comp['component_data']
        cd.setdefault('components', {}).setdefault('tools', {}).setdefault('AloneClickChoice', {}).setdefault('anwserConfig', {})['anwserRadio'] = 1 if is_correct else 2
        for s in cd.get('states', []):
            if 'MSprite' in s.get('source', {}):
                s['source']['MSprite']['value'] = ''

# ── Validation summary ────────────────────────────────────────────
print('\n关卡 | 音频  | 选项1(comp4) | 选项2(comp5) | 选项3(comp6) | 正确 | lc_hide节点')
print('-' * 80)
audio_rev = {v: k for k, v in AUDIO_URLS.items()}
img_rev = {v: k for k, v in IMAGE_URLS.items()}

POS_NODE_V  = {1: 4, 2: 6, 3: 5}
POS_CLICK_V = {1: 9, 2: 8, 3: 7}

print('\n关卡 | 音频    | 左(L1)   | 中(L2)   | 右(L3)   | 正确位 | lc节点 | 点击选择无图')
print('-' * 85)
for gi, (audio_word, opt1, opt2, opt3, correct_idx) in enumerate(LEVELS):
    game = games[gi]
    comps = game['components']

    au_val = next((s.get('source',{}).get('MAudio',{}).get('value','') for s in comps[3]['component_data']['states'] if s['state']=='clickEnd'), '')
    au_name = audio_rev.get(au_val, '?')

    pos_imgs = {}
    for pos in [1,2,3]:
        v = next((s['source']['MSprite']['value'] for s in comps[POS_NODE_V[pos]]['component_data']['states'] if s['state']=='default'), '')
        pos_imgs[pos] = img_rev.get(v, '?')

    correct_pos_found = next((pos for pos in [1,2,3] if comps[POS_CLICK_V[pos]]['component_data'].get('components',{}).get('tools',{}).get('AloneClickChoice',{}).get('anwserConfig',{}).get('anwserRadio')==1), '?')

    sprite_ok = all(
        not any(s.get('source',{}).get('MSprite',{}).get('value','') for s in comps[POS_CLICK_V[pos]]['component_data'].get('states',[]))
        for pos in [1,2,3]
    )

    lc_node = next((str(POS_NODE_V[pos]) for pos in [1,2,3] if any(s['state']=='level_correct' for s in comps[POS_NODE_V[pos]]['component_data']['states'])), '?')
    lc_pos_name = {str(4):'LEFT',str(6):'CENTER',str(5):'RIGHT'}.get(lc_node,'?')

    marker = '✅' if sprite_ok else '❌有图'
    print(f'L{gi+1:2d} | {au_name:7} | {pos_imgs[1]:8} | {pos_imgs[2]:8} | {pos_imgs[3]:8} | pos={correct_pos_found}  | comp[{lc_node}]({lc_pos_name}) | {marker}')

# Save
config['game'] = games
data['result']['configuration'] = json.dumps(config, ensure_ascii=False)
with open('output/j8_monster_fixed.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

print('\n✅ Saved output/j8_monster_fixed.json')
