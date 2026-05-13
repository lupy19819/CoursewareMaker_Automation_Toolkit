const http = require('http');
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

async function getTabWs() {
  return new Promise((r, rej) => http.get('http://127.0.0.1:18800/json/list', res => {
    let d = ''; res.on('data', c => d += c); res.on('end', () => r(JSON.parse(d)[0]?.webSocketDebuggerUrl));
  }).on('error', rej));
}

async function main() {
  const wsUrl = await getTabWs();
  const ws = new WebSocket(wsUrl);
  let id = 0; const pending = new Map();
  ws.on('message', data => {
    const m = JSON.parse(data);
    if (m.id && pending.has(m.id)) { const { res } = pending.get(m.id); pending.delete(m.id); res(m); }
  });
  await new Promise(r => ws.on('open', r));
  const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, { res: r }); ws.send(JSON.stringify({ id: i, method, params })); });

  const games = [
    ['d1', '7be1e474-4b98-11f1-a80e-6effa3ce9c89'],
    ['d2', 'd3694c3c-4b98-11f1-b0f5-e648d636fd2c']
  ];

  for (const [day, gid] of games) {
    console.log(`\nProcessing ${day} (${gid})...`);

    // Step 1: fetch config
    const fetchCode = `(async()=>{const tok=localStorage.getItem('GAMEMAKER_TOKEN');const r=await fetch('https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=${gid}',{credentials:'include',headers:{beibotoken:tok}});const d=await r.json();return d.result.configuration;})()`;
    const fetchR = await send('Runtime.evaluate', { expression: fetchCode, returnByValue: true, awaitPromise: true });
    const configStr = fetchR?.result?.result?.value;
    if (!configStr) { console.log('Failed to fetch config'); continue; }

    const cfg = JSON.parse(configStr);

    // Step 2: update images
    let updated = 0, words = [];
    for (const lv of cfg.game) {
      let word = '';
      for (const comp of lv.components) {
        if (comp.component_data && comp.component_data.name === '文本-fin') {
          for (const st of (comp.component_data.states || [])) {
            if (st.state === 'default') { word = (st.source && st.source.MLabel) ? st.source.MLabel.value : ''; break; }
          }
        }
      }
      words.push(word);
      if (word && WORD_TO_IMG[word]) {
        for (const comp of lv.components) {
          if (comp.component_data && comp.component_data.name === '节点_37') {
            for (const st of (comp.component_data.states || [])) {
              if (st.source && st.source.MSprite) { st.source.MSprite.value = WORD_TO_IMG[word]; updated++; }
            }
          }
        }
      }
    }
    console.log(`Words: ${words.join(', ')} | Images updated: ${updated}`);

    // Step 3: save via browser (needs credentials)
    const newCfgStr = JSON.stringify(cfg).replace(/'/g, "\\'");
    const saveCode = `(async()=>{const tok=localStorage.getItem('GAMEMAKER_TOKEN');const sr=await fetch('https://sszt-gateway.speiyou.com/beibo/game/config/save',{method:'POST',credentials:'include',headers:{beibotoken:tok,'Content-Type':'application/json'},body:JSON.stringify({game_id:'${gid}',configuration:JSON.stringify(${JSON.stringify(cfg)})})});const sd=await sr.json();return JSON.stringify({code:sd.code,msg:sd.msg});})()`;
    const saveR = await send('Runtime.evaluate', { expression: saveCode, returnByValue: true, awaitPromise: true });
    console.log(`Save result: ${saveR?.result?.result?.value}`);
  }

  ws.close();
}

main().catch(console.error);
