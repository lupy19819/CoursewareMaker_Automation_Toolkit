const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
  const ctx = browser.contexts()[0];
  const page = ctx.pages().find(p => p.url().includes('coursewaremaker'));
  
  // 不传参数，直接在evaluate内部读取token
  const result = await page.evaluate(async () => {
    const t = localStorage.getItem('GAMEMAKER_TOKEN');
    const search = async (key) => {
      const r = await fetch('https://sszt-gateway.speiyou.com/beibo/game/config/game/list?pageNum=1&pageSize=20&search_key=' + encodeURIComponent(key), {headers:{beibotoken:t}});
      const d = await r.json();
      return (d?.result?.list || []).map(g => ({id: g.game_id, name: g.game_name}));
    };
    const getConfig = async (id) => {
      const r = await fetch('https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=' + id, {headers:{beibotoken:t}});
      const d = await r.json();
      return d?.result?.configuration;
    };
    const list1 = await search('\u5f00\u5fc3\u6e38\u4e50\u56ed\u66257');
    const list2 = await search('\u8fc7\u6865\u5927\u5192\u9669\u79cb14');
    const k = list1.find(g => g.name.includes('level2') && g.name.includes('\u65747'));
    const g = list2.find(g => g.name.includes('\u8fc7\u6865') && g.name.includes('\u679c14'));
    return {
      list1: list1.slice(0,5),
      list2: list2.slice(0,5),
      kId: k?.id, kName: k?.name,
      gId: g?.id, gName: g?.name,
      kConfig: k ? await getConfig(k.id) : null,
      gConfig: g ? await getConfig(g.id) : null,
    };
  });
  
  console.log('开心游乐园候选:', JSON.stringify(result.list1));
  console.log('过桥大冒险候选:', JSON.stringify(result.list2));
  console.log('匹配开心游乐园:', result.kName, result.kId);
  console.log('匹配过桥大冒险:', result.gName, result.gId);
  
  if (result.kConfig) {
    fs.writeFileSync('reference_configs/kaixin_spring7_ref.json', result.kConfig);
    console.log('✅ 已保存 kaixin_spring7_ref.json, 长度:', result.kConfig.length);
  }
  if (result.gConfig) {
    fs.writeFileSync('reference_configs/guoqiao_autumn14_ref.json', result.gConfig);
    console.log('✅ 已保存 guoqiao_autumn14_ref.json, 长度:', result.gConfig.length);
  }
  
  await browser.close();
})().catch(e => console.error('Error:', e.message));
