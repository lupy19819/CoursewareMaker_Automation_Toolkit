const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const GAME_NAME = process.argv[2] || "国际新小班暑J10跑酷赛跑";
const YUNDONG_TEMPLATE_ID = "47995925-fb37-11ef-8c1b-ce918f8037e8";
const API_BASE = "https://sszt-gateway.speiyou.com/beibo/game/config";

async function main() {
    const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
    const ctx = browser.contexts()[0];
    let page = ctx.pages().find(p => (p.url()||"").includes("coursewaremaker.speiyou.com"));
    if (!page) {
        page = await ctx.newPage();
        await page.goto("https://coursewaremaker.speiyou.com");
        await page.waitForLoadState("networkidle");
    }

    const { token, userName } = await page.evaluate(function() {
        const tok = localStorage.getItem("GAMEMAKER_TOKEN") || "";
        let user = "用户";
        try { user = JSON.parse(localStorage.getItem("USER_INFO") || "{}").userName || "用户"; } catch {}
        return { token: tok, userName: user };
    });
    console.error("用户:", userName);

    // Step 1: 获取运动PK模板的配置
    const tmplResp = await fetch(`${API_BASE}/game/${YUNDONG_TEMPLATE_ID}`, {
        headers: { "beibotoken": token, "Origin": "https://coursewaremaker.speiyou.com" }
    });
    const tmplResult = await tmplResp.json();
    console.error("获取模板结果code:", tmplResult.code);

    if (tmplResult.code !== 0) {
        console.error("获取模板失败:", JSON.stringify(tmplResult).slice(0, 200));
        process.exit(1);
    }

    const templateConfig = tmplResult.result.configuration;
    const templateGameName = tmplResult.result.game_name;
    console.error("模板名称:", templateGameName);
    const parsed = JSON.parse(templateConfig);
    console.error("模板关卡数:", parsed.custom_game?.length || 0);

    // Step 2: 用模板配置创建新游戏
    const createResp = await fetch(`${API_BASE}/game`, {
        method: "POST",
        headers: {
            "beibotoken": token,
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://coursewaremaker.speiyou.com",
            "Referer": "https://coursewaremaker.speiyou.com/"
        },
        body: JSON.stringify({
            user: userName,
            game_type: 1,
            game_name: GAME_NAME,
            template_id: YUNDONG_TEMPLATE_ID,
            configuration: templateConfig   // 用模板原始配置初始化
        })
    });
    const createResult = await createResp.json();
    console.error("创建结果code:", createResult.code, "msg:", createResult.msg);

    if (createResult.code !== 0) {
        console.error("创建失败:", JSON.stringify(createResult));
        process.exit(1);
    }

    const gameId = createResult.result.game_id;
    console.error("✅ 游戏创建成功:", gameId);
    console.log(gameId);

    await browser.close();
}
main().catch(e => { console.error("ERROR:", e.message); process.exit(1); });
