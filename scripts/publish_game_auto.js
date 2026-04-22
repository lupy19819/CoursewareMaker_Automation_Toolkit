/**
 * CoursewareMaker 自动发布游戏脚本
 *
 * 使用方法:
 * node publish_game_auto.js <game_id> <year> <term_id> <grade> [desc]
 *
 * 示例:
 * node publish_game_auto.js "b82175b7-395f-11f1-bdd1-76b63c7cf458" 2026 2 5
 */

const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

// 配置项
const API_BASE = 'https://sszt-gateway.speiyou.com/beibo/game/config';
const CHROME_DEBUG_PORT = 9222;

// 学科映射
const SUBJECT_MAP = {
  '数学': '1',
  'math': '1'
};

// 学期映射
const TERM_MAP = {
  '春季': '1',
  '秋季': '2',
  'spring': '1',
  'fall': '2'
};

// 年级映射
const GRADE_MAP = {
  '一年级': '1',
  '二年级': '2',
  '三年级': '3',
  '四年级': '4',
  '五年级': '5',
  '六年级': '6'
};

async function getToken() {
  try {
    const browser = await puppeteer.connect({
      browserURL: `http://localhost:${CHROME_DEBUG_PORT}`,
      defaultViewport: null
    });

    const pages = await browser.pages();
    const page = pages[0];

    const token = await page.evaluate(() => {
      return localStorage.getItem('GAMEMAKER_TOKEN');
    });

    if (!token) {
      throw new Error('未找到 GAMEMAKER_TOKEN，请先在浏览器中登录 CoursewareMaker');
    }

    return token;
  } catch (error) {
    console.error('❌ 获取Token失败:', error.message);
    throw error;
  }
}

async function publishGame(gameId, publishConfig) {
  const token = await getToken();

  console.log(`\n🎮 开始发布游戏: ${gameId}`);
  console.log(`📊 发布配置:`, JSON.stringify(publishConfig, null, 2));

  const headers = {
    'beibotoken': token,
    'content-type': 'application/json;charset=UTF-8',
    'origin': 'https://coursewaremaker.speiyou.com',
    'referer': 'https://coursewaremaker.speiyou.com/'
  };

  // 步骤1: 设置发布信息
  console.log('\n📤 步骤1: 设置发布信息...');
  const publishPayload = {
    year: publishConfig.year,
    term_id: publishConfig.term_id,
    subject_id: publishConfig.subject_id || '1',
    grade: publishConfig.grade,
    cnum_id: publishConfig.cnum_id || '31',
    is_experiential_game: 0,
    is_diagnose: publishConfig.is_diagnose !== undefined ? publishConfig.is_diagnose : 1,
    engine_version: '3.X',
    desc: publishConfig.desc || '',
    source: 1,
    knowledge: publishConfig.knowledge || [],
    skill_tag: 0,
    is_level: 0,
    settlement_type: 0,
    is_play: 1,
    is_syn: 1,
    game_id: gameId
  };

  const publishRes = await fetch(`${API_BASE}/gamePublish`, {
    method: 'PUT',
    headers: headers,
    body: JSON.stringify(publishPayload)
  });
  const publishData = await publishRes.json();

  if (publishData.code !== 0) {
    throw new Error(`设置发布信息失败: ${publishData.msg}`);
  }
  console.log('✅ 发布信息设置成功');

  // 步骤2: 更新游戏描述
  console.log('\n📤 步骤2: 更新游戏描述...');
  const descPayload = {
    game_id: gameId,
    desc: publishConfig.desc || ''
  };

  const descRes = await fetch(`${API_BASE}/gameDesc`, {
    method: 'PUT',
    headers: headers,
    body: JSON.stringify(descPayload)
  });
  const descData = await descRes.json();

  if (descData.code !== 0) {
    throw new Error(`更新描述失败: ${descData.msg}`);
  }
  console.log('✅ 游戏描述更新成功');

  // 步骤3: 加入构建队列（实际发布）
  console.log('\n📤 步骤3: 加入构建队列（发布游戏）...');
  const buildPayload = {
    game_id: gameId
  };

  const buildRes = await fetch(`${API_BASE}/build_queue`, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(buildPayload)
  });
  const buildData = await buildRes.json();

  if (buildData.code !== 0) {
    throw new Error(`加入构建队列失败: ${buildData.msg}`);
  }
  console.log('✅ 游戏已加入构建队列');

  // 步骤4: 解锁游戏
  console.log('\n📤 步骤4: 解锁游戏...');
  const unlockPayload = {
    game_id: gameId
  };

  const unlockRes = await fetch(`${API_BASE}/unlock`, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(unlockPayload)
  });
  const unlockData = await unlockRes.json();

  if (unlockData.code !== 0) {
    console.warn(`⚠️  解锁游戏失败: ${unlockData.msg}（这通常不影响发布）`);
  } else {
    console.log('✅ 游戏已解锁');
  }

  console.log('\n✅ 游戏发布成功！');
  return {
    success: true,
    game_id: gameId,
    publish_config: publishConfig
  };
}

