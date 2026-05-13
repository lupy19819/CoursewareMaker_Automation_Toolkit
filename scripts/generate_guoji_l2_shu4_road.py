#!/usr/bin/env python3
"""
生成 国际level2公路大冒险暑4 配置
基准：国际level1公路大冒险暑4 (9248a803-3136-11f0-a334-fa29dffefa84)
4道题，图片+音频型，绿地模板
"""
import json, copy, sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

# ── 资源 URL 映射 ──────────────────────────────────────────────
IMAGES = {
    "carry_m": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-12/bd54b6d3513662a42906e897ace8ccde.png",
    "carry_d": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-12/99c09e92b6d9582d0ba647f76993de7e.png",
    "carry_c": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-12/8360e6a7d98abf9fd49cf5c4de5448f4.png",
    "invite_m": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-12/10d41097c9ec35ffc0139b7dd937afec.png",
    "invite_d": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-12/c7020b3c5f56589a02cb897dad33efb5.png",
    "invite_c": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-12/1b56321b04855cd2972b51a912c4a3bf.png",
    "textdad_m": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-12/424ad318a3c22b72d44413521002c2cd.png",
    "textdad_d": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-12/fe0e74d38bb9fbc2a4afb38a318e1cf3.png",
    "textdad_c": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-12/095ff75b757f3f6629c79cec8e64f71d.png",
    "tidy_m": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-12/995579e3cd9eb727377836cb4ba792ec.png",
    "tidy_d": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-12/74cfbb016d4ab388cb2ea8a9cf9c0997.png",
    "tidy_c": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-12/32984a32626e89fb9c728d1dae4fe892.png",
}

AUDIOS = {
    "carry": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/audio/V0056779/2026-05-12/4d055714a9ab090811e3deeb14bd9fb5.mp3",
    "invite": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/audio/V0056779/2026-05-12/182f358dcb2980d56fc873d901a3feef.mp3",
    "textdad": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/audio/V0056779/2026-05-12/8a22451f00933b62d68d4e71f61ea596.mp3",
    "tidy": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/audio/V0056779/2026-05-12/cf7ff5becc6fe3bfd03eec89f0a38a41.mp3",
}

# ── 题目数据 ──────────────────────────────────────────────────
# 每题: (audio_key, [(img_key, is_correct), ...])
# 选项顺序与 sheet 一致
QUESTIONS = [
    # Q1: carry the shopping inside
    ("carry", [("tidy", False), ("carry", True), ("invite", False)]),
    # Q2: text Dad
    ("textdad", [("textdad", True), ("carry", False), ("invite", False)]),
    # Q3: tidy Amy's bedroom
    ("tidy", [("tidy", True), ("textdad", False), ("carry", False)]),
    # Q4: invite Grandma and Grandpa for dinner
    ("invite", [("tidy", False), ("textdad", False), ("invite", True)]),
]

def get_correct_option_index(options):
    """返回正确选项的 1-based 索引"""
    for i, (_, is_correct) in enumerate(options):
        if is_correct:
            return i + 1
    raise ValueError("No correct option found")

def get_animation_for_correct(option_index, game_level):
    """
    根据正确选项位置获取小鹿动效
    需要从基准配置读取实际 y 坐标对应关系
    基准配置：正确项=选项1(y≈286) → animation=xia
              正确项=选项2(y≈0附近) → animation=zhong
              正确项=选项3(y≈-286) → animation=shang
    注：动效与位置名称相反（顶部=xia，底部=shang）
    """
    # 从基准配置实际观察到选项1在上(大y), 选项3在下(小y/负y)
    # 正确项动效: 选项1→xia, 选项2→zhong, 选项3→shang
    ANIM_MAP = {1: "xia", 2: "zhong", 3: "shang"}
    return ANIM_MAP.get(option_index, "zhong")

def replace_level(level_data, audio_key, options):
    """替换单关的音频和选项图片"""
    level = copy.deepcopy(level_data)
    components = level.get("components", [])
    
    choice_idx = 0  # 计数 AloneClickChoice
    
    for c in components:
        cd = c.get("component_data", {})
        name = cd.get("name", "")
        states = cd.get("states", [])
        
        # 替换语音按钮音频
        if "语音" in name:
            for s in states:
                if s.get("label") == "播放语音":
                    if "MAudio" in s.get("source", {}):
                        s["source"]["MAudio"]["value"] = AUDIOS[audio_key]
        
        # 替换选项图片
        if c.get("name") == "AloneClickChoice" and choice_idx < len(options):
            img_key, is_correct = options[choice_idx]
            
            # 设置 anwserRadio
            tools = cd.get("components", {}).get("tools", {})
            if "AloneClickChoice" in tools:
                tools["AloneClickChoice"]["anwserConfig"] = {
                    "anwserRadio": 1 if is_correct else 2
                }
            
            # 替换三态图片
            for s in states:
                label = s.get("label", "")
                src = s.get("source", {})
                if "MSprite" not in src:
                    continue
                if label == "默认":
                    src["MSprite"]["value"] = IMAGES[f"{img_key}_m"]
                elif label == "当前组件正确":
                    src["MSprite"]["value"] = IMAGES[f"{img_key}_d"]
                elif label == "当前组件错误":
                    src["MSprite"]["value"] = IMAGES[f"{img_key}_c"]
            
            choice_idx += 1
        
        # 更新小鹿开车正确动效
        if name == "小鹿开车":
            correct_idx = get_correct_option_index(options)
            anim = get_animation_for_correct(correct_idx, None)
            for s in states:
                if "正确" in s.get("label", "") or s.get("label") == "全局正确":
                    src = s.get("source", {})
                    if "MSpine" in src:
                        src["MSpine"]["animation"] = anim
    
    return level

# ── 主程序 ────────────────────────────────────────────────────
def main():
    base_path = BASE_DIR / "output/road_adventure_configs/9248a803-3136-11f0-a334-fa29dffefa84.json"
    with open(base_path, "r", encoding="utf-8") as f:
        base = json.load(f)
    
    new_config = copy.deepcopy(base)
    
    # 只保留4关（前4关作为模板，完整替换内容）
    base_levels = base["game"]
    new_levels = []
    
    for i, (audio_key, options) in enumerate(QUESTIONS):
        # 使用基准第 i 关（循环使用前4关）
        base_level = base_levels[i % len(base_levels)]
        new_level = replace_level(base_level, audio_key, options)
        new_levels.append(new_level)
    
    new_config["game"] = new_levels
    
    out_path = BASE_DIR / "output/国际level2公路大冒险暑4_config.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(new_config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 配置已生成: {out_path}")
    print(f"   关卡数: {len(new_levels)}")
    
    # 校验
    errors = []
    for i, level in enumerate(new_levels):
        choices = [c for c in level.get("components", []) if c.get("name") == "AloneClickChoice"]
        if len(choices) != 3:
            errors.append(f"Q{i+1}: 选项数={len(choices)} (应为3)")
        correct_count = sum(
            1 for c in choices
            if c.get("component_data", {}).get("components", {}).get("tools", {}).get("AloneClickChoice", {}).get("anwserConfig", {}).get("anwserRadio") == 1
        )
        if correct_count != 1:
            errors.append(f"Q{i+1}: 正确项数={correct_count} (应为1)")
    
    if errors:
        print("❌ 校验失败:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("✅ 校验通过：每关3选项，每关1个正确项")

if __name__ == "__main__":
    main()
