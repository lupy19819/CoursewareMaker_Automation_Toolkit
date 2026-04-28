/**
 * 批量获取"公路大冒险"游戏配置
 * 
 * 使用方式（引用模式，只读）：
 *   node scripts/fetch_road_adventure_configs.js
 * 
 * 输出：
 *   ./output/road_adventure_configs/<game_id>.json  每个游戏的配置
 *   ./output/road_adventure_configs/index.json       游戏列表索引
 */

const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const CHROME_DEBUG_PORT = 9222;
const API_BASE = 'https://sszt-gateway.speiyou.com/beibo/game/config';
const KEYWORD = '公路大冒险';
const OUTPUT_DIR = path.join(__dirname, '../output/road_adventure_configs');

async function getToken(page) {
  const token = await page.evaluate(() => localStorage.getItem('GAMEMAKER_TOKEN'));
  if (!token) throw new Error('未找到 GAMEMAKER_TOKEN，请先登录 CoursewareMaker');
  return token;
}

/**
 * 分页获取所有包含关键词的游戏
 */
async function fetchAllGames(token) {
  const games = [];
  let page = 1;
  const pageSize = 40;

  while (true) {
    const url = `${API_BASE}/myGames?page=${page}&page_size=${pageSize}&game_name=${encodeURIComponent(KEYWORD)}&is_removed=0&is_published=-1&year=&term_id=&subject_id=&grade=&cnum_id=`;
    const res = await fetch(url, { headers: { beibotoken: token } });
    const json = await res.json();

    if (!json || json.code !== 0 || !json.result) {
      console.error('获取游戏列表失败:', JSON.stringify(json));
      break;
    }

    const list = json.result.list || [];
    games.push(...list);

    console.log(`  第 ${page} 页：获取到 ${list.length} 个游戏（已累计 ${games.length}）`);

    if (list.length < pageSize) break;
    page++;
  }

  return games;
}

/**
 * 通过 API 直接获取单个游戏配置（引用模式，不锁定）
 */
async function fetchGameConfig(token, gameId) {
  const url = `${API_BASE}/game?game_id=${gameId}`;
  const res = await fetch(url, { headers: { beibotoken: token } });
  const json = await res.json();

  if (!json || json.code !== 0 || !json.result) {
    throw new Error(`获取配置失败: ${JSON.stringify(json)}`);
  }

  const raw = json.result.configuration;
  if (!raw) return null;

  // 处理双重编码情况
  if (typeof raw === 'string') {
    try {
      return JSON.parse(raw);
    } catch {
      return raw;
    }
  }
  return raw;
}

async function main() {
  // 确保输出目录存在
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  // 连接 Chrome
  const browser = await puppeteer.connect({
    browserURL: `http://localhost:${CHROME_DEBUG_PORT}`,
    defaultViewport: null
  });

  const pages = await browser.pages();
  let cmPage = pages.find(p => p.url().includes('coursewaremaker.speiyou.com'));
  if (!cmPage) {
    cmPage = await browser.newPage();
    await cmPage.goto('https://coursewaremaker.speiyou.com');
    await new Promise(r => setTimeout(r, 2000));
  }

  console.log('✅ 已连接 Chrome');

  // 获取 token（在浏览器上下文中）
  const token = await getToken(cmPage);
  console.log('✅ 已获取 Token\n');

  // 在浏览器 context 中执行 API 请求（绕过 CORS）
  console.log(`🔍 搜索包含"${KEYWORD}"的游戏...`);

  const gamesRaw = await cmPage.evaluate(async ({ apiBase, keyword }) => {
    const token = localStorage.getItem('GAMEMAKER_TOKEN');
    const allGames = [];
    let page = 1;
    const pageSize = 40;

    while (true) {
      const url = `${apiBase}/myGames?page=${page}&page_size=${pageSize}&game_name=${encodeURIComponent(keyword)}&is_removed=0&is_published=-1&year=&term_id=&subject_id=&grade=&cnum_id=`;
      const res = await fetch(url, { headers: { beibotoken: token } });
      const json = await res.json();

      if (!json || json.code !== 0 || !json.result) break;

      const list = json.result.list || [];
      allGames.push(...list);

      if (list.length < pageSize) break;
      page++;
    }

    return allGames;
  }, { apiBase: API_BASE, keyword: KEYWORD });

  console.log(`📋 共找到 ${gamesRaw.length} 个游戏\n`);

  if (gamesRaw.length === 0) {
    console.log('未找到任何匹配游戏，退出。');
    await browser.disconnect();
    return;
  }

  // 保存游戏索引
  const index = gamesRaw.map(g => ({
    game_id: g.game_id,
    game_name: g.game_name,
    template_id: g.template_id,
    is_published: g.is_published,
    create_time: g.create_time,
    update_time: g.update_time || g.save_time,
  }));
  fs.writeFileSync(path.join(OUTPUT_DIR, 'index.json'), JSON.stringify(index, null, 2), 'utf8');
  console.log(`✅ 游戏索引已保存 → output/road_adventure_configs/index.json\n`);

  // 逐个获取配置
  const results = { success: [], failed: [] };

  for (let i = 0; i < gamesRaw.length; i++) {
    const game = gamesRaw[i];
    const { game_id, game_name } = game;
    console.log(`[${i + 1}/${gamesRaw.length}] 获取配置: ${game_name} (${game_id})`);

    try {
      const config = await cmPage.evaluate(async ({ apiBase, gameId }) => {
        const token = localStorage.getItem('GAMEMAKER_TOKEN');
        const res = await fetch(`${apiBase}/game?game_id=${gameId}`, {
          headers: { beibotoken: token }
        });
        const json = await res.json();
        if (!json || json.code !== 0 || !json.result) {
          throw new Error(JSON.stringify(json));
        }
        const raw = json.result.configuration;
        if (!raw) return null;
        if (typeof raw === 'string') {
          try { return JSON.parse(raw); } catch { return raw; }
        }
        return raw;
      }, { apiBase: API_BASE, gameId: game_id });

      if (!config) {
        console.log(`  ⚠️  配置为空，跳过`);
        results.failed.push({ game_id, game_name, reason: '配置为空' });
        continue;
      }

      const outPath = path.join(OUTPUT_DIR, `${game_id}.json`);
      fs.writeFileSync(outPath, JSON.stringify(config, null, 2), 'utf8');
      console.log(`  ✅ 已保存`);
      results.success.push({ game_id, game_name, path: outPath });

      // 避免请求过快
      await new Promise(r => setTimeout(r, 300));

    } catch (err) {
      console.log(`  ❌ 失败: ${err.message}`);
      results.failed.push({ game_id, game_name, reason: err.message });
    }
  }

  // 输出汇总
  console.log(`\n========== 完成 ==========`);
  console.log(`✅ 成功: ${results.success.length} 个`);
  console.log(`❌ 失败: ${results.failed.length} 个`);
  if (results.failed.length > 0) {
    results.failed.forEach(f => console.log(`  - ${f.game_name}: ${f.reason}`));
  }
  console.log(`\n📁 配置文件保存在: ${OUTPUT_DIR}`);

  fs.writeFileSync(
    path.join(OUTPUT_DIR, 'fetch_result.json'),
    JSON.stringify(results, null, 2),
    'utf8'
  );

  await browser.disconnect();
}

main().catch(err => {
  console.error('❌ 脚本执行出错:', err);
  process.exit(1);
});
