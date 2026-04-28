/**
 * 修复 J7赛跑、J8游泳、J9赛车 的运动PK配置
 * 只改 custom_game[] 的题目数据，不发布
 */
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const OUTPUT_DIR = path.join(__dirname, "../output");
if (!fs.existsSync(OUTPUT_DIR)) fs.mkdirSync(OUTPUT_DIR, { recursive: true });

// ============ 题目数据 ============
const GAMES = [
  {
    game_id: "32992acd-3fbe-11f1-906b-da4a8224db76",
    name: "J7赛跑",
    type: "race", // 赛跑
    prefix: "26春国际小班7赛跑",
    outputFile: "j7_current.json",
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
    type: "swim", // 游泳
    prefix: "26暑国际小班8游泳",
    outputFile: "j8_current.json",
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
    type: "car", // 赛车
    prefix: "26暑国际小班9赛车",
    outputFile: "j9_current.json",
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

// ============ 主逻辑 ============
async function main() {
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  const context = browser.contexts()[0];
  const page = context.pages().find((p) => (p.url() || "").includes("coursewaremaker.speiyou.com"));
  if (!page) throw new Error("No CoursewareMaker page found");

  const results = [];

  for (const game of GAMES) {
    console.log(`\n========== 处理 ${game.name} (${game.game_id}) ==========`);

    // Step 1: 获取当前配置
    const currentConfig = await page.evaluate(async ({ gameId }) => {
      const token = localStorage.getItem("GAMEMAKER_TOKEN") || "";
      const res = await fetch(`https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=${gameId}`, {
        headers: { beibotoken: token },
      });
      return res.json();
    }, { gameId: game.game_id });

    fs.writeFileSync(
      path.join(OUTPUT_DIR, game.outputFile),
      JSON.stringify(currentConfig, null, 2)
    );
    console.log(`✓ 已保存当前配置到 output/${game.outputFile}`);

    if (!currentConfig?.result?.configuration) {
      console.error(`✗ 无法获取配置`);
      results.push({ name: game.name, success: false, error: "无法获取配置" });
      continue;
    }

    // Step 2: 拉取资源列表
    const resources = await page.evaluate(async ({ keyword }) => {
      const token = localStorage.getItem("GAMEMAKER_TOKEN") || "";
      const res = await fetch(
        `https://sszt-gateway.speiyou.com/beibo/game/config/resources?page=1&page_size=200&keyword=${encodeURIComponent(keyword)}`,
        { headers: { beibotoken: token } }
      );
      return res.json();
    }, { keyword: game.prefix });

    const resourceList = resources?.result?.list || resources?.result?.records || resources?.result || [];
    console.log(`✓ 拉取资源: ${Array.isArray(resourceList) ? resourceList.length : 0} 条`);

    // 建立 文件名(不含扩展名) -> URL 映射
    const resMap = {};
    if (Array.isArray(resourceList)) {
      for (const r of resourceList) {
        const urlField = r.url || r.file_url || r.resourceUrl || r.src || "";
        const nameField = r.name || r.file_name || r.fileName || r.resourceName || "";
        if (urlField && nameField) {
          // 去掉扩展名
          const baseName = nameField.replace(/\.[^.]+$/, "");
          resMap[baseName] = urlField;
          // 也存原始名
          resMap[nameField] = urlField;
        }
      }
    }

    // 保存资源映射
    fs.writeFileSync(
      path.join(OUTPUT_DIR, `${game.outputFile.replace("_current.json","")}_resources.json`),
      JSON.stringify({ total: Object.keys(resMap).length, map: resMap, raw: resourceList }, null, 2)
    );
    console.log(`✓ 资源映射: ${Object.keys(resMap).length} 条`);

    // Step 3&4: 解析配置并修正
    let config;
    try {
      const rawConfig = currentConfig.result.configuration;
      config = typeof rawConfig === "string" ? JSON.parse(rawConfig) : rawConfig;
    } catch (e) {
      console.error(`✗ 配置解析失败: ${e.message}`);
      results.push({ name: game.name, success: false, error: "配置解析失败" });
      continue;
    }

    const customGame = config.custom_game || config.customGame || [];
    console.log(`  原有 custom_game 关卡数: ${customGame.length}`);

    const missingResources = [];
    const fixLog = [];

    for (let i = 0; i < game.questions.length; i++) {
      const q = game.questions[i];
      const level = customGame[i];
      if (!level) {
        console.warn(`  ⚠ 关卡 ${i+1} 不存在，跳过`);
        continue;
      }

      // 找音频资源 key
      // 常见命名: "26春国际小班7赛跑_1_daddy" 或 "26春国际小班7赛跑daddy" 等
      // 尝试多种可能的命名
      const audioKeyPatterns = [
        `${game.prefix}_${i+1}_${q.audio}`,
        `${game.prefix}${i+1}_${q.audio}`,
        `${game.prefix}_${q.audio}_${i+1}`,
        `${game.prefix}_${q.audio}`,
        `${q.audio}`,
      ];

      let audioUrl = null;
      for (const key of audioKeyPatterns) {
        if (resMap[key]) { audioUrl = resMap[key]; break; }
        // 模糊匹配（key包含pattern）
        const fuzzyKey = Object.keys(resMap).find(k => 
          k.includes(`${game.prefix}`) && k.includes(`${q.audio}`) && k.includes(`${i+1}`)
        );
        if (fuzzyKey) { audioUrl = resMap[fuzzyKey]; break; }
      }

      if (!audioUrl) {
        // 尝试只按词模糊匹配（排除序号要求）
        const fuzzyKey = Object.keys(resMap).find(k =>
          k.toLowerCase().includes(game.prefix.toLowerCase()) && 
          k.toLowerCase().includes(q.audio.toLowerCase())
        );
        if (fuzzyKey) audioUrl = resMap[fuzzyKey];
      }

      if (!audioUrl) {
        missingResources.push(`音频: ${game.prefix} 题${i+1} ${q.audio}`);
      }

      // 找选项图片资源
      const optUrls = [];
      for (let j = 0; j < q.opts.length; j++) {
        const optWord = q.opts[j];
        const optKeyPatterns = [
          `${game.prefix}_${i+1}_${optWord}`,
          `${game.prefix}${i+1}_${optWord}`,
          `${game.prefix}_${optWord}_${i+1}`,
          `${game.prefix}_${optWord}`,
          `${optWord}`,
        ];
        let optUrl = null;
        for (const key of optKeyPatterns) {
          if (resMap[key]) { optUrl = resMap[key]; break; }
        }
        if (!optUrl) {
          // 模糊匹配
          const fuzzyKey = Object.keys(resMap).find(k =>
            k.toLowerCase().includes(game.prefix.toLowerCase()) &&
            k.toLowerCase().includes(optWord.toLowerCase()) &&
            k.toLowerCase().includes(`${i+1}`)
          );
          if (fuzzyKey) optUrl = resMap[fuzzyKey];
        }
        if (!optUrl) {
          // 再试只按前缀和词
          const fuzzyKey2 = Object.keys(resMap).find(k =>
            k.toLowerCase().includes(game.prefix.toLowerCase()) &&
            k.toLowerCase().includes(optWord.toLowerCase())
          );
          if (fuzzyKey2) optUrl = resMap[fuzzyKey2];
        }
        if (!optUrl) {
          missingResources.push(`选项图片: ${game.prefix} 题${i+1} 选${j+1} ${optWord}`);
        }
        optUrls.push(optUrl);
      }

      // 修改 level 的音频
      // 支持多种字段名
      let audioFixed = false;
      if (audioUrl) {
        if (level.title_res) {
          if (level.title_res.btnAudio !== undefined) { level.title_res.btnAudio = audioUrl; audioFixed = true; }
          else if (level.title_res.titleAudio !== undefined) { level.title_res.titleAudio = audioUrl; audioFixed = true; }
          else { level.title_res.btnAudio = audioUrl; audioFixed = true; }
        } else if (level.titleAudio !== undefined) {
          level.titleAudio = audioUrl; audioFixed = true;
        } else if (level.btnAudio !== undefined) {
          level.btnAudio = audioUrl; audioFixed = true;
        }
      }

      // 修改选项图片和switch
      const options = level.options || level.option || [];
      for (let j = 0; j < q.opts.length; j++) {
        const opt = options[j];
        if (!opt) continue;
        const isCorrect = (j + 1) === q.correct ? 1 : 0;

        // 设置 switch
        if (opt.item !== undefined) {
          opt.item.switch = isCorrect;
          if (optUrls[j]) opt.item.icon = optUrls[j];
        } else {
          opt.switch = isCorrect;
          if (optUrls[j]) opt.icon = optUrls[j];
        }
      }

      fixLog.push({
        q: i+1,
        audio: audioUrl ? "✓" : "✗MISSING",
        opts: optUrls.map((u,j) => u ? "✓" : `✗MISSING(${q.opts[j]})`),
        correct: q.correct,
        audioFixed,
      });
    }

    // 更新 config
    if (config.custom_game) config.custom_game = customGame;
    else if (config.customGame) config.customGame = customGame;

    // 保存修正后配置
    const fixedPath = path.join(OUTPUT_DIR, game.outputFile.replace("_current.json", "_fixed.json"));
    fs.writeFileSync(fixedPath, JSON.stringify(config, null, 2));
    console.log(`✓ 修正配置已保存到 ${fixedPath}`);

    // 输出修复日志
    for (const log of fixLog) {
      console.log(`  题${log.q}: 音频${log.audio} | 选项[${log.opts.join(",")}] | 正确项${log.correct}`);
    }
    if (missingResources.length > 0) {
      console.warn(`  ⚠ 缺失资源 (${missingResources.length}):`);
      for (const m of missingResources) console.warn(`    - ${m}`);
    }

    // Step 5: 保存配置（不发布）
    console.log(`\n  保存配置到服务器...`);
    const saveResult = await page.evaluate(async ({ gameId, configStr }) => {
      const token = localStorage.getItem("GAMEMAKER_TOKEN") || "";
      // 先获取游戏详情
      const getRes = await fetch(`https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=${gameId}`, {
        headers: { beibotoken: token },
      });
      const detail = await getRes.json();
      if (!detail || detail.code !== 0 || !detail.result) {
        return { error: `get detail failed: ${JSON.stringify(detail)}` };
      }
      const payload = { ...detail.result, configuration: JSON.parse(configStr) };
      const putRes = await fetch("https://sszt-gateway.speiyou.com/beibo/game/config/game", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json;charset=UTF-8",
          beibotoken: token,
        },
        body: JSON.stringify(payload),
      });
      return putRes.json();
    }, { gameId: game.game_id, configStr: JSON.stringify(config) });

    console.log(`  保存结果: ${JSON.stringify(saveResult)}`);

    const success = saveResult?.code === 0 || saveResult?.success === true;
    results.push({
      name: game.name,
      game_id: game.game_id,
      success,
      saveResult,
      missingResources,
      fixLog,
    });

    if (!success) {
      // 尝试 saveConfig 端点
      console.log(`  PUT失败，尝试 saveConfig 端点...`);
      const saveResult2 = await page.evaluate(async ({ gameId, configStr }) => {
        const token = localStorage.getItem("GAMEMAKER_TOKEN") || "";
        const res = await fetch("https://sszt-gateway.speiyou.com/beibo/game/config/saveConfig", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            beibotoken: token,
          },
          body: JSON.stringify({ game_id: gameId, configuration: configStr }),
        });
        return res.json();
      }, { gameId: game.game_id, configStr: JSON.stringify(config) });
      console.log(`  saveConfig 结果: ${JSON.stringify(saveResult2)}`);
      const success2 = saveResult2?.code === 0 || saveResult2?.success === true;
      results[results.length-1].success = success2;
      results[results.length-1].saveResult2 = saveResult2;
    }
  }

  // 最终摘要
  console.log("\n\n========== 修复摘要 ==========");
  for (const r of results) {
    const status = r.success ? "✅ 成功" : "❌ 失败";
    console.log(`${status} ${r.name} (${r.game_id})`);
    if (r.missingResources && r.missingResources.length > 0) {
      console.log(`  ⚠ 缺失资源: ${r.missingResources.length} 条`);
      r.missingResources.forEach(m => console.log(`    - ${m}`));
    } else if (r.missingResources) {
      console.log(`  ✓ 所有资源均找到`);
    }
    if (r.error) console.log(`  错误: ${r.error}`);
  }

  fs.writeFileSync(path.join(OUTPUT_DIR, "fix_summary.json"), JSON.stringify(results, null, 2));
  console.log("\n详细摘要已保存到 output/fix_summary.json");

  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
