const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

async function main() {
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  const context = browser.contexts()[0];
  const page = context.pages().find((p) => (p.url() || "").includes("coursewaremaker"));
  if (!page) throw new Error("No CoursewareMaker page");

  const keywords = [
    { kw: "26春国际小班7赛跑", file: "j7" },
    { kw: "26暑国际小班8游泳", file: "j8" },
    { kw: "26暑国际小班9赛车", file: "j9" },
  ];

  for (const { kw, file } of keywords) {
    const rawText = await page.evaluate(async (name) => {
      const token = localStorage.getItem("GAMEMAKER_TOKEN") || "";
      const payload = { page: 1, page_size: 200, name: name };
      const res = await fetch("https://sszt-gateway.speiyou.com/beibo/game/config/resources", {
        method: "POST",
        headers: { "Content-Type": "application/json;charset=UTF-8", beibotoken: token },
        body: JSON.stringify(payload),
      });
      return res.text();
    }, kw);

    const outFile = path.join(__dirname, `../output/${file}_resources.json`);
    fs.writeFileSync(outFile, rawText);
    
    try {
      const data = JSON.parse(rawText);
      const list = data?.result?.list || [];
      console.log(`${kw}: ${list.length} resources`);
      if (list.length > 0) {
        console.log(`  Sample:`, JSON.stringify(list[0]).slice(0, 300));
      }
    } catch(e) {
      console.log(`${kw}: raw=${rawText.slice(0,200)}`);
    }
  }

  await browser.close();
}
main().catch((e) => { console.error(e); process.exit(1); });
