#!/usr/bin/env python3
"""
批量抓取"开心游乐园"类游戏配置
用途：分析参考，不限于自己发布的游戏
输出：output/kaixin_refs/<game_id>.json
"""
import json, os, time, urllib.request, urllib.parse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, 'output/kaixin_refs')
os.makedirs(OUT_DIR, exist_ok=True)

# ─── 从浏览器复制最新值 ──────────────────────────────────────────────────────
TOKEN  = os.environ.get('GAMEMAKER_TOKEN', '')
COOKIE = os.environ.get('GAMEMAKER_COOKIE', '')

GATEWAY = 'https://sszt-gateway.speiyou.com'
HEADERS = {'beibotoken': TOKEN, 'Cookie': COOKIE, 'Content-Type': 'application/json'}

def get(path):
    req = urllib.request.Request(GATEWAY + path, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def fetch_all_games(keyword='开心游乐园', page_size=50):
    """分页拉取所有匹配游戏"""
    games = []
    page = 1
    while True:
        q = urllib.parse.urlencode({'page': page, 'pageSize': page_size,
                                    'game_name': keyword})
        d = get(f'/beibo/game/config/games?{q}')
        res = d.get('result', {})
        items = res.get('list') or res.get('records') or res.get('data') or res.get('games') or []
        games.extend(items)
        total = res.get('total', 0)
        print(f'  第{page}页: 获取 {len(items)} 条 (共 {total} 条)')
        if len(games) >= total or not items:
            break
        page += 1
        time.sleep(0.3)
    return games

def fetch_config(game_id):
    """获取单个游戏完整配置"""
    d = get(f'/beibo/game/config/game?game_id={game_id}')
    return d.get('result', {})

def main():
    if not TOKEN:
        print('❌ 请设置环境变量 GAMEMAKER_TOKEN')
        print('   export GAMEMAKER_TOKEN="eyJhbGci..."')
        print('   export GAMEMAKER_COOKIE="oneLoginToken=..."')
        return

    print('🔍 搜索"开心游乐园"游戏列表...')
    games = fetch_all_games()
    print(f'✅ 找到 {len(games)} 个游戏\n')

    # 保存游戏列表摘要
    summary_path = os.path.join(OUT_DIR, '_index.json')
    summary = [{'game_id': g.get('game_id'), 'game_name': g.get('game_name'),
                'template_id': g.get('template_id'), 'create_time': g.get('create_time')}
               for g in games]
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f'📋 列表已保存: {summary_path}')

    # 逐个抓取配置
    ok, skip, fail = 0, 0, 0
    for i, g in enumerate(games):
        gid  = g.get('game_id', '')
        name = g.get('game_name', '')
        out_path = os.path.join(OUT_DIR, f'{gid}.json')

        if os.path.exists(out_path):
            print(f'  [{i+1}/{len(games)}] ⏭  跳过（已存在）: {name}')
            skip += 1
            continue

        try:
            cfg = fetch_config(gid)
            # 排除 components 大字段（仅保留 configuration 内容）
            cfg.pop('components', None)
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            print(f'  [{i+1}/{len(games)}] ✅ {name} ({gid[:8]}...)')
            ok += 1
        except Exception as e:
            print(f'  [{i+1}/{len(games)}] ❌ {name}: {e}')
            fail += 1
        time.sleep(0.3)

    print(f'\n完成: ✅{ok} ⏭{skip} ❌{fail}')
    print(f'输出目录: {OUT_DIR}')

if __name__ == '__main__':
    main()
