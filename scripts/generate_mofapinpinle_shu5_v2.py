#!/usr/bin/env python3
"""
国际level2魔法拼拼乐暑5d1 / 暑5d2 配置生成（v3 修正版）
使用 generate_from_questions，位置和槽位分配全部动态计算，不依赖 zIndex 排序
"""
import sys, os, json, copy, importlib.util

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

# 动态加载 generate_mofappl_config.py
spec = importlib.util.spec_from_file_location("mofappl", os.path.join(SCRIPT_DIR, "generate_mofappl_config.py"))
mofappl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mofappl)

OUTPUT_DIR = os.path.join(BASE, 'output')

# 题目配图 URL（2026-05-11 上传）
IMG_BASE = "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-11/"
IMAGES = {
    "kid":           IMG_BASE + "6bc1f6663f59f2a50ac080e0ce4b82a2.png",
    "granddaughter": IMG_BASE + "d7af1a0f0c40b8674119abefd41fae22.png",
    "grandson":      IMG_BASE + "dc7828784c7f99d9e902ab420c5864c6.png",
    "grown-up":      IMG_BASE + "2affba181fea8338a96506bc0383cde6.png",
    "daughter":      IMG_BASE + "07aaa3c3d7dceb0185d5da62c28202c1.png",
    "son":           IMG_BASE + "90a871b43dcb54bc39b8997af27915a4.png",
    "grandparent":   IMG_BASE + "125a80a922e57f75d51e9cb925140c03.png",
    "grandchildren": IMG_BASE + "64eddaa40f6e02e46047e907114fddc2.png",
}

# 各图片真实像素尺寸（用于保持比例）
IMAGE_SIZES = {
    "kid":           (350, 252),
    "granddaughter": (351, 253),
    "grandson":      (352, 253),
    "grown-up":      (350, 253),
    "daughter":      (250, 344),
    "son":           (250, 344),
    "grandparent":   (322, 260),
    "grandchildren": (344, 250),
}

# sentence_parts 手动指定（区分拖拽槽 vs 固定文本）
LEVELS_D1 = [
    {
        "sentence": "kid",
        "sentence_parts": [
            {"type": "slot", "content": "k"},
            {"type": "slot", "content": "i"},
            {"type": "slot", "content": "d"},
        ],
        "slots": ["k", "i", "d"],
        "items": ["k", "d", "i"],
    },
    {
        "sentence": "granddaughter",
        "sentence_parts": [
            {"type": "slot", "content": "gr"},
            {"type": "slot", "content": "and"},
            {"type": "slot", "content": "d"},
            {"type": "slot", "content": "augh"},
            {"type": "slot", "content": "ter"},
        ],
        "slots": ["gr", "and", "d", "augh", "ter"],
        "items": ["and", "gr", "ter", "augh", "d"],
    },
    {
        "sentence": "grandson",
        "sentence_parts": [
            {"type": "slot", "content": "gr"},
            {"type": "slot", "content": "and"},
            {"type": "slot", "content": "s"},
            {"type": "slot", "content": "on"},
        ],
        "slots": ["gr", "and", "s", "on"],
        "items": ["on", "and", "gr", "s"],
    },
    {
        "sentence": "grown-up",
        "sentence_parts": [
            {"type": "slot", "content": "gr"},
            {"type": "slot", "content": "ow"},
            {"type": "slot", "content": "n"},
            {"type": "fixed", "content": "-"},
            {"type": "slot", "content": "u"},
            {"type": "slot", "content": "p"},
        ],
        "slots": ["gr", "ow", "n", "u", "p"],
        "items": ["ow", "u", "gr", "n", "p"],
    },
]

