/**
 * 批量获取"单词拼拼乐"游戏配置（引用模式，只读）
 * node scripts/fetch_spelling_configs.js
 */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const CHROME_DEBUG_PORT = 9222;
const API_BASE = 'https://sszt-gateway.speiyou.com/beibo/game/config';
const KEYWORD = '单词拼拼乐';
const OUTPUT_DIR = path.join(__dirname, '../output/spelling_configs');

(async () => {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const browser = await puppeteer.connect({
    browserURL: `http://localhost:${CHROME_DEBUG_PORT}`,
    defaultViewport: null,
  });

  const pages = await browser.pages();
  let cmPage = pages.find(p => p.url().includes('coursewaremaker.speiyou.com') || p.url().includes('speiyou'));
  if (!cmPage) throw new Error('未找到 CoursewareMaker 标签页');

  console.log('✅ 已连接 Chrome');

  // 在浏览器上下文中执行所有请求
  const result = await cmPage.evaluate(async ({ apiBase, keyword }) => {
    const token = localStorage.getItem('GAMEMAKER_TOKEN');
    if (!token) throw new Error('未找到 GAMEMAKER_TOKEN');

    // 获取游戏列表
    const games = [];
    let page = 1;
    while (true) {
      const url = `${apiBase}/myGames?page=${page}&page_size=40&game_name=${encodeURIComponent(keyword)}&is_removed=0&is_published=-1&year=&term_id=&subject_id=&grade=&cnum_id=`;
      const res = await fetch(url, { headers: { beibotoken: token } });
      const json = await res.json();
      if (!json || json.code !== 0 || !json.result) break;
      const list = json.result.list || [];
      games.push(...list);
      if (list.length < 40) break;
      page++;
    }

    // 获取每个游戏配置
    const configs = [];
    for (const game of games) {
      try {
        const res = await fetch(`${apiBase}/game?game_id=${game.game_id}`, { headers: { beibotoken: token } });
        const json = await res.json();
        if (json && json.code === 0 && json.result) {
          let config = json.result.configuration;
          if (typeof config === 'string') { try { config = JSON.parse(config); } catch(e) {} }
          configs.push({ meta: game, config });
        }
      } catch(e) {
        configs.push({ meta: game, error: e.message });
      }
    }
    return configs;
  }, { apiBase: API_BASE, keyword: KEYWORD });

  const index = [];
  for (const item of result) {
    if (item.error) {
      console.error(`❌ ${item.meta.game_name}: ${item.error}`);
      continue;
    }
    const outPath = path.join(OUTPUT_DIR, `${item.meta.game_id}.json`);
    fs.writeFileSync(outPath, JSON.stringify(item.config, null, 2));
    index.push({ game_id: item.meta.game_id, name: item.meta.game_name, grade: item.meta.grade, subject: item.meta.subject_id });
    console.log(`✅ ${item.meta.game_name}`);
  }

  fs.writeFileSync(path.join(OUTPUT_DIR, 'index.json'), JSON.stringify(index, null, 2));
  console.log(`\n完成！共保存 ${index.length} 个配置`);
  process.exit(0);
})().catch(e => { console.error(e); process.exit(1); });
