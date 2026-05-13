"""
生成 J10 贪吃小怪兽配置
"""
import json
from pathlib import Path
from copy import deepcopy

# 加载模板
template_path = Path('/home/148139_wy/.openclaw/media/inbound/贪吃参考---397d660c-e224-48e1-807d-91b4efcbf685.json')
raw = template_path.read_text(encoding='utf-8').strip()
if raw.startswith("'") and raw.endswith("'"):
    raw = raw[1:-1]
config = json.loads(raw)

# J10 资源映射
RESOURCE_LOOKUP = {
    "26暑国际小班10贪吃e":   {"id": 75820, "url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-05-07/6f6bd48f255c90c849b56054cfe251cb.png"},
    "26暑国际小班10贪吃f":   {"id": 75821, "url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-05-07/a6ab25cac1b833e514bd229507fdff06.png"},
    "26暑国际小班10贪吃g":   {"id": 75822, "url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-05-07/ea7dc037963c2528cd772cf4cee54322.png"},
    "26暑国际小班10贪吃h":   {"id": 75823, "url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-05-07/616038a477e36a03786e13dc5c2e2aec.png"},
    "26暑国际小班10贪吃音频e": {"id": 75824, "url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/audio/345733/2026-05-07/c5bfa6c41d43dd3340efcf7ca9586673.mp3"},
    "26暑国际小班10贪吃音频f": {"id": 75825, "url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/audio/345733/2026-05-07/2f90546e50cb4f612c9922a2b59ec914.mp3"},
    "26暑国际小班10贪吃音频g": {"id": 75826, "url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/audio/345733/2026-05-07/c4cd41355554d003b4146867a36e0aca.mp3"},
    "26暑国际小班10贪吃音频h": {"id": 75827, "url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/audio/345733/2026-05-07/095421ce24170a713dc4cba729f1fef1.mp3"},
}

# J10 题目数据 (options[0]=位置1, options[1]=位置2, options[2]=位置3)
QUESTIONS = [
    {"qno": 1, "audio": "26暑国际小班10贪吃音频e", "options": ["26暑国际小班10贪吃e", "26暑国际小班10贪吃g", "26暑国际小班10贪吃f"], "correct_pos": 1},
    {"qno": 2, "audio": "26暑国际小班10贪吃音频f", "options": ["26暑国际小班10贪吃g", "26暑国际小班10贪吃e", "26暑国际小班10贪吃f"], "correct_pos": 3},
    {"qno": 3, "audio": "26暑国际小班10贪吃音频g", "options": ["26暑国际小班10贪吃f", "26暑国际小班10贪吃g", "26暑国际小班10贪吃h"], "correct_pos": 2},
    {"qno": 4, "audio": "26暑国际小班10贪吃音频h", "options": ["26暑国际小班10贪吃g", "26暑国际小班10贪吃f", "26暑国际小班10贪吃h"], "correct_pos": 3},
]

# 只保留4个关卡
config["game"] = config["game"][:4]

# 节点映射
NODE_NAME_BY_POS = {1: "节点", 2: "节点_104", 3: "节点_103"}
RIGHT_ANIMATION_BY_POS = {1: "right_1_2", 2: "right_2_2", 3: "right_3_2"}

def update_component(comp, state_name, key, value):
    """更新组件状态中的值"""
    for state in comp.get("component_data", {}).get("states", []):
        if state.get("state") == state_name:
            state["source"] = state.get("source", {})
            if key == "image":
                state["source"]["MSprite"] = {"value": value}
            elif key == "audio":
                state["source"]["MAudio"] = {"value": value}

def find_component(components, pattern):
    """按 component_data.name 查找组件"""
    for comp in components:
        name = comp.get("component_data", {}).get("name", "")
        if pattern in name:
            return comp
    return None

def process_level(level, question, qidx):
    """处理单个关卡"""
    components = level.get("components", [])
    
    # 找到 TitleStem 并更新题干音频
    title_stem = find_component(components, "TitleStem")
    if title_stem:
        update_component(title_stem, "clickEnd", "audio", RESOURCE_LOOKUP[question["audio"]]["url"])
    
    # 找到三个选项节点
    options = []
    for pos in [1, 2, 3]:
        node_name = NODE_NAME_BY_POS[pos]
        node = find_component(components, node_name)
        if node:
            options.append({"pos": pos, "comp": node, "res": question["options"][pos-1]})
    
    # 更新选项图片和正确项标记
    for opt in options:
        pos = opt["pos"]
        comp = opt["comp"]
        res_name = opt["res"]
        
        # 更新图片
        update_component(comp, "default", "image", RESOURCE_LOOKUP[res_name]["url"])
        
        # 设置正确项标记
        tools = comp.get("component_data", {}).get("components", {}).get("tools", {})
        alone_click = tools.get("AloneClickChoice", {})
        answer_cfg = alone_click.get("anwserConfig", {})
        
        if pos == question["correct_pos"]:
            answer_cfg["anwserRadio"] = 1
        else:
            answer_cfg["anwserRadio"] = 2
    
    # 设置节点_102 反馈动效
    effect_monster = find_component(components, "节点_102")
    if effect_monster:
        for state in effect_monster.get("component_data", {}).get("states", []):
            if state.get("state") == "level_correct":
                state["source"] = state.get("source", {})
                state["source"]["MSpine"] = {"animation": RIGHT_ANIMATION_BY_POS[question["correct_pos"]]}
    
    return {"level": qidx+1, "correct_pos": question["correct_pos"], "audio": question["audio"]}

# 处理每个关卡
results = []
for i, (level, question) in enumerate(zip(config["game"], QUESTIONS)):
    result = process_level(level, question, i)
    results.append(result)

# 保存配置
output_dir = Path('/home/148139_wy/.openclaw/workspace/CoursewareMaker_Automation_Toolkit')
output_json = output_dir / '国际新小班暑J10贪吃小怪兽.config.json'
output_json.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')

print(f"✓ 配置已保存: {output_json}")
print(f"关卡数: {len(config['game'])}")
print("处理结果:", json.dumps(results, ensure_ascii=False, indent=2))
