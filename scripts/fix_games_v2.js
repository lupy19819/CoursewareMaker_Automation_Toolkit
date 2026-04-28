/**
 * Fix J7/J8/J9 YundongPK game configs
 * Reads configs from saved files, uses fetched resources to fix custom_game levels
 */
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const OUTPUT = path.join(__dirname, "../output");

// ============ 题目数据 ============
const GAMES = [
  {
    game_id: "32992acd-3fbe-11f1-906b-da4a8224db76",
    name: "J7赛跑",
    configFile: "j7_current.json",
    resourceFile: "j7_resources.json",
    questions: [
      { audio: "daddy", opts: ["mummy","daddy","baby"], correct: 2 },
      { audio: "mummy", opts: ["mummy","daddy","baby"], correct: 1 },
      { audio: "baby",  opts: ["baby","daddy","mummy"], correct: 1 },
      { audio: "mummy", opts: ["daddy","mummy","baby"], correct: 2 },
      { audio: "daddy", opts: ["baby","mummy","daddy"], correct: 3 },
      { audio: "baby",  opts: ["daddy","mummy","baby"], correct: 3 },
      { audio: "mummy", opts: ["baby","mummy","daddy"], correct: 2 },
      { audio: "baby",  opts: ["mummy","daddy","baby"], correct: 3 },
      { audio: "daddy", opts: ["mummy","baby","daddy"], correct: 3 },
      { audio: "baby",  opts: ["daddy","mummy","baby"], correct: 3 },
    ],
  },
  {
    game_id: "33e6a1b0-3fbe-11f1-906b-da4a8224db76",
    name: "J8游泳",
    configFile: "j8_current.json",
    resourceFile: "j8_resources.json",
    questions: [
      { audio: "sister",  opts: ["brother","sister","pet"],   correct: 2 },
      { audio: "brother", opts: ["brother","sister","pet"],   correct: 1 },
      { audio: "pet",     opts: ["pet","brother","sister"],   correct: 1 },
      { audio: "brother", opts: ["sister","pet","brother"],   correct: 3 },
      { audio: "sister",  opts: ["brother","sister","pet"],   correct: 2 },
      { audio: "pet",     opts: ["sister","pet","brother"],   correct: 2 },
      { audio: "sister",  opts: ["sister","brother","pet"],   correct: 1 },
      { audio: "brother", opts: ["pet","brother","sister"],   correct: 2 },
      { audio: "pet",     opts: ["sister","pet","brother"],   correct: 2 },
      { audio: "sister",  opts: ["sister","brother","pet"],   correct: 1 },
    ],
  },
  {
    game_id: "c5e2b08a-3fc3-11f1-906b-da4a8224db76",
    name: "J9赛车",
    configFile: "j9_current.json",
    resourceFile: "j9_resources.json",
    questions: [
      { audio: "grandma", opts: ["grandma","grandpa","family"], correct: 1 },
      { audio: "grandpa", opts: ["family","grandpa","grandma"], correct: 2 },
      { audio: "family",  opts: ["grandma","grandpa","family"], correct: 3 },
      { audio: "family",  opts: ["grandma","family","grandpa"], correct: 2 },
      { audio: "grandma", opts: ["grandpa","family","grandma"], correct: 3 },
      { audio: "grandpa", opts: ["family","grandma","grandpa"], correct: 3 },
      { audio: "grandma", opts: ["grandma","grandpa","family"], correct: 1 },
      { audio: "family",  opts: ["grandpa","family","grandma"], correct: 2 },
      { audio: "grandpa", opts: ["grandma","family","grandpa"], correct: 3 },
      { audio: "grandma", opts: ["grandma","grandpa","family"], correct: 1 },
    ],
  },
];

function buildResourceMap(resourceList) {
  // Build maps: word -> audio URL, word -> image URL
  const audioMap = {};
  const imageMap = {};
  for (const r of resourceList) {
    const name = r.name || "";
    const url = r.url || "";
    const cat = r.category || "";
    if (cat === "audio") {
      // Extract word from name (last word after last space or after 音频)
      const m = name.match(/音频(?:单词)?(.+)$/);
      const word = m ? m[1].trim() : null;
      if (word && !audioMap[word]) audioMap[word] = url; // first occurrence
    } else if (cat === "image") {
      // Extract word: last part after prefix
      const m = name.match(/(?:赛跑|游泳|赛车)(.+)$/);
      const word = m ? m[1].trim() : null;
      if (word && !imageMap[word]) imageMap[word] = url;
    }
  }
  return { audioMap, imageMap };
}

