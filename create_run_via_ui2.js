/**
 * 通过精品游戏模板创建运动PK赛跑游戏
 */
const { chromium } = require("playwright");
const GAME_NAME = process.argv[2] || "国际新小班暑J10跑酷赛跑";
const YUNDONG_TEMPLATE_ID = "47995925-fb37-11ef-8c1b-ce918f8037e8";

async function main() {
    const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
    const ctx = browser.contexts()[0];
    let page = ctx.pages().find(p => (p.url()||"").includes("coursewaremaker.speiyou.com"));
    if (!page) {
        page = await ctx.newPage();
        await page.goto("https://coursewaremaker.speiyou.com");
        await page.waitForLoadState("networkidle");
    }

    // 拦截游戏创建响应
    let createdGameId = null;
    page.on("response", async (resp) => {
        const url = resp.url();
        const method = resp.request().method();
        if (url.includes("/beibo/game/config") && method === "POST") {
            try {
                const body = await resp.json();
                if (body?.result?.game_id) {
                    createdGameId = body.result.game_id;
                    console.error("🎮 新游戏ID:", createdGameId);
                }
            } catch {}
        }
    });

    // 去精品游戏模板页
    await page.goto("https://coursewaremaker.speiyou.com/#/list/game/template");
    await page.waitForTimeout(3000);
    await page.screenshot({ path: "/tmp/boutique_list.png" });
    console.error("精品模板页截图已保存");

    // 搜索运动PK
    const searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="查询"], .search-input input').first();
    if (await searchInput.isVisible().catch(() => false)) {
        await searchInput.fill("运动PK");
        await page.keyboard.press("Enter");
        await page.waitForTimeout(2000);
        console.error("已搜索运动PK");
    }
    await page.screenshot({ path: "/tmp/search_result.png" });

    // 找到对应模板卡片并hover → 点"使用"
    // 先看所有游戏卡片
    const cards = await page.locator('.game-card, [class*="card"], [class*="item"]').all();
    console.error("找到卡片数:", cards.length);
    for (const c of cards.slice(0, 15)) {
        const txt = await c.textContent().catch(() => "");
        if (txt.includes("运动") || txt.includes("赛跑") || txt.includes("PK")) {
            console.error("  找到相关卡片:", txt.slice(0, 60).replace(/\s+/g, " "));
        }
    }

    // 用 API 直接通过模板ID创建游戏（从 localStorage 拿 token）
    const token = await page.evaluate(function() {
        return localStorage.getItem("GAMEMAKER_TOKEN") || "";
    });
    console.error("Token 前20字符:", token.slice(0, 20));

    // 创建游戏请求
    const result = await page.evaluate(async function(params) {
        const res = await fetch("https://sszt-gateway.speiyou.com/beibo/game/config", {
            method: "POST",
            headers: {
                "beibotoken": params.token,
                "Content-Type": "application/json;charset=UTF-8"
            },
            body: JSON.stringify({
                game_name: params.name,
                template_id: params.templateId,
                grade: 7,
                subject_id: 1,
                year: 2026,
                term_id: 2,
                cnum_id: 31,
                is_diagnose: 1
            })
        });
        return res.json();
    }, { token, name: GAME_NAME, templateId: YUNDONG_TEMPLATE_ID });

    console.error("创建结果:", JSON.stringify(result).slice(0, 200));

    if (result?.result?.game_id) {
        createdGameId = result.result.game_id;
    }

    if (createdGameId) {
        console.log(createdGameId);
    } else {
        console.error("失败，返回:", JSON.stringify(result));
        process.exit(1);
    }

    await browser.close();
}
main().catch(e => { console.error("ERROR:", e.message); process.exit(1); });