LEVELS_D2 = [
    {
        "sentence": "daughter",
        "sentence_parts": [
            {"type": "slot", "content": "d"},
            {"type": "slot", "content": "au"},
            {"type": "slot", "content": "gh"},
            {"type": "slot", "content": "t"},
            {"type": "slot", "content": "er"},
        ],
        "slots": ["d", "au", "gh", "t", "er"],
        "items": ["t", "er", "au", "d", "gh"],
    },
    {
        "sentence": "son",
        "sentence_parts": [
            {"type": "slot", "content": "s"},
            {"type": "slot", "content": "o"},
            {"type": "slot", "content": "n"},
        ],
        "slots": ["s", "o", "n"],
        "items": ["n", "o", "s"],
    },
    {
        "sentence": "grandparent",
        "sentence_parts": [
            {"type": "slot", "content": "gr"},
            {"type": "slot", "content": "and"},
            {"type": "slot", "content": "pa"},
            {"type": "slot", "content": "rent"},
        ],
        "slots": ["gr", "and", "pa", "rent"],
        "items": ["pa", "gr", "and", "rent"],
    },
    {
        "sentence": "grandchildren",
        "sentence_parts": [
            {"type": "slot", "content": "gr"},
            {"type": "slot", "content": "and"},
            {"type": "slot", "content": "chil"},
            {"type": "slot", "content": "dr"},
            {"type": "slot", "content": "en"},
        ],
        "slots": ["gr", "and", "chil", "dr", "en"],
        "items": ["gr", "chil", "en", "and", "dr"],
    },
]


def calc_display_size(word, max_w=430, max_h=360):
    size = IMAGE_SIZES.get(word)
    if not size:
        return max_w, 300
    iw, ih = size
    ratio = iw / ih
    if ratio >= 1:
        w = min(iw, max_w)
        h = round(w / ratio, 2)
        if h > max_h:
            h = max_h
            w = round(h * ratio, 2)
    else:
        h = min(ih, max_h)
        w = round(h * ratio, 2)
    return w, h


def patch_word_image(level, word):
    """在 build_level 之后，用真实图片URL和尺寸覆盖 题目配图"""
    img_url = IMAGES.get(word)
    if not img_url:
        return
    disp_w, disp_h = calc_display_size(word)
    for comp in level.get('components', []):
        cd = comp.get('component_data', {})
        if cd.get('name') == '题目配图':
            for state in cd.get('states', []):
                src = state.setdefault('source', {})
                if not isinstance(src.get('MSprite'), dict):
                    src['MSprite'] = {}
                src['MSprite']['value'] = img_url
                t = state.get('transform', {})
                if t:
                    t['w'] = disp_w
                    t['h'] = disp_h


def main():
    ref5_path = os.path.join(BASE, 'output/mofappl_configs/77cb396a-babd-11f0-885a-ba4dce53cceb.json')
    ref3_path = os.path.join(BASE, 'output/mofappl_configs/c3f13451-dfc0-11f0-9165-0e324dbd00ee.json')
    with open(ref5_path) as f:
        ref5 = json.load(f)
    with open(ref3_path) as f:
        ref3 = json.load(f)

    for day, levels_data in [("暑5d1", LEVELS_D1), ("暑5d2", LEVELS_D2)]:
        print(f"\n=== 生成 {day} ===")
        out_path = os.path.join(OUTPUT_DIR, f"国际level2魔法拼拼乐{day}_config.json")

        output_levels = []
        for i, lv_data in enumerate(levels_data):
            q = dict(lv_data)
            q['audio_url'] = ''
            n = len(q['slots'])
            # 选模板：3槽用ref3，其余用ref5
            tmpl = mofappl.find_template_level(ref3 if n <= 3 else ref5, n)
            if tmpl is None:
                tmpl = ref5['game'][0]
            # 用保持原始位置的函数生成
            level = mofappl.build_level_keep_positions(tmpl, q, level_idx=i)
            patch_word_image(level, lv_data['sentence'])
            print(f"  L{i} {lv_data['sentence']}({n}槽): OK")
            output_levels.append(level)

        cfg = {
            'common':     ref5['common'],
            'game':       output_levels,
            'additional': ref5['additional'],
            'components': ref5.get('components', [])
        }
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        print(f"  写入: {out_path}")


if __name__ == '__main__':
    main()
