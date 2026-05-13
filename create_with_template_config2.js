/**
 * 在浏览器上下文里执行所有 fetch，避免 Node.js CORS/格式问题
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

    const result = await page.evaluate(async function(params) {
        const token = localStorage.getItem("GAMEMAKER_TOKEN") || "";
        let userName = "用户";
        try { userName = JSON.parse(localStorage.getItem("USER_INFO") || "{}").userName || "用户"; } catch {}

        // 获取模板配置
        const tmplRes = await fetch(`${params.apiBase}/game/${params.templateId}`, {
            headers: { "beibotoken": token }
        });
        const tmpl = await tmplRes.json();
        if (tmpl.code !== 0) return { ok: false, step: "get_template", data: tmpl };

        const templateConfig = tmpl.result.configuration;

        // 创建游戏（用模板原始 configuration）
        const createRes = await fetch(`${params.apiBase}/game`, {
            method: "POST",
            headers: {
                "beibotoken": token,
                "Content-Type": "application/json;charset=UTF-8"
            },
            body: JSON.stringify({
                user: userName,
                game_type: 1,
                game_name: params.gameName,
                template_id: params.templateId,
                configuration: templateConfig
            })
        });
        const created = await createRes.json();
        if (created.code !== 0) return { ok: false, step: "create", data: created };

        return { ok: true, game_id: created.result.game_id, user: userName };
    }, { apiBase: API_BASE, templateId: YUNDONG_TEMPLATE_ID, gameName: GAME_NAME });

    if (result.ok) {
        console.error("✅ 游戏创建成功:", result.game_id, "用户:", result.user);
        console.log(result.game_id);
    } else {
        console.error("❌ 失败步骤:", result.step);
        console.error("返回:", JSON.stringify(result.data).slice(0, 300));
        process.exit(1);
    }

    await browser.close();
}
main().catch(e => { console.error("ERROR:", e.message); process.exit(1); });
