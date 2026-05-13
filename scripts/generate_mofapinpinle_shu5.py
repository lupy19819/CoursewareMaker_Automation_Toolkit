#!/usr/bin/env python3
"""
国际level2魔法拼拼乐暑5d1 / 暑5d2 配置生成
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# 复用 generate_spelling_config.py 的核心逻辑
import importlib.util, types

# 动态加载基础脚本获取 build_config 函数
spec = importlib.util.spec_from_file_location("base", os.path.join(os.path.dirname(__file__), "generate_spelling_config.py"))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

BASE = "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com"

# ===== 暑5d1 题目 =====
LEVELS_D1 = [
    {
        "text": "kid",
        "answer_area": [
            {"type": "slot", "content": "k"},
            {"type": "slot", "content": "i"},
            {"type": "slot", "content": "d"},
        ],
        "items": ["k", "d", "i"],
        "word_audio_url": "",
        "word_image_url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/46fc17d6a8f6bb6994480f59a67a3523.png",
    },
    {
        "text": "granddaughter",
        "answer_area": [
            {"type": "slot", "content": "gr"},
            {"type": "slot", "content": "and"},
            {"type": "slot", "content": "d"},
            {"type": "slot", "content": "augh"},
            {"type": "slot", "content": "ter"},
        ],
        "items": ["and", "gr", "ter", "augh", "d"],
        "word_audio_url": "",
        "word_image_url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/4a877f8a5b8c19c33bb4ad1736fe12af.png",
    },
    {
        "text": "grandson",
        "answer_area": [
            {"type": "slot", "content": "gr"},
            {"type": "slot", "content": "and"},
            {"type": "slot", "content": "s"},
            {"type": "slot", "content": "on"},
        ],
        "items": ["on", "and", "gr", "s"],
        "word_audio_url": "",
        "word_image_url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/32068c41667e53570fac22a5f66f01ce.png",
    },
    {
        "text": "grown-up",
        "answer_area": [
            {"type": "slot", "content": "gr"},
            {"type": "slot", "content": "ow"},
            {"type": "slot", "content": "n"},
            {"type": "fixed", "content": "-"},
            {"type": "slot", "content": "u"},
            {"type": "slot", "content": "p"},
        ],
        "items": ["ow", "u", "gr", "n", "p"],
        "word_audio_url": "",
        "word_image_url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/9dd37909b9f8a9f41cfdec06c78d0672.png",
    },
]

# ===== 暑5d2 题目 =====
LEVELS_D2 = [
    {
        "text": "daughter",
        "answer_area": [
            {"type": "slot", "content": "d"},
            {"type": "slot", "content": "au"},
            {"type": "slot", "content": "gh"},
            {"type": "slot", "content": "t"},
            {"type": "slot", "content": "er"},
        ],
        "items": ["t", "er", "au", "d", "gh"],
        "word_audio_url": "",
        "word_image_url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/66a320ed9ab3ee1ef642592c9434a448.png",
    },
    {
        "text": "son",
        "answer_area": [
            {"type": "slot", "content": "s"},
            {"type": "slot", "content": "o"},
            {"type": "slot", "content": "n"},
        ],
        "items": ["n", "o", "s"],
        "word_audio_url": "",
        "word_image_url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/5dcd0abda4d77dee6296a2567b7ab43e.png",
    },
    {
        "text": "grandparent",
        "answer_area": [
            {"type": "slot", "content": "gr"},
            {"type": "slot", "content": "and"},
            {"type": "slot", "content": "pa"},
            {"type": "slot", "content": "rent"},
        ],
        "items": ["pa", "gr", "and", "rent"],
        "word_audio_url": "",
        "word_image_url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/a6ea7f041fc85e37feaeea3e6af1dc0d.png",
    },
    {
        "text": "grandchildren",
        "answer_area": [
            {"type": "slot", "content": "gr"},
            {"type": "slot", "content": "and"},
            {"type": "slot", "content": "chil"},
            {"type": "slot", "content": "dr"},
            {"type": "slot", "content": "en"},
        ],
        "items": ["gr", "chil", "en", "and", "dr"],
        "word_audio_url": "",
        "word_image_url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-09/c1f8fdd8b0553ec2ec44ada43ab9b471.png",
    },
]

if __name__ == "__main__":
    import json, os
    out_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(out_dir, exist_ok=True)

    # 临时替换 LEVELS 并生成 d1
    base.LEVELS = LEVELS_D1
    cfg_d1 = base.build_config()
    out_d1 = os.path.join(out_dir, "国际level2魔法拼拼乐暑5d1_config.json")
    with open(out_d1, "w", encoding="utf-8") as f:
        json.dump(cfg_d1, f, ensure_ascii=False, indent=2)
    print(f"D1 config saved: {out_d1}")

    # 生成 d2
    base.LEVELS = LEVELS_D2
    cfg_d2 = base.build_config()
    out_d2 = os.path.join(out_dir, "国际level2魔法拼拼乐暑5d2_config.json")
    with open(out_d2, "w", encoding="utf-8") as f:
        json.dump(cfg_d2, f, ensure_ascii=False, indent=2)
    print(f"D2 config saved: {out_d2}")
