import json, urllib.request, sys

TOKEN = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ7XCJlbWFpbFwiOlwidl93dXFpbmdxaW5nMkB0YWwuY29tXCIsXCJlbXBOb1wiOlwiVjAwNTY3NzlcIixcImxvZ2luVGltZU91dFwiOjk2MCxcIm5hbWVcIjpcIuWQtOmdkumdklwiLFwicmVmcmVzaFRpbWVcIjpcIjIwMjYtMDUtMTIgMTM6NDU6MzZcIixcInJlZnJlc2hUaW1lT3V0XCI6MTB9IiwiZXhwIjoxNzc4NjIxNzM2fQ.oPL-_JksUNdBnptvqbBxhGiY0tEo8CSyHcFLqYE2iuo'
COOKIE = 'oneLoginToken=eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIzNDU3MzMiLCJleHAiOjE3Nzc0MDgxNDZ9.Nfc6iUN0aVhsQTcuWCy67aDW4Cbj3mD_ohCT1TuoZDs'

req = urllib.request.Request(
    'https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=27fead19-4dd3-11f1-b0f5-e648d636fd2c',
    headers={'beibotoken': TOKEN, 'Cookie': COOKIE}
)
with urllib.request.urlopen(req, timeout=15) as resp:
    r = json.loads(resp.read())

if r.get('code') != 0:
    print('ERROR:', r)
    sys.exit(1)

meta = r['result']
print(f'游戏名：{meta["game_name"]}')
cfg = json.loads(meta['configuration'])

with open('/home/148139_wy/.openclaw/workspace/CoursewareMaker_Automation_Toolkit/output/国际level2游泳暑8_fetched.json','w') as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)

print(f'顶层 keys: {list(cfg.keys())}')
for game in cfg.get('custom_game',[]):
    for i, topic in enumerate(game.get('topics',[])):
        tr = topic['title_res']
        print(f'  题{i+1}: titleBg={bool(tr.get("titleBg"))} icon={bool(tr.get("icon"))}')
        for opt in tr['options']:
            ot = opt['item']['opstionText']
            print(f'    {ot.get("MLabel")} | correct={opt["item"]["switch"]} | sz={ot.get("fontSize")} | bold={ot.get("isBold","未设置")}')
