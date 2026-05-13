/**
 * 修复游戏的 template_id：从单词拼拼乐改为魔法拼拼乐（空）
 */
const http = require('http');
const https = require('https');
const WebSocket = require('./node_modules/ws/lib/websocket.js');

function httpsReq(method, path, headers, body) {
  return new Promise((resolve, reject) => {
    const bodyStr = body ? JSON.stringify(body) : null;
    const opts = {
      hostname: 'sszt-gateway.speiyou.com', path, method,
      headers: { ...headers, ...(bodyStr ? { 'Content-Type': 'application/json;charset=UTF-8', 'Content-Length': Buffer.byteLength(bodyStr) } : {}) }
    };
    const req = https.request(opts, res => {
      let d = ''; res.on('data', c => d += c); res.on('end', () => {
        try { resolve(JSON.parse(d)); } catch (e) { resolve({ _raw: d.slice(0, 300) }); }
      });
    });
    req.on('error', reject);
    if (bodyStr) req.write(bodyStr);
    req.end();
  });
}

async function getToken() {
  const wsUrl = await new Promise((r, rej) => http.get('http://127.0.0.1:18800/json/list', res => {
    let d = ''; res.on('data', c => d += c); res.on('end', () => r(JSON.parse(d)[0]?.webSocketDebuggerUrl));
  }).on('error', rej));
  const ws = new WebSocket(wsUrl);
  let id = 0; const pending = new Map();
  ws.on('message', data => { const m = JSON.parse(data); if (m.id && pending.has(m.id)) { const { res } = pending.get(m.id); pending.delete(m.id); res(m); } });
  await new Promise(r => ws.on('open', r));
  const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, { res: r }); ws.send(JSON.stringify({ id: i, method, params })); });
  const r = await send('Runtime.evaluate', { expression: "localStorage.getItem('GAMEMAKER_TOKEN')", returnByValue: true });
  ws.close();
  return r?.result?.result?.value;
}

async function main() {
  const TOKEN = await getToken();

  const games = [
    ['暑5d1', '7be1e474-4b98-11f1-a80e-6effa3ce9c89'],
    ['暑5d2', 'd3694c3c-4b98-11f1-b0f5-e648d636fd2c']
  ];

  // 国际level2魔法拼拼乐春5 的 parent_id 作为参考
  const MOFAPPL_PARENT_ID = 'de4e77fe-bbac-11f0-885a-ba4dce53cceb';

  for (const [name, gid] of games) {
    console.log(`\n=== ${name} ===`);

    const gameData = await httpsReq('GET', `/beibo/game/config/game?game_id=${gid}`, { beibotoken: TOKEN });
    if (gameData.code !== 0) { console.error('Fetch failed:', gameData); continue; }

    const { components: _omit, ...detailMeta } = gameData.result;

    // 解析配置（修复可能的双重序列化）
    let cfg = detailMeta.configuration;
    if (typeof cfg === 'string') {
      cfg = JSON.parse(cfg);
      if (typeof cfg === 'string') cfg = JSON.parse(cfg);
    }

    console.log(`Current template_id: "${detailMeta.template_id}" → 改为 ""`);
    console.log(`Current parent_id: "${detailMeta.parent_id}" → 改为 "${MOFAPPL_PARENT_ID}"`);

    const payload = {
      ...detailMeta,
      template_id: '',           // 清空 template_id
      parent_id: MOFAPPL_PARENT_ID,  // 设为魔法拼拼乐的 parent
      configuration: cfg         // 传对象（不是字符串）
    };

    const saveData = await httpsReq('PUT', '/beibo/game/config/game', { beibotoken: TOKEN }, payload);
    console.log(`Save: code=${saveData.code} msg=${saveData.msg || saveData._raw}`);
  }
}

main().catch(console.error);
