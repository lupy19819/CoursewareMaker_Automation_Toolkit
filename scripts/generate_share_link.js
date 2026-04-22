/**
 * 为单个游戏生成分享链接
 * Usage: node generate_share_link.js <game_id>
 */

const puppeteer = require('puppeteer-core');
const fs = require('fs');

const CHROME_DEBUG_PORT = 9222;
const API_BASE = 'https://sszt-gateway.speiyou.com/beibo/game/config';
const BASE_PREVIEW_URL = 'https://coursewaremaker.speiyou.com/#/share-preview';

// 从命令行获取game_id
const gameId = process.argv[2];

if (!gameId) {
  console.error('❌ 错误: 请提供游戏ID');
  console.log('用法: node generate_share_link.js <game_id>');
  process.exit(1);
}

// 获取Token
async function getToken(page) {
  return await page.evaluate(() => {
    return localStorage.getItem('GAMEMAKER_TOKEN');
  });
}

// 生成分享链接
async function generateShareLink(token, gameId) {
  console.log(`\n🔗 正在为游戏生成分享链接: ${gameId}`);

  const headers = {
    'beibotoken': token,
    'content-type': 'application/json;charset=UTF-8'
  };

  try {
    // 创建分享链接
    const response = await fetch(`${API_BASE}/createPreviewUrl`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        game_id: gameId,
        base_preview_url: BASE_PREVIEW_URL
      })
    });

    const data = await response.json();

    if (data.code !== 0) {
      throw new Error(`API返回错误: ${data.msg}`);
    }

    const result = data.result;
    console.log(`\n✅ 分享链接生成成功！\n`);
    console.log(`📋 分享链接: ${result.preview_url}`);
    console.log(`🔑 加密参数: ${result.pw}`);
    console.log(`📅 创建时间: ${result.create_time}`);
    console.log(`⏰ 有效期至: ${result.valid_date} (${result.valid_time}天)`);

    return {
      success: true,
      gameId,
      shareLink: result.preview_url,
      pw: result.pw,
      createTime: result.create_time,
      validDate: result.valid_date,
      validTime: result.valid_time
    };

  } catch (error) {
    console.error(`❌ 生成失败: ${error.message}`);
    return {
      success: false,
      gameId,
      error: error.message
    };
  }
}

// 主函数
async function main() {
  console.log('🚀 开始生成分享链接...\n');

  // 连接到已运行的Chrome
  const browser = await puppeteer.connect({
    browserURL: `http://localhost:${CHROME_DEBUG_PORT}`,
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

  // 生成分享链接
  const result = await generateShareLink(token, gameId);

  // 保存结果
  const timestamp = Date.now();
  const resultFile = `D:/codexProject/share_link_${gameId.substring(0, 8)}_${timestamp}.json`;
  fs.writeFileSync(resultFile, JSON.stringify(result, null, 2));
  console.log(`\n📁 结果已保存: ${resultFile}`);

  await browser.disconnect();
}

main().catch(console.error);
