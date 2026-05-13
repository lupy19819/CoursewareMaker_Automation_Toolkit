/**
 * 通过 CoursewareMaker 浏览器 UI 创建运动PK赛跑游戏
 * 正确使用模板初始化流程
 */
const { chromium } = require("playwright");

const GAME_NAME = process.argv[2] || "国际新小班暑J10跑酷赛跑";

async function main() {
    const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
    const ctx = browser.contexts()[0];
    let page = ctx.pages().find(p => (p.url()||"").includes("coursewaremaker.speiyou.com"));
    if (!page) {
        page = await ctx.newPage();
        await page.goto("https://coursewaremaker.speiyou.com/#/list/mine/template");
        await page.waitForLoadState("networkidle");
    }

    let createdGameId = null;
    page.on("response", async (resp) => {
        if (resp.url().includes("/beibo/game/config") && resp.request().method() === "POST") {
            try {
                const body = await resp.json();
                if (body?.result?.game_id) {
                    createdGameId = body.result.game_id;
                    console.error("🎮 检测到新游戏ID:", createdGameId);
                }
            } catch {}
        }
    });

    // 导航到模板列表页
    await page.goto("https://coursewaremaker.speiyou.com/#/list/mine/template");
    await page.waitForTimeout(3000);
    await page.screenshot({ path: "/tmp/ui_step1.png" });
    console.error("Step1 截图已保存");

    // 找"新建游戏"按钮 - 尝试多种选择器
    const newBtnSelectors = [
        'button:has-text("新建")',
        '[class*="create"]:has-text("新建")',
        '.el-button:has-text("新建")',
        'button:has-text("创建")',
    ];
    let clicked = false;
    for (const sel of newBtnSelectors) {
        const el = page.locator(sel).first();
        if (await el.isVisible().catch(() => false)) {
            await el.click();
            clicked = true;
            console.error("点击了新建按钮:", sel);
            break;
        }
    }
    if (!clicked) {
        // 截图查看当前状态
        await page.screenshot({ path: "/tmp/ui_no_btn.png" });
        console.error("未找到新建按钮，截图 /tmp/ui_no_btn.png");
        // 列出所有可见按钮
        const allBtns = await page.locator("button").all();
        for (const b of allBtns) {
            const txt = await b.textContent().catch(() => "");
            if (txt.trim()) console.error("  按钮:", txt.trim().slice(0, 40));
        }
        await browser.close();
        process.exit(1);
    }

    await page.waitForTimeout(2000);
    await page.screenshot({ path: "/tmp/ui_step2.png" });
    console.error("Step2（点击新建后）截图已保存");

    // 等待模板选择对话框
    // 寻找"运动PK"或相关选项
    const templates = await page.locator('[class*="template"], [class*="game-type"], .game-item').all();
    console.error("找到模板选项数量:", templates.length);
    for (const t of templates.slice(0, 20)) {
        const txt = await t.textContent().catch(() => "");
        if (txt.trim()) console.error("  模板:", txt.trim().slice(0, 50));
    }

    // 尝试点击"运动PK"或"赛跑"
    const pkSelectors = [
        '[class*="template"]:has-text("运动PK")',
        '[class*="template"]:has-text("赛跑")',
        ':has-text("运动PK")',
        ':has-text("赛跑")',
    ];
    let pkClicked = false;
    for (const sel of pkSelectors) {
        const el = page.locator(sel).first();
        if (await el.isVisible().catch(() => false)) {
            await el.click();
            pkClicked = true;
            console.error("点击了模板:", sel);
            break;
        }
    }
    if (!pkClicked) {
        await page.screenshot({ path: "/tmp/ui_no_template.png" });
        console.error("未找到运动PK模板，截图 /tmp/ui_no_template.png");
    }

    await page.waitForTimeout(2000);
    await page.screenshot({ path: "/tmp/ui_step3.png" });
    console.error("Step3 截图已保存");

    // 如果有名称输入框，填入游戏名称
    const nameInput = page.locator('input[placeholder*="名称"], input[placeholder*="name"], .game-name input').first();
    if (await nameInput.isVisible().catch(() => false)) {
        await nameInput.fill(GAME_NAME);
        console.error("填入游戏名称:", GAME_NAME);
    }

    await page.waitForTimeout(1000);
    await page.screenshot({ path: "/tmp/ui_step4.png" });

    // 确认创建
    const confirmSelectors = [
        'button:has-text("确认")',
        'button:has-text("确定")',
        'button:has-text("创建")',
        '.el-button--primary:has-text("确")',
    ];
    for (const sel of confirmSelectors) {
        const el = page.locator(sel).first();
        if (await el.isVisible().catch(() => false)) {
            await el.click();
            console.error("点击了确认按钮:", sel);
            break;
        }
    }

    // 等待页面跳转或请求完成
    await page.waitForTimeout(5000);
    await page.screenshot({ path: "/tmp/ui_final.png" });
    console.error("Final 截图已保存");
    console.error("当前URL:", page.url());

    if (createdGameId) {
        console.log(createdGameId);
    } else {
        // 尝试从URL提取
        const url = page.url();
        const match = url.match(/game_id=([a-f0-9-]{36})/);
        if (match) {
            console.log(match[1]);
        } else {
            console.error("未获取到game_id");
            process.exit(1);
        }
    }

    await browser.close();
}
main().catch(e => { console.error("ERROR:", e.message); process.exit(1); });
