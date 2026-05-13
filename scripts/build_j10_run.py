"""
生成 J10 跑酷赛跑配置
结构：custom_game[i].topics[0].title_res.{btnAudio, options[0..2].item.{icon, switch}}
"""
import json, uuid
from pathlib import Path
from copy import deepcopy

# 模板：测试小班赛跑J2（10题）
template_path = Path('/home/148139_wy/.openclaw/workspace/CoursewareMaker_Automation_Toolkit/测试小班赛跑J2.config.json')
config = json.loads(template_path.read_text(encoding='utf-8'))

# 资源映射
RESOURCE_LOOKUP = {
    "26暑国际小班10赛跑bag":  "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-05-07/8c127bf68c564b31a843d3582b447efa.png",
    "26暑国际小班10赛跑book": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-05-07/1452c4cead4b3eba85ea424f3479b4c6.png",
    "26暑国际小班10赛跑toy":  "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-05-07/75551656ec57e4dc0c42c2e51ecb3fc7.png",
    "26暑国际小班10赛跑音频单词bag":  "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/audio/345733/2026-05-07/1c3317d9966a36a6462e4464d8494cb2.mp3",
    "26暑国际小班10赛跑音频单词book": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/audio/345733/2026-05-07/c542ec22c05bf2f2baabc8fa3b7be0b8.mp3",
    "26暑国际小班10赛跑音频单词toy":  "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/audio/345733/2026-05-07/f89b9ce4e24200ff40946a4d0929dd2a.mp3",
}

# J10 题目数据（10题，options顺序=位置1/2/3，correct_pos=哪个是正确的）
QUESTIONS = [
    {"qno":  1, "audio": "26暑国际小班10赛跑音频单词book", "options": ["26暑国际小班10赛跑book", "26暑国际小班10赛跑bag",  "26暑国际小班10赛跑toy"],  "correct_pos": 1},
    {"qno":  2, "audio": "26暑国际小班10赛跑音频单词bag",  "options": ["26暑国际小班10赛跑toy",  "26暑国际小班10赛跑bag",  "26暑国际小班10赛跑book"], "correct_pos": 2},
    {"qno":  3, "audio": "26暑国际小班10赛跑音频单词toy",  "options": ["26暑国际小班10赛跑bag",  "26暑国际小班10赛跑book", "26暑国际小班10赛跑toy"],  "correct_pos": 3},
    {"qno":  4, "audio": "26暑国际小班10赛跑音频单词toy",  "options": ["26暑国际小班10赛跑toy",  "26暑国际小班10赛跑book", "26暑国际小班10赛跑bag"],  "correct_pos": 1},
    {"qno":  5, "audio": "26暑国际小班10赛跑音频单词book", "options": ["26暑国际小班10赛跑book", "26暑国际小班10赛跑bag",  "26暑国际小班10赛跑toy"],  "correct_pos": 1},
    {"qno":  6, "audio": "26暑国际小班10赛跑音频单词bag",  "options": ["26暑国际小班10赛跑bag",  "26暑国际小班10赛跑book", "26暑国际小班10赛跑toy"],  "correct_pos": 1},
    {"qno":  7, "audio": "26暑国际小班10赛跑音频单词book", "options": ["26暑国际小班10赛跑toy",  "26暑国际小班10赛跑bag",  "26暑国际小班10赛跑book"], "correct_pos": 3},
    {"qno":  8, "audio": "26暑国际小班10赛跑音频单词toy",  "options": ["26暑国际小班10赛跑bag",  "26暑国际小班10赛跑toy",  "26暑国际小班10赛跑book"], "correct_pos": 2},
    {"qno":  9, "audio": "26暑国际小班10赛跑音频单词bag",  "options": ["26暑国际小班10赛跑bag",  "26暑国际小班10赛跑book", "26暑国际小班10赛跑toy"],  "correct_pos": 1},
    {"qno": 10, "audio": "26暑国际小班10赛跑音频单词book", "options": ["26暑国际小班10赛跑toy",  "26暑国际小班10赛跑book", "26暑国际小班10赛跑bag"],  "correct_pos": 2},
]

cg = config['custom_game']
# 确保有10个关卡（模板已有10个）
assert len(cg) == 10, f"模板只有{len(cg)}个关卡"

results = []
for i, question in enumerate(QUESTIONS):
    level = cg[i]
    topic = level['topics'][0]
    title_res = topic['title_res']

    # 更新题干音频
    title_res['btnAudio'] = RESOURCE_LOOKUP[question['audio']]

    # 更新选项
    for j, opt in enumerate(title_res['options']):
        pos = j + 1  # 1-indexed
        opt['item']['icon'] = RESOURCE_LOOKUP[question['options'][j]]
        opt['item']['switch'] = (pos == question['correct_pos'])

    results.append({
        "level": i+1,
        "audio": question['audio'],
        "correct_pos": question['correct_pos'],
        "correct_option": question['options'][question['correct_pos']-1]
    })

output_dir = Path('/home/148139_wy/.openclaw/workspace/CoursewareMaker_Automation_Toolkit')
output_json = output_dir / '国际新小班暑J10跑酷赛跑.config.json'
output_json.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')

print(f"✓ 赛跑配置已保存: {output_json}")
print(json.dumps(results, ensure_ascii=False, indent=2))
