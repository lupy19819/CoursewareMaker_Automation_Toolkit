#!/usr/bin/env python3
"""
运动PK配置校验脚本 —— 与参考配置对比
用法: python3 validate_yundong_pk_config.py <config.json> <game_type>
game_type: 赛跑 | 游泳 | 赛车

校验通过: 退出码 0，输出 ✅ VALID
校验失败: 退出码 1，输出具体差异
"""

import argparse
import json
import sys
from pathlib import Path

REFERENCE_DIR = Path(__file__).parent.parent / "reference_configs" / "yundong_pk"
GAME_TYPE_MAP = {
    "赛跑": "赛跑_reference.json",
    "游泳": "游泳_reference.json",
    "赛车": "赛车_reference.json",
}

IGNORE_VALUE_PATHS = {
    # 内容类字段：结构存在即可，值不必相同
    "spine", "btnAudio", "titleAuido", "titleText", "icon",
    "bgOptionNormal", "bgOptionCorrect", "bgOptionWrong",
    "opstionText", "switch", "titleBg", "MLabel", "fontSize",
    "game_id", "id",
}


def collect_keys(obj, path="", out=None):
    """收集所有 JSON 路径（忽略数组下标，统一用 [*]）"""
    if out is None:
        out = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            collect_keys(v, path + "." + k, out)
    elif isinstance(obj, list):
        for v in obj:
            collect_keys(v, path + "[*]", out)
    else:
        out.add(path)
    return out


def load_config(path: Path):
    raw = json.loads(path.read_text(encoding="utf-8").strip().strip("'"))
    if isinstance(raw, dict) and "result" in raw and isinstance(raw["result"], dict) and "configuration" in raw["result"]:
        cfg = raw["result"]["configuration"]
        return json.loads(cfg) if isinstance(cfg, str) else cfg
    if isinstance(raw, dict) and isinstance(raw.get("configuration"), str):
        return json.loads(raw["configuration"])
    return raw


def value_at(data, path: str):
    current = data
    for part in path.split("."):
        if not part:
            continue
        if "[" in part:
            key, rest = part.split("[", 1)
            if key:
                current = current[key]
            index = int(rest.rstrip("]"))
            current = current[index]
        else:
            current = current[part]
    return current


def validate_meta_bindings(config: dict, meta_path: Path) -> list[str]:
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    issues = []
    levels = meta.get("levels") or []
    custom_game = config.get("custom_game") or []

    if len(levels) != len(custom_game):
        issues.append(f"build-meta 关卡数 {len(levels)} 与 custom_game 关卡数 {len(custom_game)} 不一致")
        return issues

    for level_index, level_meta in enumerate(levels):
        prefix = f"custom_game[{level_index}].topics[0].title_res"
        title_res = custom_game[level_index]["topics"][0]["title_res"]
        audio_url = level_meta.get("audio_url") or ""
        if audio_url:
            for key in ("btnAudio", "titleAuido"):
                actual = title_res.get(key) or ""
                if actual != audio_url:
                    issues.append(f"L{level_index + 1} {key} 未写入预期音频 URL: expected={audio_url} actual={actual}")
        else:
            issues.append(f"L{level_index + 1} build-meta 缺少 audio_url")

        stem_url = level_meta.get("stem_img_url") or ""
        actual_stem = title_res.get("icon") or ""
        if stem_url and actual_stem != stem_url:
            issues.append(f"L{level_index + 1} 题干图未写入预期 URL: expected={stem_url} actual={actual_stem}")
        if not stem_url and actual_stem:
            issues.append(f"L{level_index + 1} build-meta 无题干图，但配置 icon 非空: actual={actual_stem}")

        options_meta = level_meta.get("options") or []
        options = title_res.get("options") or []
        if len(options_meta) > len(options):
            issues.append(f"L{level_index + 1} 选项数不足: meta={len(options_meta)} config={len(options)}")
            continue
        for option_index, option_meta in enumerate(options_meta):
            item = options[option_index].get("item", {})
            option_no = option_meta.get("option_no", option_index + 1)
            option_url = option_meta.get("option_img_url") or ""
            actual_icon = item.get("icon") or ""
            if option_url and actual_icon != option_url:
                issues.append(f"L{level_index + 1} 选项{option_no}图片未写入预期 URL: expected={option_url} actual={actual_icon}")
            if not option_url and actual_icon:
                issues.append(f"L{level_index + 1} 选项{option_no} meta 无图片，但配置 icon 非空: actual={actual_icon}")
            expected_switch = bool(option_meta.get("is_correct"))
            actual_switch = bool(item.get("switch"))
            if actual_switch != expected_switch:
                issues.append(f"L{level_index + 1} 选项{option_no}正确项 switch 不一致: expected={expected_switch} actual={actual_switch}")

    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config_path", type=Path)
    parser.add_argument("game_type", choices=sorted(GAME_TYPE_MAP))
    parser.add_argument("--meta", type=Path, help="Build meta generated with the config; enables URL/content binding checks")
    args = parser.parse_args()
    config_path, game_type = args.config_path, args.game_type

    if game_type not in GAME_TYPE_MAP:
        print(f"未知 game_type: {game_type}，可选: {list(GAME_TYPE_MAP.keys())}")
        sys.exit(2)

    ref_path = REFERENCE_DIR / GAME_TYPE_MAP[game_type]
    if not ref_path.exists():
        print(f"参考配置不存在: {ref_path}")
        sys.exit(2)

    config = load_config(Path(config_path))
    ref = json.loads(ref_path.read_text())

    ref_keys = collect_keys(ref)
    cfg_keys = collect_keys(config)

    # 只报参考配置有、但当前配置缺失的结构路径
    missing = sorted(ref_keys - cfg_keys)

    meta_issues = validate_meta_bindings(config, args.meta) if args.meta else []

    if missing:
        print(f"❌ INVALID — 缺少 {len(missing)} 个结构路径（相对参考配置）:\n")
        for p in missing[:30]:
            print(f"  {p}")
        if len(missing) > 30:
            print(f"  ... 共 {len(missing)} 处")
        sys.exit(1)
    if meta_issues:
        print(f"❌ INVALID — 资源/正确项写入校验失败 {len(meta_issues)} 处:\n")
        for issue in meta_issues[:50]:
            print(f"  {issue}")
        if len(meta_issues) > 50:
            print(f"  ... 共 {len(meta_issues)} 处")
        sys.exit(1)

    suffix = "，并通过 build-meta 资源写入校验" if args.meta else ""
    print(f"✅ VALID — {config_path} 与 {game_type} 参考配置结构一致{suffix}")
    sys.exit(0)


if __name__ == "__main__":
    main()
