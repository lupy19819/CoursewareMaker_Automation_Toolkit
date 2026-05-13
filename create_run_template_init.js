/**
 * 用模板正确创建运动PK游戏：创建时不传 configuration，让服务端初始化
 */
const { chromium } = require("playwright");
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

    console.error("用户:", userName, "Token OK:", !!token);

    // 方案A：创建时不传 configuration（让服务端用模板初始化）
    const resp = await fetch(`${API_BASE}/game`, {
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
            template_id: YUNDONG_TEMPLATE_ID
            // ← 故意不传 configuration
        })
    });

    const result = await resp.json();
    console.error("创建结果code:", result.code, "msg:", result.msg);

    if (result.code === 0 && result.result?.game_id) {
        const gameId = result.result.game_id;
        console.error("✅ 游戏创建成功:", gameId);

        // 验证：获取刚创建的游戏配置
        const getResp = await fetch(`${API_BASE}/game/${gameId}`, {
            headers: { "beibotoken": token }
        });
        const getResult = await getResp.json();
        const cfg = getResult.result?.configuration;
        if (cfg) {
            const parsed = JSON.parse(cfg);
            const levels = parsed.custom_game?.length || 0;
            console.error(`✅ 初始配置：${levels} 关卡（模板初始化）`);
        } else {
            console.error("⚠️  无 configuration，服务端未初始化");
        }

        console.log(gameId);
    } else {
        console.error("❌ 创建失败:", JSON.stringify(result));
        process.exit(1);
    }

    await browser.close();
}
main().catch(e => { console.error("ERROR:", e.message); process.exit(1); });
