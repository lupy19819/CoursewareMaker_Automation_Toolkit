const fs = require("fs");
const { chromium } = require("playwright");

(async () => {
  const port = process.env.CHROME_PORT || 9222;
  const browser = await chromium.connectOverCDP("http://127.0.0.1:" + port);
  const context = browser.contexts()[0];
  const page = context.pages().find(p => (p.url()||'').includes('coursewaremaker')) || context.pages()[0];
  
  const result = await page.evaluate(async (gameId) => {
    const tokenRaw = localStorage.getItem('GAMEMAKER_TOKEN');
    let token = null;
    try { token = JSON.parse(tokenRaw); } catch(e) { token = tokenRaw; }
    const res = await fetch('https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=' + gameId, {
      credentials: 'include',
      headers: token ? { beibotoken: token } : {}
    });
    const d = await res.json();
    return d.result?.configuration || d.data?.config_data || '';
  }, 'a525854c-4b73-11f1-b0f5-e648d636fd2c');
  
  if (result) {
    const parsed = JSON.parse(result);
    fs.writeFileSync('/tmp/guoqiao_server.json', JSON.stringify(parsed, null, 2));
    process.stdout.write('OK\n');
  }
  await browser.close();
})().catch(e => { process.stderr.write(e.message + '\n'); process.exit(1); });
