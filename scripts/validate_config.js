/**
 * validate_config.js — 游戏配置合规性校验
 *
 * 用途：
 *   对已生成或已导入的游戏配置，逐关校验布局坐标、皮肤 hash 和键盘资源
 *   是否符合 layout_constants.json + component_skin_inventory.json 中的最新规范。
 *
 * 用法：
 *   node scripts/validate_config.js <game_id>
 *   node scripts/validate_config.js --file <path/to/config.json>
 *
 * 依赖：
 *   - standard_question_toolkit/data/layout_constants.json
 *   - standard_question_toolkit/data/component_skin_inventory.json
 *   - Playwright（已在 package.json 中声明）
 *   - Edge 浏览器已启动并监听 localhost:9222
 *
 * 退出码：
 *   0 = 全部检查通过
 *   1 = 发现不合规项（或运行出错）
 */

'use strict';

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// ─── 加载规范常量 ───────────────────────────────────────────────────────────

const TOOLKIT_DATA = path.join(__dirname, '..', 'standard_question_toolkit', 'data');

const CONSTANTS = JSON.parse(
  fs.readFileSync(path.join(TOOLKIT_DATA, 'layout_constants.json'), 'utf8')
);

const SKIN_INV = JSON.parse(
  fs.readFileSync(path.join(TOOLKIT_DATA, 'component_skin_inventory.json'), 'utf8')
);

// 构建 skin_key → skin 对象的索引
const SKIN_BY_KEY = {};
for (const skin of SKIN_INV.skins) {
  SKIN_BY_KEY[skin.skin_key] = skin;
}

// disabled 共用 URL 集合（用于快速成员判断）
const DISABLED_URLS = new Set(Object.values(CONSTANTS.keyboard_disabled_shared).filter(v => typeof v === 'string' && v.startsWith('http')));

const COMPONENT_ID_CHOICE = '3b9b8ec3-f7d3-11ee-b9ef-8e2f78cd4bcd';
const COMPONENT_ID_FILL   = '0b26ef14-f7e0-11ee-b9ef-8e2f78cd4bcd';

// 浮点比较容差（单位 px）
const TOLERANCE = 1;

// ─── 辅助函数 ────────────────────────────────────────────────────────────────

function isApprox(actual, expected, tol = TOLERANCE) {
  if (actual == null || expected == null) return false;
  return Math.abs(Number(actual) - Number(expected)) <= tol;
}

/** 从 URL 中提取前 8 位十六进制 hash（文件名首段） */
function extractUrlHash(url) {
  if (!url || typeof url !== 'string') return '';
  const filename = url.split('/').pop().replace('.png', '');
  return filename.slice(0, 8);
}

/** 根据关卡编号（1起）确定应使用的皮肤 */
function getSkinForLevel(levelNum) {
  for (const mapping of CONSTANTS.skin_level_mapping) {
    if (levelNum >= mapping.level_range[0] && levelNum <= mapping.level_range[1]) {
      return { mapping, skin: SKIN_BY_KEY[mapping.skin_key] };
    }
  }
  return { mapping: null, skin: null };
}

/** 递归收集组件内所有图片 URL（包括 states 里面的） */
function collectStateUrls(comp) {
  const urls = [];
  const stateArr = comp?.component_data?.states || [];
  for (const state of stateArr) {
    // 真实路径：state.source.MSprite.value（不是 state.components.base.MSprite.value）
    const val = state?.source?.MSprite?.value;
    if (val) urls.push({ label: state.label || state.stateName || '', url: val });
  }
  return urls;
}

// ─── 关卡校验 ────────────────────────────────────────────────────────────────

// z 层级规范（component_data.name → expected zIndex）
const Z_RULES = [
  { match: name => name.includes('题型说明'),                              expected: 0 },
  { match: name => name.includes('背景图片') || name.includes('【勿动】背景'), expected: 1 },
  { match: name => name.includes('配图'),                                  expected: 3 },
  { match: name => name.includes('【可修改】文本') || name.includes('文本-条件'), expected: 4 },
  { match: name => name.includes('输入框') || name.includes('简易数字键盘') || name.includes('选项'), expected: 6 },
  { match: name => name.includes('撒花'),                                  expected: 99 },
];