async function main() {
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  const context = browser.contexts()[0];
  const page = context.pages().find((p) => (p.url() || "").includes("coursewaremaker"));
  if (!page) throw new Error("No CoursewareMaker page");

  // First fetch J8 and J9 configs (J7 already exists)
  for (const game of GAMES.slice(1)) {
    if (!fs.existsSync(path.join(OUTPUT, game.configFile))) {
      console.log(`Fetching config for ${game.name}...`);
      const rawText = await page.evaluate(async (gameId) => {
        const token = localStorage.getItem("GAMEMAKER_TOKEN") || "";
        const res = await fetch(`https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=${gameId}`, {
          headers: { beibotoken: token },
        });
        return res.text();
      }, game.game_id);
      fs.writeFileSync(path.join(OUTPUT, game.configFile), rawText);
    }
  }

  const results = [];

  for (const game of GAMES) {
    console.log(`\n========== ${game.name} ==========`);

    // Load config from file
    const currentData = JSON.parse(fs.readFileSync(path.join(OUTPUT, game.configFile), "utf8"));
    const rawConfig = currentData?.result?.configuration;
    if (!rawConfig) {
      console.error(`✗ No configuration`);
      results.push({ name: game.name, success: false, error: "No configuration" });
      continue;
    }
    const config = typeof rawConfig === "string" ? JSON.parse(rawConfig) : rawConfig;
    const customGame = config.custom_game || [];
    console.log(`  custom_game levels: ${customGame.length}`);

    // Load resources from file
    const resData = JSON.parse(fs.readFileSync(path.join(OUTPUT, game.resourceFile), "utf8"));
    const resList = resData?.result?.list || [];
    const { audioMap, imageMap } = buildResourceMap(resList);
    console.log(`  audioMap words: ${Object.keys(audioMap).join(", ")}`);
    console.log(`  imageMap words: ${Object.keys(imageMap).join(", ")}`);

    const missing = [];
    const fixLog = [];

    for (let i = 0; i < game.questions.length; i++) {
      const q = game.questions[i];
      const level = customGame[i];
      if (!level) { missing.push(`Level ${i+1} missing`); continue; }

      const topic = level.topics && level.topics[0];
      if (!topic) { missing.push(`Level ${i+1} topics[0] missing`); continue; }

      const tr = topic.title_res;
      if (!tr) { missing.push(`Level ${i+1} title_res missing`); continue; }

      // Audio
      const audioUrl = audioMap[q.audio];
      if (!audioUrl) missing.push(`音频: ${q.audio} (题${i+1})`);
      else {
        if (tr.btnAudio !== undefined) tr.btnAudio = audioUrl;
        if (tr.titleAuido !== undefined) tr.titleAuido = audioUrl;
      }

      // Options
      const options = tr.options || [];
      for (let j = 0; j < q.opts.length; j++) {
        const word = q.opts[j];
        const isCorrect = (j + 1) === q.correct;
        const opt = options[j];
        if (!opt || !opt.item) { missing.push(`Level ${i+1} option ${j+1} missing`); continue; }

        const imgUrl = imageMap[word];
        if (!imgUrl) missing.push(`图片: ${word} (题${i+1} 选${j+1})`);
        else opt.item.icon = imgUrl;

        opt.item.switch = isCorrect;
      }

      fixLog.push(`题${i+1}: 音频=${q.audio}${audioUrl?"✓":"✗"} | 选项=[${q.opts.join(",")}] | 正确=${q.correct}`);
    }

    for (const log of fixLog) console.log(" ", log);
    if (missing.length) {
      console.warn(`  ⚠ 缺失(${missing.length}):`, missing.join("; "));
    }

    // Save fixed config to file for reference
    const fixedPath = path.join(OUTPUT, game.configFile.replace("_current", "_fixed"));
    fs.writeFileSync(fixedPath, JSON.stringify(config, null, 2));

    // Save to server via PUT
    console.log(`  Saving to server...`);
    const configStr = JSON.stringify(config);
    const saveResult = await page.evaluate(async ({ gameId, configStr }) => {
      const token = localStorage.getItem("GAMEMAKER_TOKEN") || "";
      const getRes = await fetch(`https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=${gameId}`, {
        headers: { beibotoken: token },
      });
      const detailText = await getRes.text();
      let detail;
      try { detail = JSON.parse(detailText); } catch(e) { return { error: "parse detail: " + detailText.slice(0,100) }; }
      if (!detail || detail.code !== 0 || !detail.result) {
        return { error: "get detail failed: " + JSON.stringify(detail).slice(0,200) };
      }
      let parsedConfig;
      try { parsedConfig = JSON.parse(configStr); } catch(e) { return { error: "parse config: " + e.message }; }
      const payload = { ...detail.result, configuration: parsedConfig };
      const putRes = await fetch("https://sszt-gateway.speiyou.com/beibo/game/config/game", {
        method: "PUT",
        headers: { "Content-Type": "application/json;charset=UTF-8", beibotoken: token },
        body: JSON.stringify(payload),
      });
      const putText = await putRes.text();
      return { rawResponse: putText };
    }, { gameId: game.game_id, configStr });

    console.log(`  Server response: ${JSON.stringify(saveResult)}`);

    let success = false;
    if (saveResult?.rawResponse) {
      try {
        const r = JSON.parse(saveResult.rawResponse);
        success = r.code === 0 || r.success === true;
        console.log(`  Parsed: code=${r.code}, msg=${r.msg || r.message || ""}`);
      } catch(e) {
        console.log(`  Raw: ${saveResult.rawResponse.slice(0,200)}`);
      }
    }

    results.push({ name: game.name, game_id: game.game_id, success, missing, fixedPath });
  }

  // Summary
  console.log("\n========== 修复摘要 ==========");
  for (const r of results) {
    console.log(`${r.success ? "✅" : "❌"} ${r.name} (${r.game_id})`);
    if (r.missing && r.missing.length) {
      console.log(`  ⚠ 缺失: ${r.missing.join("; ")}`);
    } else if (r.missing) {
      console.log(`  ✓ 所有资源均找到`);
    }
  }

  fs.writeFileSync(path.join(OUTPUT, "fix_summary.json"), JSON.stringify(results, null, 2));
  await browser.close();
}

main().catch((e) => { console.error(e); process.exit(1); });