async function batchPublish(gameList, publishConfig) {
  console.log(`\n🚀 开始批量发布 ${gameList.length} 个游戏...\n`);

  const results = [];

  for (let i = 0; i < gameList.length; i++) {
    const game = gameList[i];
    console.log(`\n[${ i + 1}/${gameList.length}] 发布游戏: ${game.game_id}`);

    try {
      // 如果游戏有自己的配置，使用游戏配置，否则使用默认配置
      const config = game.publish_config || publishConfig;

      const result = await publishGame(game.game_id, config);
      results.push({
        ...result,
        game_name: game.game_name || `游戏${i + 1}`,
        status: 'success'
      });

      console.log(`✅ [${i + 1}/${gameList.length}] ${game.game_name || game.game_id} 发布成功`);

      // 等待1秒，避免触发限流
      if (i < gameList.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    } catch (error) {
      console.error(`❌ [${i + 1}/${gameList.length}] ${game.game_name || game.game_id} 发布失败:`, error.message);
      results.push({
        game_id: game.game_id,
        game_name: game.game_name || `游戏${i + 1}`,
        status: 'failed',
        error: error.message
      });
    }
  }

  // 保存结果
  const timestamp = Date.now();
  const resultFile = path.join(__dirname, `publish_results_${timestamp}.json`);
  fs.writeFileSync(resultFile, JSON.stringify(results, null, 2));
  console.log(`\n📁 发布结果已保存到: ${resultFile}`);

  // 统计
  const successCount = results.filter(r => r.status === 'success').length;
  const failedCount = results.filter(r => r.status === 'failed').length;

  console.log('\n📊 批量发布完成:');
  console.log(`  ✅ 成功: ${successCount} 个`);
  console.log(`  ❌ 失败: ${failedCount} 个`);
  console.log(`  📝 总计: ${results.length} 个`);

  return results;
}

// 主函数
(async () => {
  try {
    const args = process.argv.slice(2);

    if (args.length === 0) {
      console.log(`
CoursewareMaker 自动发布游戏脚本

用法:
  单个游戏发布:
    node publish_game_auto.js <game_id> <year> <term_id> <grade> [desc]

  批量发布:
    node publish_game_auto.js --batch <games_json_file> <year> <term_id> <grade>

参数说明:
  game_id    - 游戏ID
  year       - 年份 (如: 2026)
  term_id    - 学期ID ("1"=春季, "2"=秋季)
  grade      - 年级 ("1"-"6")
  desc       - 游戏描述 (可选)

批量发布的JSON文件格式:
[
  {
    "game_id": "游戏ID1",
    "game_name": "游戏名称1"
  },
  {
    "game_id": "游戏ID2",
    "game_name": "游戏名称2"
  }
]

示例:
  node publish_game_auto.js "b82175b7-395f-11f1-bdd1-76b63c7cf458" 2026 2 5
  node publish_game_auto.js --batch xinyi_games.json 2026 2 1
      `);
      process.exit(0);
    }

    if (args[0] === '--batch') {
      // 批量发布模式
      const gamesFile = args[1];
      const year = parseInt(args[2]);
      const termId = args[3];
      const grade = args[4];

      if (!fs.existsSync(gamesFile)) {
        throw new Error(`游戏列表文件不存在: ${gamesFile}`);
      }

      const gameList = JSON.parse(fs.readFileSync(gamesFile, 'utf-8'));

      const publishConfig = {
        year: year,
        term_id: termId,
        grade: grade,
        subject_id: '1', // 默认数学
        cnum_id: '31',
        is_diagnose: 1,
        desc: ''
      };

      await batchPublish(gameList, publishConfig);
    } else {
      // 单个游戏发布模式
      const gameId = args[0];
      const year = parseInt(args[1]);
      const termId = args[2];
      const grade = args[3];
      const desc = args[4] || '';

      const publishConfig = {
        year: year,
        term_id: termId,
        grade: grade,
        subject_id: '1', // 默认数学
        cnum_id: '31',
        is_diagnose: 1,
        desc: desc
      };

      await publishGame(gameId, publishConfig);
    }

    process.exit(0);
  } catch (error) {
    console.error('\n❌ 发布失败:', error.message);
    process.exit(1);
  }
})();
