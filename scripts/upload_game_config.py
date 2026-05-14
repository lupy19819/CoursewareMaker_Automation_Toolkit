#!/usr/bin/env python3
"""
upload_game_config.py
将本地 JSON 配置文件上传（覆盖保存）到 CoursewareMaker 指定游戏。

用法：
    python3 scripts/upload_game_config.py <game_id> <config_json_path>

示例：
    python3 scripts/upload_game_config.py ad4d7659-4d0c-11f1-b0f5-e648d636fd2c output/guoqiao_shu2/guoqiao_shu2.json

说明：
    - 需先在脚本顶部配置 TOKEN/COOKIE，或通过环境变量传入
    - 保存语义与 CDP 脚本统一：GET /game 拿完整元信息，仅替换 configuration 后 PUT /game
    - configuration 字段以 dict 形式传入 payload，由 json.dumps 序列化一次（单层编码），服务器会再存一次
    - 若传 JSON 字符串，服务器会存成双重编码，导致引擎 analysisComponentsJson 崩溃

注意：
    - TOKEN 来自 localStorage.getItem('GAMEMAKER_TOKEN') 【必须】
    - COOKIE 来自 document.cookie 中的 oneLoginToken 【可选】
    - TOKEN 和 COOKIE 均有过期时间，需定期更新
    - 仅使用 TOKEN 模式已测试支持：配置上传 ✅  发布游戏 ⚠️（可能受限）

环境变量：
    GAMEMAKER_TOKEN   beibotoken 值（必须）
    GAMEMAKER_COOKIE  oneLoginToken=xxx 完整 cookie 字符串（可选）
"""

import json
import sys
import os
import urllib.request
import urllib.error

# ─── 配置区（优先读环境变量）────────────────────────────────────────────────
TOKEN = os.environ.get('GAMEMAKER_TOKEN', '')
COOKIE = os.environ.get('GAMEMAKER_COOKIE', '')

BASE_URL = 'https://sszt-gateway.speiyou.com/beibo/game/config'

# ─── 工具函数 ─────────────────────────────────────────────────────────────────

def api_get(path, token, cookie):
    req = urllib.request.Request(
        f'{BASE_URL}{path}',
        headers={'beibotoken': token, 'Cookie': cookie}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def api_put(path, payload, token, cookie):
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(
        f'{BASE_URL}{path}',
        data=body,
        headers={
            'beibotoken': token,
            'Cookie': cookie,
            'Content-Type': 'application/json; charset=utf-8',
        },
        method='PUT'
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


# ─── 主流程 ───────────────────────────────────────────────────────────────────

def upload_config(game_id: str, config_path: str, token: str, cookie: str):
    # 1. 读本地配置
    with open(config_path, encoding='utf-8') as f:
        cfg = json.load(f)
    print(f"✅ 本地配置已读取：{config_path}")
    print(f"   顶层 keys: {list(cfg.keys())}")
    print(f"   关卡数: {len(cfg.get('game', []))}")

    # 2. 获取游戏元信息（名称、模板等）
    r = api_get(f'/game?game_id={game_id}', token, cookie)
    if r.get('code') != 0:
        raise RuntimeError(f"获取游戏信息失败: {r}")
    meta = r['result']
    print(f"✅ 游戏信息已获取：{meta['game_name']} ({game_id})")

    # 3. 构建 PUT payload
    # 关键：保存语义与浏览器/CDP 脚本一致：
    # - 保留 GET /game 返回的完整元信息
    # - 仅替换 configuration
    # - configuration 传 dict（不是 JSON 字符串）
    payload = dict(meta)
    payload['components'] = payload.get('components') if isinstance(payload.get('components'), list) else []
    payload['configuration'] = cfg

    # 4. 保存
    result = api_put('/game', payload, token, cookie)
    if result.get('code') != 0:
        raise RuntimeError(f"保存失败: {result}")
    print(f"✅ 配置已保存！")

    # 5. 验证（回读解码层数）
    r2 = api_get(f'/game?game_id={game_id}', token, cookie)
    raw = r2['result']['configuration']
    parsed = json.loads(raw)
    if isinstance(parsed, dict):
        print(f"✅ 编码验证通过（单层），关卡数: {len(parsed.get('game', []))}")
    else:
        print(f"⚠️  仍为双重编码，请检查 payload 结构")

# ─── CLI 入口 ─────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    game_id = sys.argv[1]
    config_path = sys.argv[2]

    if not TOKEN:
        print("❌ 缺少 TOKEN，请设置环境变量 GAMEMAKER_TOKEN 或在脚本顶部填写")
        print("   从浏览器控制台获取：localStorage.getItem('GAMEMAKER_TOKEN')")
        sys.exit(1)

    if not COOKIE:
        print("⚠️  缺少 COOKIE，将只使用 TOKEN 进行认证")
        COOKIE = ""  # 设置为空字符串，让请求继续

    try:
        upload_config(game_id, config_path, TOKEN, COOKIE)
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP 错误: {e.code} {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)
