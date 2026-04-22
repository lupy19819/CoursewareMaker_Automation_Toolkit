/**
 * 批量创建并配置 CoursewareMaker 游戏
 */

const puppeteer = require('puppeteer-core');
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const CHROME_DEBUG_PORT = 9222;
const API_BASE = 'https://sszt-gateway.speiyou.com/beibo/game/config';
const TEMPLATE_ID = '70a3010b-0b7a-11ef-b3a3-fa7902489df6'; // 拖拽类模板

/**
 * 从Chrome localStorage获取token
 */
async function getTokenFromChrome() {
    const browser = await puppeteer.connect({
        browserURL: `http://localhost:${CHROME_DEBUG_PORT}`,
        defaultViewport: null
    });

    const pages = await browser.pages();
    let page = pages.find(p => p.url().includes('coursewaremaker.speiyou.com'));

    if (!page) {
        page = await browser.newPage();
        await page.goto('https://coursewaremaker.speiyou.com');
    }

    const token = await page.evaluate(() => {
        return localStorage.getItem('GAMEMAKER_TOKEN');
    });

    if (!token) {
        throw new Error('未找到GAMEMAKER_TOKEN');
    }

    return token;
}

/**
 * 获取用户名
 */
async function getUserName() {
    const browser = await puppeteer.connect({
        browserURL: `http://localhost:${CHROME_DEBUG_PORT}`,
        defaultViewport: null
    });

    const pages = await browser.pages();
    const page = pages.find(p => p.url().includes('coursewaremaker.speiyou.com'));

    if (!page) {
        return '用户';
    }

    const userName = await page.evaluate(() => {
        const userInfo = localStorage.getItem('USER_INFO');
        if (userInfo) {
            try {
                const parsed = JSON.parse(userInfo);
                return parsed.name || '用户';
            } catch (e) {
                return '用户';
            }
        }
        return '用户';
    });

    return userName;
}

/**
 * 创建空游戏
 */
async function createEmptyGame(gameName, token, userName) {
    // 使用一个最小化的配置
    const minimalConfig = {
        "common": {
            "settlement_component": {
                "component_id": "3a3cba67-f961-11ee-b9ef-8e2f78cd4bcd",
                "component_url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assetboundle/OverTips/0.2.0/3X/OverTips.zip",
                "component_data": {}
            },
            "global_config": {
                "font_url": "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/font/FZY4JW.ttf"
            }
        },
        "game": [],
        "additional": [],
        "components": []
    };

    const response = await fetch(`${API_BASE}/game`, {
        method: 'POST',
        headers: {
            'beibotoken': token,
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'https://coursewaremaker.speiyou.com',
            'Referer': 'https://coursewaremaker.speiyou.com/'
        },
        body: JSON.stringify({
            user: userName,
            game_type: 1,
            game_name: gameName,
            template_id: TEMPLATE_ID,
            configuration: minimalConfig
        })
    });

    const result = await response.json();

    if (result.code !== 0) {
        throw new Error(`创建游戏失败: ${result.msg}`);
    }

    return result.result.game_id;
}

/**
 * 使用CDP保存配置
 */
async function saveConfigViaCDP(gameId, configObject) {
    const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
    const context = browser.contexts()[0];
    const page = context.pages().find((p) => (p.url() || "").includes("coursewaremaker.speiyou.com"));

    if (!page) {
        throw new Error("No CoursewareMaker page found");
    }

    const result = await page.evaluate(
        async ({ gameId, configObject }) => {
            const token = localStorage.getItem("GAMEMAKER_TOKEN") || "";
            if (!token) {
                throw new Error("GAMEMAKER_TOKEN missing");
            }

            // 获取当前游戏详情
            const getRes = await fetch(`https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=${gameId}`, {
                headers: { beibotoken: token },
            });
            const detail = await getRes.json();
            if (!detail || detail.code !== 0 || !detail.result) {
                throw new Error(`get detail failed: ${JSON.stringify(detail)}`);
            }

            // 更新配置
            const payload = { ...detail.result, configuration: configObject };
            const putRes = await fetch("https://sszt-gateway.speiyou.com/beibo/game/config/game", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json;charset=UTF-8",
                    beibotoken: token,
                },
                body: JSON.stringify(payload),
            });
            const putJson = await putRes.json();

            // 验证
            const verifyRes = await fetch(`https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=${gameId}`, {
                headers: { beibotoken: token },
            });
            const verify = await verifyRes.json();

            return {
                success: putJson.code === 0,
                save_time: verify?.result?.save_time,
                config_size: verify?.result?.configuration?.length || 0
            };
        },
        { gameId, configObject }
    );

    await browser.close();
    return result;
}