function validateLevel(level, levelIndex) {
  const issues = [];
  const warnings = [];
  const levelNum = levelIndex + 1;
  // 正确路径：level.components（不是 level.levelData.components）
  const components = level?.components || [];

  const { mapping: skinMapping, skin: expectedSkin } = getSkinForLevel(levelNum);

  for (const comp of components) {
    // 正确路径：component_data.name（不是顶层 componentName）
    const name     = comp.component_data?.name || comp.component_name || '';
    const cid      = comp.component_id  || '';
    // 真实路径：states[0].transform（不是 component_data.layout）
    const layout   = comp.component_data?.states?.[0]?.transform || {};
    // 真实路径：states[0].source.MSprite.value（不是 components.base.MSprite.value）
    const baseVal  = comp.component_data?.states?.[0]?.source?.MSprite?.value || '';

    // ── 0. z 层级校验 ────────────────────────────────────────────────────────
    const actualZ = comp.component_data?.zIndex;
    for (const rule of Z_RULES) {
      if (rule.match(name)) {
        if (actualZ !== rule.expected) {
          issues.push({
            check: 'z层级',
            component: name,
            levelNum,
            expected: rule.expected,
            actual:   actualZ,
            fix:      `Level ${levelNum} [${name}] zIndex 应为 ${rule.expected}，当前为 ${actualZ}`
          });
        }
        break;
      }
    }

    // ── 1. 背景图皮肤 hash ───────────────────────────────────────────────────
    if (name.includes('背景图片')) {
      if (expectedSkin) {
        const actualHash = extractUrlHash(baseVal);
        if (!baseVal.includes(expectedSkin.skin_key)) {
          issues.push({
            check: '皮肤-背景',
            component: name,
            levelNum,
            expected: `${expectedSkin.skin_name} hash=${expectedSkin.skin_key}`,
            actual:   `hash=${actualHash}  url=${baseVal}`,
            fix:      `Level ${levelNum} (${skinMapping.level_range[0]}–${skinMapping.level_range[1]}关) 应使用 ${expectedSkin.skin_name}，当前背景图不匹配`
          });
        }
      }
    }

    // ── 2. 输入框皮肤（含 states 里的图） ────────────────────────────────────
    if (name.includes('输入框') && expectedSkin?.skin_assets?.input_box) {
      const stateUrls = collectStateUrls(comp);
      const allowedSet = new Set(Object.values(expectedSkin.skin_assets.input_box).filter(v => v.startsWith('http')));
      for (const { label, url } of stateUrls) {
        if (url && !allowedSet.has(url)) {
          warnings.push({
            check: '皮肤-输入框',
            component: name,
            levelNum,
            detail: `state[${label}] URL 不属于 ${expectedSkin.skin_name} 输入框资源集`,
            actual: url
          });
        }
      }
    }

    // ── 3. 选择题选项坐标和宽度 ──────────────────────────────────────────────
    if (cid === COMPONENT_ID_CHOICE) {
      // y 坐标
      if (!isApprox(layout.y, CONSTANTS.choice_3_options.y)) {
        issues.push({
          check: '选项 y',
          component: name,
          levelNum,
          expected: CONSTANTS.choice_3_options.y,
          actual:   layout.y,
          fix:      `Level ${levelNum} 选项 y 应为 ${CONSTANTS.choice_3_options.y}`
        });
      }
      // 宽度（3选 474 或 4选 264）
      const valid_ws = [CONSTANTS.choice_3_options.w, CONSTANTS.choice_4_options.w];
      if (!valid_ws.some(w => isApprox(layout.w, w))) {
        issues.push({
          check: '选项宽度',
          component: name,
          levelNum,
          expected: '474（3选项）或 264（4选项）',
          actual:   layout.w,
          fix:      `Level ${levelNum} 选项宽度不符合规范`
        });
      }
    }

    // ── 4. 键盘 y 坐标 ───────────────────────────────────────────────────────
    if (name.includes('简易数字键盘') || name.includes('SimpleNumericKeyboard')) {
      if (!isApprox(layout.y, CONSTANTS.keyboard.y)) {
        issues.push({
          check: '键盘 y',
          component: name,
          levelNum,
          expected: CONSTANTS.keyboard.y,
          actual:   layout.y,
          fix:      `Level ${levelNum} 键盘 y 应为 ${CONSTANTS.keyboard.y}`
        });
      }
      // disabled 三态 URL 校验（跨皮肤共用）
      const stateUrls = collectStateUrls(comp);
      for (const { label, url } of stateUrls) {
        if (label.toLowerCase().includes('disabled') || label.includes('禁用')) {
          if (url && !DISABLED_URLS.has(url)) {
            issues.push({
              check: '键盘 disabled',
              component: name,
              levelNum,
              expected: '2026-04-13 跨皮肤共用 disabled URL',
              actual:   url,
              fix:      `Level ${levelNum} 键盘 disabled 态（${label}）应使用 keyboard_disabled_shared 中的共用资源`
            });
          }
        }
      }
    }

    // ── 5. 填空框尺寸和缩放 ───────────────────────────────────────────────────
    if (cid === COMPONENT_ID_FILL) {
      if (!isApprox(layout.w, CONSTANTS.fill_blank.w) ||
          !isApprox(layout.h, CONSTANTS.fill_blank.h)) {
        issues.push({
          check: '填空框尺寸',
          component: name,
          levelNum,
          expected: `${CONSTANTS.fill_blank.w} × ${CONSTANTS.fill_blank.h}`,
          actual:   `${layout.w} × ${layout.h}`,
          fix:      `Level ${levelNum} 填空框尺寸不应偏离 218×131`
        });
      }
      if (!isApprox(layout.scaleX, 1, 0.01) || !isApprox(layout.scaleY, 1, 0.01)) {
        issues.push({
          check: '填空框缩放',
          component: name,
          levelNum,
          expected: 'scaleX=1, scaleY=1',
          actual:   `scaleX=${layout.scaleX}, scaleY=${layout.scaleY}`,
          fix:      `Level ${levelNum} 填空框不应缩放变形`
        });
      }
    }
  }

  return { issues, warnings };
}

