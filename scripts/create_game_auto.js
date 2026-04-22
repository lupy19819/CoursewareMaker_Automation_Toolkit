/**
 * 自动创建 CoursewareMaker 游戏
 * 用法: node create_game_auto.js <游戏名称> <模板ID> <配置文件路径>
 */

const puppeteer = require('puppeteer-core');
const fs = require('fs');

// 配置
const CHROME_DEBUG_PORT = 9222;
const API_BASE = 'https://sszt-gateway.speiyou.com/beibo/game/config';
const EDITOR_BASE = 'https://coursewaremaker.speiyou.com/#/editor';

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
        throw new Error('未找到GAMEMAKER_TOKEN，请先登录 CoursewareMaker');
    }

    console.log('✅ 已获取Token');
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
        return '用户'; // 默认值
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
 * 创建游戏
 */
async function createGame(gameName, templateId, configuration, token, userName) {
    console.log(`\n📝 创建游戏: ${gameName}`);
    console.log(`📋 模板ID: ${templateId}`);
    console.log(`👤 创建者: ${userName}`);

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
            template_id: templateId,
            configuration: configuration
        })
    });

    const result = await response.json();

    if (result.code !== 0) {
        throw new Error(`创建游戏失败: ${result.msg}`);
    }

    const gameId = result.result.game_id;
    console.log(`✅ 游戏创建成功！`);
    console.log(`🎮 游戏ID: ${gameId}`);

    return gameId;
}

/**
 * 锁定游戏
 */
async function lockGame(gameId, token) {
    console.log(`\n🔒 锁定游戏: ${gameId}`);

    const response = await fetch(`${API_BASE}/lock`, {
        method: 'POST',
        headers: {
            'beibotoken': token,
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'https://coursewaremaker.speiyou.com',
            'Referer': 'https://coursewaremaker.speiyou.com/'
        },
        body: JSON.stringify({
            id: gameId,
            version: '0.0',
            type: 'game'
        })
    });

    const result = await response.json();

    if (result.code !== 0) {
        console.warn(`⚠️ 锁定游戏失败: ${result.msg}`);
    } else {
        console.log(`✅ 游戏已锁定`);
    }
}

/**
 * 在浏览器中打开游戏编辑器
 */
async function openGameEditor(gameId) {
    const editorUrl = `${EDITOR_BASE}?game_id=${gameId}`;

    const browser = await puppeteer.connect({
        browserURL: `http://localhost:${CHROME_DEBUG_PORT}`,
        defaultViewport: null
    });

    const page = await browser.newPage();
    await page.goto(editorUrl);

    console.log(`🌐 已在浏览器中打开编辑器`);
    console.log(`🔗 ${editorUrl}`);
}

/**
 * 主函数
 */
async function main() {
    const args = process.argv.slice(2);

    if (args.length < 3) {
        console.error('用法: node create_game_auto.js <游戏名称> <模板ID> <配置文件路径>');
        console.error('示例: node create_game_auto.js "我的游戏" "70a3010b-0b7a-11ef-b3a3-fa7902489df6" "./game_config.json"');
        process.exit(1);
    }

    const [gameName, templateId, configPath] = args;

    // 读取配置文件
    if (!fs.existsSync(configPath)) {
        console.error(`❌ 配置文件不存在: ${configPath}`);
        process.exit(1);
    }

    const configuration = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    console.log(`✅ 已加载配置文件: ${configPath}`);

    try {
        // 1. 获取Token
        const token = await getTokenFromChrome();

        // 2. 获取用户名
        const userName = await getUserName();

        // 3. 创建游戏
        const gameId = await createGame(gameName, templateId, configuration, token, userName);

        // 4. 锁定游戏
        await lockGame(gameId, token);

        // 5. 打开编辑器
        await openGameEditor(gameId);

        // 6. 输出结果
        console.log('\n' + '='.repeat(60));
        console.log('🎉 游戏创建完成！');
        console.log('='.repeat(60));
        console.log(`游戏ID: ${gameId}`);
        console.log(`游戏名称: ${gameName}`);
        console.log(`编辑器链接: ${EDITOR_BASE}?game_id=${gameId}`);
        console.log('='.repeat(60));

        // 将游戏ID写入文件
        fs.writeFileSync('latest_game_id.txt', gameId);
        console.log('\n✅ 游戏ID已保存到 latest_game_id.txt');

    } catch (error) {
        console.error('\n❌ 创建失败:', error.message);
        process.exit(1);
    }
}

main();
