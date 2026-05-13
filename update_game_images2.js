/**
 * 更新暑5d1/d2游戏图片（节点_37）并保存
 * 使用PUT /beibo/game/config/game，需携带完整detailMeta
 */
const http = require('http');
const https = require('https');
const WebSocket = require('./node_modules/ws/lib/websocket.js');

const BASE = 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0056779/2026-05-11/';
const WORD_TO_IMG = {
  'kid': BASE + '9db97cfaf8201ef211de8c2f7ccc4c07.png',
  'granddaughter': BASE + 'a9bf0aab6d50d560782a5cee81fa9b63.png',
  'grandson': BASE + '22b6e2ac40eeed75b1663d972b7d8f9f.png',
  'grown-up': BASE + '263aa344cfeed9ba9f2f6a5476bfb841.png',
  'daughter': BASE + '33296c7db39951cf2e88e2ed6b2ce620.png',
  'son': BASE + '8a28d777134ba1b2ce82ff073a2362dc.png',
  'grandparent': BASE + 'ecef1a753816a6fd34bc44aea10a23a2.png',
  'grandchildren': BASE + 'abda6886001db661d4057a8114fcb83e.png',
};

function httpsReq(method, path, headers, body) {
  return new Promise((resolve, reject) => {
    const bodyStr = body ? JSON.stringify(body) : null;
    const opts = {
      hostname: 'sszt-gateway.speiyou.com', path, method,
      headers: { ...headers, ...(bodyStr ? { 'Content-Type': 'application/json;charset=UTF-8', 'Content-Length': Buffer.byteLength(bodyStr) } : {}) }
    };
    const req = https.request(opts, res => {
      let d = ''; res.on('data', c => d += c); res.on('end', () => {
        try { resolve(JSON.parse(d)); } catch (e) { resolve({ _raw: d.slice(0, 200) }); }
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
  if (!TOKEN) { console.error('Failed to get GAMEMAKER_TOKEN'); process.exit(1); }
  console.log('Token:', TOKEN.slice(0, 30) + '...');

  const games = [
    ['暑5d1', '7be1e474-4b98-11f1-a80e-6effa3ce9c89'],
    ['暑5d2', 'd3694c3c-4b98-11f1-b0f5-e648d636fd2c']
  ];

  for (const [name, gid] of games) {
    console.log(`\n=== ${name} ===`);

    // GET full game detail
    const gameData = await httpsReq('GET', `/beibo/game/config/game?game_id=${gid}`, { beibotoken: TOKEN });
    if (gameData.code !== 0) { console.error('Fetch failed:', gameData); continue; }

    const { components: _omit, ...detailMeta } = gameData.result;
    const cfg = JSON.parse(detailMeta.configuration);

    // Update 节点_37 images
    let updated = 0, words = [];
    for (const lv of cfg.game) {
      let word = '';
      for (const comp of lv.components) {
        if (comp.component_data?.name === '文本-fin') {
          for (const st of (comp.component_data.states || [])) {
            if (st.state === 'default') { word = st.source?.MLabel?.value || ''; break; }
          }
        }
      }
      words.push(word);
      if (word && WORD_TO_IMG[word]) {
        for (const comp of lv.components) {
          if (comp.component_data?.name === '节点_37') {
            for (const st of (comp.component_data.states || [])) {
              if (st.source?.MSprite) { st.source.MSprite.value = WORD_TO_IMG[word]; updated++; }
            }
          }
        }
      }
    }
    console.log(`Words: [${words.join(', ')}] | Updated: ${updated}`);

    // PUT save
    const payload = { ...detailMeta, configuration: JSON.stringify(cfg) };
    const saveData = await httpsReq('PUT', '/beibo/game/config/game', { beibotoken: TOKEN }, payload);
    console.log(`Save: code=${saveData.code} msg=${saveData.msg || saveData._raw || 'ok'}`);
  }
}

main().catch(console.error);
