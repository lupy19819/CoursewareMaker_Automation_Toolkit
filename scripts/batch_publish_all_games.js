/**
 * 批量发布新一和新二年级的游戏
 * 使用 CoursewareMaker API
 */

const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

// 配置
const CONFIG = {
  chromeDebugPort: 9222,
  apiBase: 'https://sszt-gateway.speiyou.com/beibo/game/config',
  year: 2026,
  term_id: "2",        // 暑期（用户说"跟刚才监听的一样"）
  subject_id: "1",     // 数学
  cnum_id: "31",       // 通用课次
  is_diagnose: 1,      // 诊断游戏
  engine_version: "3.X"
};

// 读取游戏ID列表
const xinyiGames = JSON.parse(fs.readFileSync('D:/codexProject/xinyi_game_id_list.json', 'utf-8'));
const xinerGames = JSON.parse(fs.readFileSync('D:/codexProject/xiner_game_id_list.json', 'utf-8'));

// 获取Token
async function getToken(page) {
  return await page.evaluate(() => {
    return localStorage.getItem('GAMEMAKER_TOKEN');
  });
}

// 发布单个游戏（4步流程）
async function publishGame(token, gameId, gameName, grade) {
  console.log(`\n🎮 开始发布: ${gameName} (${gameId})`);

  const headers = {
    'beibotoken': token,
    'content-type': 'application/json;charset=UTF-8'
  };

  try {
    // 步骤1: 设置发布信息
    const publishPayload = {
      year: CONFIG.year,
      term_id: CONFIG.term_id,
      subject_id: CONFIG.subject_id,
      grade: grade,
      cnum_id: CONFIG.cnum_id,
      is_experiential_game: 0,
      is_diagnose: CONFIG.is_diagnose,
      engine_version: CONFIG.engine_version,
      desc: "",
      source: 1,
      knowledge: [],
      skill_tag: 0,
      is_level: 0,
      settlement_type: 0,
      is_play: 1,
      is_syn: 1,
      game_id: gameId
    };

    const publishResp = await fetch(`${CONFIG.apiBase}/gamePublish`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(publishPayload)
    });
    const publishData = await publishResp.json();

    if (publishData.code !== 0) {
      throw new Error(`gamePublish失败: ${publishData.msg}`);
    }
    console.log(`  ✅ 步骤1: 发布信息设置成功`);

    // 步骤2: 更新游戏描述
    const descResp = await fetch(`${CONFIG.apiBase}/gameDesc`, {
      method: 'PUT',
      headers,
      body: JSON.stringify({ game_id: gameId, desc: "" })
    });
    const descData = await descResp.json();

    if (descData.code !== 0) {
      throw new Error(`gameDesc失败: ${descData.msg}`);
    }
    console.log(`  ✅ 步骤2: 描述更新成功`);

    // 步骤3: 加入构建队列（实际发布）
    const buildResp = await fetch(`${CONFIG.apiBase}/build_queue`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ game_id: gameId })
    });
    const buildData = await buildResp.json();

    if (buildData.code !== 0) {
      throw new Error(`build_queue失败: ${buildData.msg}`);
    }
    console.log(`  ✅ 步骤3: 构建队列加入成功`);

    // 步骤4: 解锁游戏
    const unlockResp = await fetch(`${CONFIG.apiBase}/unlock`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        id: gameId,
        version: "0.0",
        type: "game"
      })
    });
    const unlockData = await unlockResp.json();

    if (unlockData.code !== 0) {
      throw new Error(`unlock失败: ${unlockData.msg}`);
    }
    console.log(`  ✅ 步骤4: 游戏解锁成功`);

    console.log(`✅ ${gameName} 发布成功！`);
    return { success: true, gameId, gameName };

  } catch (error) {
    console.error(`❌ ${gameName} 发布失败: ${error.message}`);
    return { success: false, gameId, gameName, error: error.message };
  }
}

// 主函数
async function main() {
  console.log('🚀 开始批量发布游戏...\n');

  // 连接到已运行的Chrome
  const browser = await puppeteer.connect({
    browserURL: `http://localhost:${CONFIG.chromeDebugPort}`,
    defaultViewport: null
  });

  const pages = await browser.pages();
  const page = pages[0];

  // 获取Token
  const token = await getToken(page);
  if (!token) {
    console.error('❌ 无法获取GAMEMAKER_TOKEN，请确保已登录CoursewareMaker');
    process.exit(1);
  }
  console.log('✅ Token获取成功\n');

  const results = {
    xinyi: [],
    xiner: [],
    summary: { total: 0, success: 0, failed: 0 }
  };

  // 发布新一年级（grade="1"）
  console.log('\n📚 ========== 新一年级（一年级）========== \n');
  for (const game of xinyiGames) {
    const result = await publishGame(token, game.gameId, game.gameName, "1");
    results.xinyi.push(result);
    results.summary.total++;
    if (result.success) {
      results.summary.success++;
    } else {
      results.summary.failed++;
    }
    await new Promise(resolve => setTimeout(resolve, 1000)); // 延迟1秒
  }

  // 发布新二年级（grade="2"）
  console.log('\n📚 ========== 新二年级（二年级）========== \n');
  for (const game of xinerGames) {
    const result = await publishGame(token, game.gameId, game.gameName, "2");
    results.xiner.push(result);
    results.summary.total++;
    if (result.success) {
      results.summary.success++;
    } else {
      results.summary.failed++;
    }
    await new Promise(resolve => setTimeout(resolve, 1000)); // 延迟1秒
  }

  // 保存结果
  const timestamp = Date.now();
  fs.writeFileSync(
    `D:/codexProject/batch_publish_results_${timestamp}.json`,
    JSON.stringify(results, null, 2)
  );

  // 打印总结
  console.log('\n' + '='.repeat(60));
  console.log('📊 批量发布完成！');
  console.log('='.repeat(60));
  console.log(`✅ 成功: ${results.summary.success}/${results.summary.total}`);
  console.log(`❌ 失败: ${results.summary.failed}/${results.summary.total}`);
  console.log(`📁 详细结果已保存: batch_publish_results_${timestamp}.json`);
  console.log('='.repeat(60));

  await browser.disconnect();
}

main().catch(console.error);