/**
 * 处理单个游戏
 */
async function processGame(index, configPath, token, userName) {
    const gameName = `2026新二思维全能力诊断${index}`;
    const configFileName = path.basename(configPath);

    console.log(`\n${'='.repeat(60)}`);
    console.log(`[${index}/12] 处理: ${configFileName}`);
    console.log(`游戏名称: ${gameName}`);
    console.log('='.repeat(60));

    try {
        // 1. 读取配置文件
        console.log('📖 读取配置文件...');
        const configText = fs.readFileSync(configPath, 'utf8');
        const configObject = JSON.parse(configText);
        console.log(`✅ 配置文件已加载 (${Math.round(configText.length / 1024)}KB)`);

        // 2. 创建空游戏
        console.log('🎮 创建游戏...');
        const gameId = await createEmptyGame(gameName, token, userName);
        console.log(`✅ 游戏已创建: ${gameId}`);

        // 3. 导入配置
        console.log('💾 保存配置...');
        const result = await saveConfigViaCDP(gameId, configObject);

        if (result.success) {
            console.log(`✅ 配置已保存`);
            console.log(`   保存时间: ${result.save_time}`);
            console.log(`   配置大小: ${result.config_size} 字符`);
        } else {
            throw new Error('配置保存失败');
        }

        const editorUrl = `https://coursewaremaker.speiyou.com/#/editor?game_id=${gameId}`;

        return {
            index: index,
            gameName: gameName,
            gameId: gameId,
            configFile: configFileName,
            editorUrl: editorUrl,
            success: true
        };

    } catch (error) {
        console.error(`❌ 失败: ${error.message}`);
        return {
            index: index,
            gameName: gameName,
            configFile: configFileName,
            success: false,
            error: error.message
        };
    }
}

/**
 * 主函数
 */
async function main() {
    console.log('🚀 批量创建游戏开始');
    console.log('='.repeat(60));

    const configDir = 'D:/codexProject/generated_configs/xiner_split_12_games';

    // 获取Token和用户名
    console.log('🔐 获取认证信息...');
    const token = await getTokenFromChrome();
    const userName = await getUserName();
    console.log(`✅ 用户: ${userName}`);

    // 处理游戏 2-12
    const results = [];
    for (let i = 2; i <= 12; i++) {
        const configPath = path.join(configDir, `新二_第${i.toString().padStart(2, '0')}关_单关游戏.json`);

        if (!fs.existsSync(configPath)) {
            console.log(`⚠️ 配置文件不存在: ${configPath}`);
            continue;
        }

        const result = await processGame(i, configPath, token, userName);
        results.push(result);

        // 每个游戏之间稍作停顿，避免API频率限制
        if (i < 12) {
            console.log('\n⏳ 等待2秒...');
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
    }

    // 输出汇总
    console.log('\n' + '='.repeat(60));
    console.log('📊 批量创建完成汇总');
    console.log('='.repeat(60));

    const successful = results.filter(r => r.success);
    const failed = results.filter(r => !r.success);

    console.log(`✅ 成功: ${successful.length}/${results.length}`);
    console.log(`❌ 失败: ${failed.length}/${results.length}`);

    if (successful.length > 0) {
        console.log('\n成功创建的游戏:');
        successful.forEach(r => {
            console.log(`  ${r.index}. ${r.gameName}`);
            console.log(`     ID: ${r.gameId}`);
            console.log(`     链接: ${r.editorUrl}`);
        });
    }

    if (failed.length > 0) {
        console.log('\n失败的游戏:');
        failed.forEach(r => {
            console.log(`  ${r.index}. ${r.gameName} - ${r.error}`);
        });
    }

    // 保存结果到文件
    const outputFile = 'D:/codexProject/batch_create_results.json';
    fs.writeFileSync(outputFile, JSON.stringify(results, null, 2));
    console.log(`\n📄 详细结果已保存到: ${outputFile}`);
}

main().catch(error => {
    console.error('\n❌ 批量处理失败:', error);
    process.exit(1);
});
