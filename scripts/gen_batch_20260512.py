#!/usr/bin/env python3
"""
生成5个运动PK配置 (2026-05-12批次)
- 国际level2赛跑暑4  (赛跑, 4题)
- 国际level2游泳暑8  (游泳, 4题)
- 国际level2赛跑暑7  (赛跑, 5题)
- 国际L3A跑酷游泳暑3 (游泳, 6题)
- 国际L3A跑酷赛跑暑4 (赛跑, 6题)
全部: 图片题干 + 文字选项, 无音频
"""
import json, pathlib, uuid, copy, re

REPO = pathlib.Path(__file__).resolve().parents[1]
UPLOAD_LOG = REPO / "output" / "upload_log.jsonl"
TEMPLATE_RUN = REPO / "templates" / "detail_jsons" / "run_detail.json"
TEMPLATE_SWIM = REPO / "templates" / "detail_jsons" / "swim_detail.json"
OUTPUT_DIR = REPO / "output" / "configs_20260512"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── 加载 upload_log → name -> url ──────────────────────────────────────
def load_url_map():
    rows = [json.loads(l) for l in UPLOAD_LOG.read_text().splitlines() if l.strip()]
    m = {}
    for r in rows:
        name = r.get("name", "")
        url = r.get("url", "")
        if name and url:
            m[name] = url
    return m

def find_url(url_map, name):
    """模糊匹配: 先精确, 再去掉.png后缀, 再去掉空格差异"""
    if name in url_map:
        return url_map[name]
    # strip .png
    stem = re.sub(r'\.png$', '', name, flags=re.IGNORECASE)
    if stem in url_map:
        return url_map[stem]
    # try with leading 26 prefix
    with26 = "26" + stem if not stem.startswith("26") else stem
    if with26 in url_map:
        return url_map[with26]
    # collapse double spaces
    stem2 = re.sub(r'\s+', ' ', stem).strip()
    with26_2 = "26" + stem2 if not stem2.startswith("26") else stem2
    for key in url_map:
        k2 = re.sub(r'\s+', ' ', key).strip()
        if k2 == stem2 or k2 == with26_2:
            return url_map[key]
    return None

# ── 加载模板 ─────────────────────────────────────────────────────────────
def load_config(path):
    raw = json.loads(path.read_text())
    return json.loads(raw["result"]["configuration"])

# ── 从首关提取底图三态 ────────────────────────────────────────────────────
def extract_option_bg(config):
    cg = config["custom_game"]
    if not cg:
        return {}, {}, {}
    tp = cg[0]["topics"][0]
    opts = tp["title_res"]["options"]
    if not opts:
        return {}, {}, {}
    item = opts[0]["item"]
    return item["bgOptionNormal"], item["bgOptionCorrect"], item["bgOptionWrong"]

# ── 估算字号 ─────────────────────────────────────────────────────────────
def font_size(text):
    n = len(str(text))
    if n <= 4: return 70
    if n <= 8: return 60
    if n <= 12: return 50
    return 42

# ── 构建单关数据 ──────────────────────────────────────────────────────────
EMPTY_SPINE = {"scale": 1, "spine": "", "spine_spine_id": ""}
CORRECT_SPINE = {"scale": 1, "spine": "", "spine_spine_id": ""}

def build_topic(stem_url, options, bg_normal, bg_correct, bg_wrong, titleBg):
    """
    stem_url: 题干图片URL
    options: list of (text, is_correct)
    """
    built_opts = []
    for text, is_correct in options:
        item = {
            "bgOptionCorrect": bg_correct,
            "bgOptionNormal": bg_normal,
            "bgOptionWrong": bg_wrong,
            "correctSpine": CORRECT_SPINE,
            "icon": "",
            "opstionText": {
                "MLabel": str(text),
                "fontSize": font_size(text)
            },
            "switch": is_correct
        }
        built_opts.append({"item": item})

    title_res = {
        "audioSpine": EMPTY_SPINE,
        "btnAudio": "",
        "icon": stem_url,
        "options": built_opts,
        "titleAuido": "",
        "titleBg": titleBg,
        "titleText": {"MLabel": "", "fontSize": 70}
    }
    return {
        "CustomTopicConfig": {"maxQuestionNum": 1, "minQuestionNum": 1},
        "title_res": title_res
    }

def build_custom_game(questions, bg_normal, bg_correct, bg_wrong, titleBg):
    """questions: list of (stem_url, [(text, is_correct), ...])"""
    result = []
    for stem_url, opts in questions:
        uid = str(uuid.uuid4())
        topic = build_topic(stem_url, opts, bg_normal, bg_correct, bg_wrong, titleBg)
        result.append({"id": uid, "topics": [topic]})
    return result

