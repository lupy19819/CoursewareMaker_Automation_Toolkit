const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
  const pages = browser.contexts()[0].pages();
  const page = pages.find(p => p.url().includes('coursewaremaker')) || pages[0];
  
  await page.evaluate(t => { window._oc_token = t; }, await page.evaluate(() => localStorage.getItem('GAMEMAKER_TOKEN')));
  
  const kConfig = fs.readFileSync('output/kaixin_shu2_final.json', 'utf8');
  const gConfig = fs.readFileSync('output/guoqiao_shu2_final.json', 'utf8');
  
  const kaixinId = '57cd2b7b-4b73-11f1-b0f5-e648d636fd2c';   // 国际level2开心游乐园暑2
  const guoqiaoId = '2f6b1cd3-4b75-11f1-b0f5-e648d636fd2c';  // 26国际level2过桥大冒险暑2
  
  async function updateGame(gameId, config, name) {
    return page.evaluate(async ([gid, cfg]) => {
      const t = window._oc_token;
      // 先获取现有游戏信息
      const getR = await fetch('https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=' + gid, {
        headers: { beibotoken: t }
      });
      const getData = await getR.json();
      if (!getData.result) return { error: 'game not found', code: getData.code };
      
      const existing = getData.result;
      // 更新配置（POST update）
      const putR = await fetch('https://sszt-gateway.speiyou.com/beibo/game/config/game', {
        method: 'POST',
        headers: { beibotoken: t, 'Content-Type': 'application/json;charset=UTF-8' },
        body: JSON.stringify({
          game_id: gid,
          game_name: existing.game_name,
          template_id: existing.template_id,
          game_type: existing.game_type || 1,
          configuration: cfg,
          picture: existing.picture || '',
        })
      });
      return await putR.json();
    }, [gameId, config]);
  }
  
  console.log('更新开心游乐园暑2...');
  const r1 = await updateGame(kaixinId, kConfig, '国际level2开心游乐园暑2');
  console.log('结果:', JSON.stringify({ code: r1.code, msg: r1.message }));
  
  console.log('更新26国际level2过桥大冒险暑2...');
  const r2 = await updateGame(guoqiaoId, gConfig, '26国际level2过桥大冒险暑2');
  console.log('结果:', JSON.stringify({ code: r2.code, msg: r2.message }));
  
  await browser.close();
})().catch(e => console.error('Error:', e.message));
