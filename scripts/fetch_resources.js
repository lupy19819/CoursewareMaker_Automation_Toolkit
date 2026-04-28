const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

async function main() {
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  const context = browser.contexts()[0];
  const page = context.pages().find((p) => (p.url() || "").includes("coursewaremaker"));
  if (!page) throw new Error("No CoursewareMaker page");

  const keywords = ["26春国际小班7赛跑", "26暑国际小班8游泳", "26暑国际小班9赛车"];

  for (const kw of keywords) {
    const rawText = await page.evaluate(async (keyword) => {
      const token = localStorage.getItem("GAMEMAKER_TOKEN") || "";
      const res = await fetch(
        "https://sszt-gateway.speiyou.com/beibo/game/config/resources?page=1&page_size=200&keyword=" + encodeURIComponent(keyword),
        { headers: { beibotoken: token } }
      );
      return res.text();
    }, kw);

    const safeName = kw.replace(/\s/g, "_").replace(/[^\w\u4e00-\u9fa5]/g, "_");
    const outFile = path.join(__dirname, "../output/resources_" + safeName + ".json");
    fs.writeFileSync(outFile, rawText);
    console.log(`${kw}: saved (${rawText.length} chars)`);
    console.log(`  First 400:`, rawText.slice(0, 400));
  }

  await browser.close();
}
main().catch((e) => { console.error(e); process.exit(1); });
