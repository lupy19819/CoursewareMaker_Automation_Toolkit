#!/usr/bin/env python3
"""
生成 国际level2公路大冒险暑4 配置
基准：国际level1公路大冒险暑4 (9248a803-3136-11f0-a334-fa29dffefa84)
4道题，图片+音频型，绿地模板
"""
import argparse
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
    for i, option in enumerate(options):
        if is_correct(option):
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

def resolve_audio(question):
    if isinstance(question, dict):
        if question.get("audio_url"):
            return question["audio_url"]
        if question.get("audio_key"):
            return AUDIOS[question["audio_key"]]
        return ""
    return AUDIOS[question]


def resolve_stem_text(question):
    if isinstance(question, dict):
        return (question.get("stem_text") or question.get("title_text") or question.get("text") or "").strip()
    return ""


def infer_prompt_type(question):
    audio = resolve_audio(question)
    text = resolve_stem_text(question)
    if audio and text:
        return "audio_text"
    if audio:
        return "pure_audio"
    if text:
        return "pure_text"
    return "unknown"


def resolve_image(option, state):
    if isinstance(option, dict):
        if option.get("image_urls"):
            return option["image_urls"][state]
        if option.get("image_key"):
            return IMAGES[f"{option['image_key']}_{state}"]
    image_key = option[0] if isinstance(option, (list, tuple)) else option
    return IMAGES[f"{image_key}_{state}"]


def is_correct(option):
    if isinstance(option, dict):
        return bool(option.get("correct") or option.get("is_correct"))
    return bool(option[1])


def normalize_questions(payload):
    questions = payload.get("questions", payload.get("levels")) if isinstance(payload, dict) else payload
    if not isinstance(questions, list) or not questions:
        raise ValueError("input must be a non-empty list or an object with questions/levels")
    normalized = []
    for index, q in enumerate(questions, 1):
        if isinstance(q, dict):
            audio = q
            options = q.get("options", [])
        else:
            audio_key, options = q
            audio = {"audio_key": audio_key}
        if infer_prompt_type(audio) == "unknown":
            raise ValueError(f"L{index}: road adventure requires audio_url/audio_key and/or stem_text")
        if len(options) != 3:
            raise ValueError(f"L{index}: road adventure requires exactly 3 options")
        if sum(1 for option in options if is_correct(option)) != 1:
            raise ValueError(f"L{index}: each level must have exactly one correct option")
        normalized.append((audio, options))
    return normalized


def load_questions(path):
    with open(path, encoding="utf-8") as f:
        return normalize_questions(json.load(f))


def set_label_value(component, value):
    changed = False
    for state in component.get("component_data", {}).get("states", []):
        source = state.get("source", {})
        label = source.get("MLabel")
        if isinstance(label, dict):
            label["value"] = value
            changed = True
    return changed


def is_stem_text_component(component):
    cd = component.get("component_data", {})
    name = cd.get("name", "")
    has_label = any("MLabel" in state.get("source", {}) for state in cd.get("states", []))
    if not has_label:
        return False
    return any(keyword in name for keyword in ("题干", "题目", "文本", "问题")) or name == "节点"


def replace_level(level_data, audio_ref, options):
    """替换单关的音频和选项图片"""
    level = copy.deepcopy(level_data)
    components = level.get("components", [])
    stem_text = resolve_stem_text(audio_ref)
    stem_text_written = False
    
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
                        s["source"]["MAudio"]["value"] = resolve_audio(audio_ref)

        # 替换题干文本。模板必须提供明确的 MLabel 承载节点，否则阻断，避免把文本误写到选项或装饰组件。
        if stem_text and is_stem_text_component(c):
            stem_text_written = set_label_value(c, stem_text) or stem_text_written
        
        # 替换选项图片
        if c.get("name") == "AloneClickChoice" and choice_idx < len(options):
            opt = options[choice_idx]
            
            # 设置 anwserRadio
            tools = cd.get("components", {}).get("tools", {})
            if "AloneClickChoice" in tools:
                tools["AloneClickChoice"]["anwserConfig"] = {
                    "anwserRadio": 1 if is_correct(opt) else 2
                }
            
            # 替换三态图片
            for s in states:
                label = s.get("label", "")
                src = s.get("source", {})
                if "MSprite" not in src:
                    continue
                if label == "默认":
                    src["MSprite"]["value"] = resolve_image(opt, "m")
                elif label == "当前组件正确":
                    src["MSprite"]["value"] = resolve_image(opt, "d")
                elif label == "当前组件错误":
                    src["MSprite"]["value"] = resolve_image(opt, "c")
            
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

    if stem_text and not stem_text_written:
        raise ValueError("road adventure stem_text provided but no stem text MLabel component was found in template")
    
    return level

# ── 主程序 ────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="公路大冒险配置生成脚本")
    parser.add_argument("--input", help="动态题目 JSON。题目相关音频/选项/正确项必须从这里读取")
    parser.add_argument("--template", default=str(BASE_DIR / "reference_configs/road_adventure_ref.json"), help="模板/参考配置 JSON")
    parser.add_argument("--output", default=str(BASE_DIR / "output/国际level2公路大冒险暑4_config.json"), help="输出配置 JSON")
    parser.add_argument("--meta", help="输出 build meta JSON")
    args = parser.parse_args()

    base_path = Path(args.template)
    with open(base_path, "r", encoding="utf-8") as f:
        base = json.load(f)
    
    new_config = copy.deepcopy(base)
    
    # 只保留4关（前4关作为模板，完整替换内容）
    base_levels = base["game"]
    new_levels = []
    
    questions = load_questions(args.input) if args.input else normalize_questions(QUESTIONS)
    for i, (audio_ref, options) in enumerate(questions):
        # 使用基准第 i 关（循环使用前4关）
        base_level = base_levels[i % len(base_levels)]
        new_level = replace_level(base_level, audio_ref, options)
        new_levels.append(new_level)
    
    new_config["game"] = new_levels
    
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(new_config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 配置已生成: {out_path}")
    print(f"   关卡数: {len(new_levels)}")
    if args.meta:
        meta = {
            "schema": "coursewaremaker.road_adventure.build_meta.v1",
            "generator": "scripts/generate_guoji_l2_shu4_road.py",
            "template": str(base_path),
            "output": str(out_path),
            "question_count": len(questions),
            "levels": [
                {
                    "index": i,
                    "prompt_type": infer_prompt_type(audio_ref),
                    "stem_text": resolve_stem_text(audio_ref),
                    "has_audio": bool(resolve_audio(audio_ref)),
                    "option_count": len(options),
                }
                for i, (audio_ref, options) in enumerate(questions, 1)
            ],
        }
        Path(args.meta).parent.mkdir(parents=True, exist_ok=True)
        Path(args.meta).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    
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
