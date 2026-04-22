/**
 * 批量创建并配置新一年级游戏
 * 游戏命名：2026新一思维全能力诊断1~12
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// 配置
const CONFIG_DIR = 'D:/codexProject/generated_configs/xinyi_split_12_games';
const TEMPLATE_ID = '70a3010b-0b7a-11ef-b3a3-fa7902489df6'; // 拖拽类游戏模板
const GAME_NAME_PREFIX = '2026新一思维全能力诊断';
const CDP_PORT = 9222;

// 结果记录
const results = [];
const logFile = 'D:/codexProject/batch_xinyi_creation.log';

function log(message) {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] ${message}`;
  console.log(logMessage);
  fs.appendFileSync(logFile, logMessage + '\n');
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function getAuthInfo() {
  try {
    const response = await fetch(`http://localhost:${CDP_PORT}/json/version`);
    const data = await response.json();
    const wsUrl = data.webSocketDebuggerUrl;

    const playwright = require('playwright');
    const browser = await playwright.chromium.connectOverCDP(`http://localhost:${CDP_PORT}`);
    const context = browser.contexts()[0];
    const pages = context.pages();
    const page = pages[0];

    const authInfo = await page.evaluate(() => {
      const token = localStorage.getItem('GAMEMAKER_TOKEN');
      const userInfo = JSON.parse(localStorage.getItem('USER_INFO') || '{}');
      return {
        token: token,
        userName: userInfo.name || '江昊（jiang hao）' // 默认用户名
      };
    });

    await browser.close();
    return authInfo;
  } catch (error) {
    throw new Error(`获取认证信息失败: ${error.message}`);
  }
}

async function createGame(gameName, token, userName) {
  log(`创建游戏: ${gameName}`);

  // 创建一个空的配置对象（使用模板默认配置）
  const emptyConfig = {
    common: {
      settlement_component: {},
      additional_settlement_component: {},
      global_config: {},
      levels: {},
      level_settlement: {}
    },
    game: [],
    additional: [],
    components: []
  };

  const response = await fetch('https://sszt-gateway.speiyou.com/beibo/game/config/game', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json;charset=UTF-8',
      'beibotoken': token
    },
    body: JSON.stringify({
      user: userName,
      game_type: 1,
      game_name: gameName,
      template_id: TEMPLATE_ID,
      configuration: emptyConfig
    })
  });

  const result = await response.json();

  if (result.code !== 0) {
    throw new Error(`创建失败: ${result.msg || JSON.stringify(result)}`);
  }

  const gameId = result.result.game_id;
  log(`✅ 游戏创建成功: ${gameId}`);
  return gameId;
}

async function lockGame(gameId, token) {
  log(`锁定游戏: ${gameId}`);

  const response = await fetch('https://sszt-gateway.speiyou.com/beibo/game/config/lock', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json;charset=UTF-8',
      'beibotoken': token
    },
    body: JSON.stringify({
      id: gameId,
      version: "0.0",
      type: "game"
    })
  });

  const result = await response.json();

  if (result.code !== 0) {
    log(`⚠️  锁定失败: ${result.msg}`);
  } else {
    log(`✅ 游戏锁定成功`);
  }
}

async function saveConfig(gameId, configPath) {
  log(`导入配置: ${path.basename(configPath)}`);

  try {
    // 使用save_game_config_via_cdp.js脚本
    const command = `node D:/codexProject/save_game_config_via_cdp.js "${gameId}" "${configPath}"`;
    const output = execSync(command, { encoding: 'utf-8', timeout: 60000 });

    log(`✅ 配置保存成功`);
    return true;
  } catch (error) {
    log(`❌ 配置保存失败: ${error.message}`);
    return false;
  }
}

async function processGame(levelNum, token, userName) {
  const gameName = `${GAME_NAME_PREFIX}${levelNum}`;
  const configFile = path.join(CONFIG_DIR, `新一_第${String(levelNum).padStart(2, '0')}关_单关游戏.json`);

  log(`\n${'='.repeat(60)}`);
  log(`开始处理第 ${levelNum} 关`);
  log(`游戏名称: ${gameName}`);
  log(`配置文件: ${path.basename(configFile)}`);
  log(`${'='.repeat(60)}`);

  const result = {
    level: levelNum,
    gameName: gameName,
    configFile: path.basename(configFile),
    gameId: null,
    editorUrl: null,
    success: false,
    error: null
  };

  try {
    // 检查配置文件是否存在
    if (!fs.existsSync(configFile)) {
      throw new Error(`配置文件不存在: ${configFile}`);
    }

    // 步骤1: 创建游戏
    const gameId = await createGame(gameName, token, userName);
    result.gameId = gameId;
    result.editorUrl = `https://coursewaremaker.speiyou.com/#/editor?game_id=${gameId}`;

    // 等待游戏创建完成
    await sleep(2000);

    // 步骤2: 锁定游戏
    await lockGame(gameId, token);
    await sleep(1000);

    // 步骤3: 导入配置
    const saveSuccess = await saveConfig(gameId, configFile);

    if (!saveSuccess) {
      throw new Error('配置保存失败');
    }

    // 等待配置保存完成
    await sleep(2000);

    result.success = true;
    log(`\n✅ 第 ${levelNum} 关处理完成！`);
    log(`   游戏ID: ${gameId}`);
    log(`   编辑器: ${result.editorUrl}`);

  } catch (error) {
    result.error = error.message;
    log(`\n❌ 第 ${levelNum} 关处理失败: ${error.message}`);
  }

  results.push(result);
  return result;
}

async function main() {
  log('========================================');
  log('开始批量创建新一年级游戏');
  log('========================================');

  try {
    // 获取认证信息
    log('获取认证信息...');
    const authInfo = await getAuthInfo();
    log(`✅ 认证信息获取成功`);
    log(`   用户: ${authInfo.userName}`);

    // 处理12个游戏
    for (let level = 1; level <= 12; level++) {
      await processGame(level, authInfo.token, authInfo.userName);

      // 每个游戏之间间隔3秒
      if (level < 12) {
        log(`\n等待3秒后处理下一个游戏...\n`);
        await sleep(3000);
      }
    }

    // 保存结果
    const resultFile = `D:/codexProject/xinyi_game_creation_results_${Date.now()}.json`;
    fs.writeFileSync(resultFile, JSON.stringify(results, null, 2));

    // 打印汇总
    log('\n========================================');
    log('批量创建完成！汇总结果：');
    log('========================================');

    const successCount = results.filter(r => r.success).length;
    const failCount = results.filter(r => !r.success).length;

    log(`✅ 成功: ${successCount} 个`);
    log(`❌ 失败: ${failCount} 个`);
    log(`📁 详细结果: ${resultFile}`);

    log('\n游戏清单：');
    results.forEach(r => {
      const status = r.success ? '✅' : '❌';
      log(`${status} ${r.gameName}: ${r.gameId || '未创建'}`);
      if (r.editorUrl) {
        log(`   ${r.editorUrl}`);
      }
    });

    // 生成游戏ID列表文件
    const gameIdList = results.filter(r => r.success).map(r => ({
      level: r.level,
      gameName: r.gameName,
      gameId: r.gameId,
      editorUrl: r.editorUrl
    }));

    const gameIdListFile = 'D:/codexProject/xinyi_game_id_list.json';
    fs.writeFileSync(gameIdListFile, JSON.stringify(gameIdList, null, 2));
    log(`\n📋 游戏ID列表已保存: ${gameIdListFile}`);

  } catch (error) {
    log(`❌ 批量处理失败: ${error.message}`);
    console.error(error);
    process.exit(1);
  }
}

main();
