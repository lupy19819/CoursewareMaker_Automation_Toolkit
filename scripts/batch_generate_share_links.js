/**
 * 批量为游戏生成分享链接
 * Usage: node batch_generate_share_links.js <game_id_list.json>
 */

const puppeteer = require('puppeteer-core');
const fs = require('fs');

const CHROME_DEBUG_PORT = 9222;
const API_BASE = 'https://sszt-gateway.speiyou.com/beibo/game/config';
const BASE_PREVIEW_URL = 'https://coursewaremaker.speiyou.com/#/share-preview';

// 从命令行获取游戏ID列表文件
const gameListFile = process.argv[2];

if (!gameListFile) {
  console.error('❌ 错误: 请提供游戏ID列表文件');
  console.log('用法: node batch_generate_share_links.js <game_id_list.json>');
  process.exit(1);
}

// 读取游戏ID列表
let gameList;
try {
  gameList = JSON.parse(fs.readFileSync(gameListFile, 'utf-8'));
} catch (error) {
  console.error(`❌ 读取文件失败: ${error.message}`);
  process.exit(1);
}

// 获取Token
async function getToken(page) {
  return await page.evaluate(() => {
    return localStorage.getItem('GAMEMAKER_TOKEN');
  });
}

// 生成分享链接
async function generateShareLink(token, gameId, gameName) {
  console.log(`\n🔗 正在生成分享链接: ${gameName} (${gameId})`);

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
    console.log(`  ✅ 分享链接: ${result.preview_url}`);
    console.log(`  📅 有效期至: ${result.valid_date}`);

    return {
      success: true,
      gameId,
      gameName,
      shareLink: result.preview_url,
      pw: result.pw,
      createTime: result.create_time,
      validDate: result.valid_date,
      validTime: result.valid_time
    };

  } catch (error) {
    console.error(`  ❌ 生成失败: ${error.message}`);
    return {
      success: false,
      gameId,
      gameName,
      error: error.message
    };
  }
}

// 主函数
async function main() {
  console.log('🚀 开始批量生成分享链接...\n');
  console.log(`📂 游戏列表: ${gameListFile}`);
  console.log(`🎮 游戏数量: ${gameList.length}\n`);

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
  console.log('✅ Token获取成功\n');

  const results = [];
  let successCount = 0;
  let failCount = 0;

  // 批量生成分享链接
  for (const game of gameList) {
    const result = await generateShareLink(token, game.gameId, game.gameName);
    results.push(result);

    if (result.success) {
      successCount++;
    } else {
      failCount++;
    }

    // 延迟500ms避免请求过快
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  // 保存结果
  const timestamp = Date.now();
  const resultFile = `D:/codexProject/share_links_batch_${timestamp}.json`;
  fs.writeFileSync(resultFile, JSON.stringify(results, null, 2));

  // 生成Markdown报告
  const mdReport = generateMarkdownReport(results, gameListFile);
  const mdFile = `D:/codexProject/share_links_report_${timestamp}.md`;
  fs.writeFileSync(mdFile, mdReport);

  // 打印总结
  console.log('\n' + '='.repeat(60));
  console.log('📊 批量生成完成！');
  console.log('='.repeat(60));
  console.log(`✅ 成功: ${successCount}/${gameList.length}`);
  console.log(`❌ 失败: ${failCount}/${gameList.length}`);
  console.log(`📁 JSON结果: ${resultFile}`);
  console.log(`📄 Markdown报告: ${mdFile}`);
  console.log('='.repeat(60));

  await browser.disconnect();
}

// 生成Markdown报告
function generateMarkdownReport(results, sourceFile) {
  const successResults = results.filter(r => r.success);
  const failResults = results.filter(r => !r.success);

  let md = `# 游戏分享链接生成报告\n\n`;
  md += `**生成时间**: ${new Date().toLocaleString('zh-CN')}\n`;
  md += `**来源文件**: ${sourceFile}\n`;
  md += `**总数**: ${results.length} | **成功**: ${successResults.length} | **失败**: ${failResults.length}\n\n`;
  md += `---\n\n`;

  if (successResults.length > 0) {
    md += `## ✅ 成功生成的分享链接 (${successResults.length})\n\n`;
    md += `| 序号 | 游戏名称 | 分享链接 | 有效期至 |\n`;
    md += `|------|----------|----------|----------|\n`;

    successResults.forEach((r, index) => {
      md += `| ${index + 1} | ${r.gameName} | [点击访问](${r.shareLink}) | ${r.validDate} |\n`;
    });

    md += `\n---\n\n`;

    md += `## 📋 完整链接列表\n\n`;
    successResults.forEach((r, index) => {
      md += `### ${index + 1}. ${r.gameName}\n`;
      md += `- **游戏ID**: \`${r.gameId}\`\n`;
      md += `- **分享链接**: ${r.shareLink}\n`;
      md += `- **创建时间**: ${r.createTime}\n`;
      md += `- **有效期至**: ${r.validDate} (${r.validTime}天)\n\n`;
    });
  }

  if (failResults.length > 0) {
    md += `\n---\n\n`;
    md += `## ❌ 生成失败 (${failResults.length})\n\n`;
    md += `| 序号 | 游戏名称 | 游戏ID | 错误信息 |\n`;
    md += `|------|----------|--------|----------|\n`;

    failResults.forEach((r, index) => {
      md += `| ${index + 1} | ${r.gameName} | ${r.gameId} | ${r.error} |\n`;
    });
  }

  return md;
}

main().catch(console.error);