# ── 题目数据 ──────────────────────────────────────────────────────────────
GAMES = [
    {
        "name": "国际level2赛跑暑4",
        "type": "run",
        "questions": [
            ("国际level2赛跑暑4img_We _go camping",        [("never", True),  ("always", False), ("sometimes", False)]),
            ("26国际level2赛跑暑4img_They _ play video games_", [("always", False), ("never", False),  ("sometimes", True)]),
            ("26国际level2赛跑暑4img_I _go swimming",      [("never", False), ("always", True),  ("sometimes", False)]),
            ("国际level2赛跑暑4img_I read books_",          [("every day", True), ("never", False), ("always", False)]),
        ]
    },
    {
        "name": "国际level2游泳暑8",
        "type": "swim",
        "questions": [
            ("26国际level2游泳暑8图片brush your teeth", [("have", False), ("comb", False),    ("brush", True)]),
            ("26国际level2游泳暑8图片comb my hair",    [("put on", False), ("comb", True),   ("brush", False)]),
            ("26国际level2游泳暑8图片have a shower",   [("have", True),   ("brush", False),  ("put on", False)]),
            ("26国际level2游泳暑8图片put on the sun hat", [("comb", False), ("have", False),  ("put on", True)]),
        ]
    },
    {
        "name": "国际level2赛跑暑7",
        "type": "run",
        "questions": [
            ("26国际level2赛跑暑7图片1", [("hurts", True),       ("hurt", False)]),
            ("26国际level2赛跑暑7图片2", [("is sore", False),    ("are sore", True)]),
            ("26国际level2赛跑暑7图片3", [("is hurting", True),  ("are hurting", False)]),
            ("26国际level2赛跑暑7图片4", [("are fine", True),    ("hurt", False),          ("is hurting", False)]),
            ("26国际level2赛跑暑7图片5", [("What's；sore", False), ("What；is hurting", False), ("What's；is hurting", True)]),
        ]
    },
    {
        "name": "国际L3A跑酷游泳暑3",
        "type": "swim",
        "questions": [
            ("26国际L3A跑酷游泳暑3img_My pencil is lost",      [("anywhere", True),  ("anyone", False),  ("anything", False)]),
            ("26国际L3A跑酷游泳暑3img_This box was empty",     [("anything", False), ("nothing", True),  ("anywhere", False)]),
            ("26国际L3A跑酷游泳暑3img_ sits on that chair_",   [("No one", True),    ("Anyone", False),  ("Anything", False)]),
            ("26国际L3A跑酷游泳暑3img_Is there in your bag",   [("anything", True),  ("anywhere", False), ("no one", False)]),
            ("26国际L3A跑酷游泳暑3img_is knocking on the door",[("Anything", False), ("Someone", True),  ("Something", False)]),
            ("26国际L3A跑酷游泳暑3img_My keys are in this room",[("someone", False), ("nothing", False), ("somewhere", True)]),
        ]
    },
    {
        "name": "国际L3A跑酷赛跑暑4",
        "type": "run",
        "questions": [
            ("26国际L3A跑酷赛跑暑4图片img_The man is than the boy", [("taller", True),       ("more tall", False)]),
            ("26国际L3A跑酷赛跑暑4图片img_This box is than that one",[("biger", False),       ("bigger", True)]),
            ("26国际L3A跑酷赛跑暑4图片img_He thinks he's the",       [("happiest", True),     ("happyest", False)]),
            ("26国际L3A跑酷赛跑暑4图片img_She runs than me",          [("quickly", False),     ("more quickly", True)]),
            ("26国际L3A跑酷赛跑暑4图片img_Lucy sings than me",        [("weller", False),      ("better", True)]),
            ("26国际L3A跑酷赛跑暑4图片img_Lisa speaks in her class",  [("more loudly", False), ("the most loudly", True)]),
        ]
    },
]

# ── 主流程 ────────────────────────────────────────────────────────────────
def main():
    url_map = load_url_map()
    config_run = load_config(TEMPLATE_RUN)
    config_swim = load_config(TEMPLATE_SWIM)

    bg_normal_run, bg_correct_run, bg_wrong_run = extract_option_bg(config_run)
    bg_normal_swim, bg_correct_swim, bg_wrong_swim = extract_option_bg(config_swim)
    titleBg_run = config_run["custom_game"][0]["topics"][0]["title_res"]["titleBg"]
    titleBg_swim = config_swim["custom_game"][0]["topics"][0]["title_res"]["titleBg"]

    results = {}
    for game in GAMES:
        tpl = config_run if game["type"] == "run" else config_swim
        bg_n = bg_normal_run if game["type"] == "run" else bg_normal_swim
        bg_c = bg_correct_run if game["type"] == "run" else bg_correct_swim
        bg_w = bg_wrong_run  if game["type"] == "run" else bg_wrong_swim
        tBg  = titleBg_run   if game["type"] == "run" else titleBg_swim

        questions_resolved = []
        missing = []
        for (stem_name, opts) in game["questions"]:
            url = find_url(url_map, stem_name)
            if not url:
                missing.append(stem_name)
                url = f"MISSING:{stem_name}"
            questions_resolved.append((url, opts))

        if missing:
            print(f"⚠️  [{game['name']}] 未找到资源: {missing}")

        out_config = copy.deepcopy(tpl)
        out_config["custom_game"] = build_custom_game(
            questions_resolved, bg_n, bg_c, bg_w, tBg
        )

        out_path = OUTPUT_DIR / f"{game['name']}.json"
        out_path.write_text(json.dumps(out_config, ensure_ascii=False, indent=2))
        print(f"✅ [{game['name']}] {len(questions_resolved)}关 -> {out_path.name}")
        results[game['name']] = str(out_path)

    print(f"\n生成完毕，共 {len(results)} 个配置文件，路径: {OUTPUT_DIR}")
    return results

if __name__ == "__main__":
    main()
