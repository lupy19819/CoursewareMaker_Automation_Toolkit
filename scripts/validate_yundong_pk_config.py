#!/usr/bin/env python3
"""
运动PK配置校验脚本 —— 与参考配置对比
用法: python3 validate_yundong_pk_config.py <config.json> <game_type>
game_type: 赛跑 | 游泳 | 赛车

校验通过: 退出码 0，输出 ✅ VALID
校验失败: 退出码 1，输出具体差异
"""

import json, sys
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


def main():
    if len(sys.argv) < 3:
        print("用法: python3 validate_yundong_pk_config.py <config.json> <game_type>")
        sys.exit(2)

    config_path, game_type = sys.argv[1], sys.argv[2]

    if game_type not in GAME_TYPE_MAP:
        print(f"未知 game_type: {game_type}，可选: {list(GAME_TYPE_MAP.keys())}")
        sys.exit(2)

    ref_path = REFERENCE_DIR / GAME_TYPE_MAP[game_type]
    if not ref_path.exists():
        print(f"参考配置不存在: {ref_path}")
        sys.exit(2)

    raw = Path(config_path).read_text().strip().strip("'")
    config = json.loads(raw)
    ref = json.loads(ref_path.read_text())

    ref_keys = collect_keys(ref)
    cfg_keys = collect_keys(config)

    # 只报参考配置有、但当前配置缺失的结构路径
    missing = sorted(ref_keys - cfg_keys)

    if not missing:
        print(f"✅ VALID — {config_path} 与 {game_type} 参考配置结构一致")
        sys.exit(0)
    else:
        print(f"❌ INVALID — 缺少 {len(missing)} 个结构路径（相对参考配置）:\n")
        for p in missing[:30]:
            print(f"  {p}")
        if len(missing) > 30:
            print(f"  ... 共 {len(missing)} 处")
        sys.exit(1)


if __name__ == "__main__":
    main()