// ─── 通过 CDP 拉取配置 ────────────────────────────────────────────────────────

async function fetchConfigViaCDP(gameId) {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9222');
  try {
    const context = browser.contexts()[0];
    const page = context.pages().find(p => (p.url() || '').includes('coursewaremaker.speiyou.com'));
    if (!page) throw new Error('未找到 CoursewareMaker 标签页，请先打开 coursewaremaker.speiyou.com');

    const raw = await page.evaluate(async (gid) => {
      const token = localStorage.getItem('GAMEMAKER_TOKEN') || '';
      if (!token) throw new Error('GAMEMAKER_TOKEN 缺失');
      const res = await fetch(`https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=${gid}`, {
        headers: { beibotoken: token }
      });
      const data = await res.json();
      if (!data || data.code !== 0) throw new Error(`接口返回错误: ${JSON.stringify(data)}`);
      return data?.result?.configuration || '';
    }, gameId);

    return raw;
  } finally {
    await browser.close();
  }
}

/** 解析配置字符串（兼容双重编码） */
function parseConfig(raw) {
  if (typeof raw === 'object') return raw;
  const s = typeof raw === 'string' ? raw.trim() : String(raw);
  // 双重编码："\"{ ... }\""
  if (s.startsWith('"')) return JSON.parse(JSON.parse(s));
  return JSON.parse(s);
}

// ─── 主流程 ───────────────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);
  let config;

  if (args[0] === '--file') {
    if (!args[1]) { console.error('缺少 --file 参数'); process.exit(1); }
    const raw = fs.readFileSync(args[1], 'utf8');
    config = parseConfig(raw);
    console.log(`\n读取本地文件: ${args[1]}`);
  } else {
    const gameId = args[0];
    if (!gameId) {
      console.error('用法:');
      console.error('  node scripts/validate_config.js <game_id>');
      console.error('  node scripts/validate_config.js --file <config.json>');
      process.exit(1);
    }
    console.log(`\n正在获取游戏 ${gameId} 的配置...`);
    const raw = await fetchConfigViaCDP(gameId);
    config = parseConfig(raw);
    console.log(`已获取配置，关卡数: ${(config.game || []).length}`);
  }

  const levels = config.game || [];
  if (levels.length === 0) {
    console.warn('\n警告：game 数组为空，无关卡可校验');
    process.exit(0);
  }

  let totalIssues = 0;
  let totalWarnings = 0;
  const report = [];

  for (let i = 0; i < levels.length; i++) {
    const { issues, warnings } = validateLevel(levels[i], i);
    totalIssues += issues.length;
    totalWarnings += warnings.length;
    report.push({ levelNum: i + 1, issues, warnings });
  }

  // ── 打印报告 ──────────────────────────────────────────────────────────────
  console.log('\n' + '═'.repeat(50));
  console.log('  配置合规性校验报告');
  console.log('═'.repeat(50));
  console.log(`  检查关卡数 : ${levels.length}`);
  console.log(`  ❌ 错误    : ${totalIssues}`);
  console.log(`  ⚠️  警告    : ${totalWarnings}`);
  console.log('─'.repeat(50));

  for (const { levelNum, issues, warnings } of report) {
    if (issues.length === 0 && warnings.length === 0) {
      console.log(`✅ Level ${String(levelNum).padStart(2)} : 通过`);
      continue;
    }
    if (issues.length > 0) {
      console.log(`❌ Level ${String(levelNum).padStart(2)} : ${issues.length} 个错误`);
      for (const iss of issues) {
        console.log(`   [${iss.check}] ${iss.fix}`);
        console.log(`      期望: ${iss.expected}`);
        console.log(`      实际: ${iss.actual}`);
      }
    }
    if (warnings.length > 0) {
      console.log(`⚠️  Level ${String(levelNum).padStart(2)} : ${warnings.length} 个警告`);
      for (const w of warnings) {
        console.log(`   [${w.check}] ${w.detail}`);
        console.log(`      实际: ${w.actual}`);
      }
    }
  }

  console.log('─'.repeat(50));

  if (totalIssues === 0) {
    console.log('\n✅ 所有关卡通过合规校验\n');
    process.exit(0);
  } else {
    console.log(`\n❌ 共 ${totalIssues} 个错误需要修复，${totalWarnings} 个警告需要确认\n`);
    process.exit(1);
  }
}

main().catch(err => {
  console.error('\n运行出错:', err.message || err);
  process.exit(1);
});
