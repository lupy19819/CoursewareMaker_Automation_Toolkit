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
 *   - standard_question_toolkit/data/courseware_workflow_rules.json
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

const WORKFLOW_RULES = JSON.parse(
  fs.readFileSync(path.join(TOOLKIT_DATA, 'courseware_workflow_rules.json'), 'utf8')
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
const COMPONENT_ID_DRAG_ITEM = 'd8b73bec-f719-11ee-b9ef-8e2f78cd4bcd';
const COMPONENT_ID_DRAG_PLACE = 'f9b49402-f73d-11ee-b9ef-8e2f78cd4bcd';
const QUESTION_TEXT_RULES = CONSTANTS.question_text_labels || {};

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

function flattenAssetUrls(value, urls = []) {
  if (!value) return urls;
  if (typeof value === 'string') {
    if (value.startsWith('http')) urls.push(value);
    return urls;
  }
  if (Array.isArray(value)) {
    for (const item of value) flattenAssetUrls(item, urls);
    return urls;
  }
  if (typeof value === 'object') {
    for (const item of Object.values(value)) flattenAssetUrls(item, urls);
  }
  return urls;
}

function getByPath(obj, pathExpr) {
  if (!pathExpr) return undefined;
  const parts = String(pathExpr)
    .replace(/\[(\d+)\]/g, '.$1')
    .split('.')
    .filter(Boolean);
  let current = obj;
  for (const part of parts) {
    if (current == null) return undefined;
    current = current[part];
  }
  return current;
}

function loadConfigBaseline(baselinePath) {
  const fullPath = path.join(__dirname, '..', baselinePath);
  const detail = JSON.parse(fs.readFileSync(fullPath, 'utf8'));
  if (detail?.result?.configuration) return parseConfig(detail.result.configuration);
  return detail;
}

function inferConfigFamily(config) {
  if (Array.isArray(config?.custom_game)) return 'yundong_pk';
  if (Array.isArray(config?.game)) return 'componentized';
  return 'unknown';
}

function inferYundongSkinKey(config) {
  let best = { key: null, score: -1 };
  for (const [skinKey, skin] of Object.entries(WORKFLOW_RULES.yundong_pk_skins || {})) {
    const baseline = loadConfigBaseline(skin.baseline_json_path);
    let score = 0;
    const markerPath = skin.scene_marker_path;
    if (markerPath && getByPath(config, markerPath) === getByPath(baseline, markerPath)) score += 5;

    const targetImages = getByPath(config, 'common.custom.additional_environment.scene.images') || {};
    const baselineImages = getByPath(baseline, 'common.custom.additional_environment.scene.images') || {};
    for (const [key, value] of Object.entries(baselineImages)) {
      if (typeof value === 'string' && value && targetImages[key] === value) score += 1;
      if (value && typeof value === 'object') {
        const targetValue = targetImages[key];
        if (targetValue && JSON.stringify(targetValue) === JSON.stringify(value)) score += 1;
      }
    }

    if (score > best.score) best = { key: skinKey, score };
  }
  return best.key;
}

function getBaselineByKey(key) {
  return WORKFLOW_RULES.validation_baselines?.[key] || null;
}

function hasComponentId(components, componentId) {
  return components.some(comp => comp.component_id === componentId);
}

function inferStandardGameplayType(components) {
  if (hasComponentId(components, COMPONENT_ID_DRAG_ITEM) || hasComponentId(components, COMPONENT_ID_DRAG_PLACE)) {
    return 'standard_drag';
  }
  if (hasComponentId(components, COMPONENT_ID_FILL)) {
    return 'standard_fill_compute';
  }
  if (hasComponentId(components, COMPONENT_ID_CHOICE)) {
    return 'standard_choice';
  }
  return null;
}

function getWorkflowBaseline(gameplayType, skinKey) {
  if (!gameplayType || !skinKey) return null;
  return WORKFLOW_RULES.validation_baselines?.[`${gameplayType}__${skinKey}`] || null;
}

function getExpectedWorkflowAssets(baseline, assetKey) {
  const assets = baseline?.expected_config?.component_assets?.[assetKey];
  return new Set(flattenAssetUrls(assets));
}

function validateComponentUrlsAgainstSet({ comp, allowedSet, issues, levelNum, check, expected, fix }) {
  if (!allowedSet || allowedSet.size === 0) return;
  for (const { label, url } of collectStateUrls(comp)) {
    if (url && !allowedSet.has(url)) {
      issues.push({
        check,
        component: comp.component_data?.name || comp.component_name || '',
        levelNum,
        expected,
        actual: `state[${label}] ${url}`,
        fix
      });
    }
  }
}

function countLabelChars(value) {
  return String(value || '').replace(/\n/g, '').length;
}

function normalizeQuestionLabelName(name) {
  return String(name || '').replace(/-行\d+$/, '');
}

function getQuestionTextProfile(levelNum) {
  if (levelNum >= 1 && levelNum <= 5) return 'purple_choice_stem';
  if (levelNum >= 6 && levelNum <= 10) return 'yellow_body';
  if (levelNum >= 11 && levelNum <= 15) return 'blue_body';
  return 'default_stem';
}

function getQuestionTextProfileForLevel(levelNum, workflowBaseline = null) {
  const profileFromWorkflow = workflowBaseline?.expected_config?.question_text_profile;
  return profileFromWorkflow || getQuestionTextProfile(levelNum);
}

function collectQuestionTextLabels(components) {
  const groups = new Map();
  for (const comp of components) {
    const name = comp.component_data?.name || '';
    if (!name.includes('文本-题干')) continue;
    const state = comp.component_data?.states?.[0] || {};
    const label = state?.source?.MLabel || {};
    const transform = state?.transform || {};
    const key = normalizeQuestionLabelName(name);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push({ name, value: label.value || '', align: label.alignType || '', transform });
  }
  return groups;
}

function validateQuestionTextLabels(components, levelNum, workflowBaseline = null) {
  const issues = [];
  const profileName = getQuestionTextProfileForLevel(levelNum, workflowBaseline);
  const profile = QUESTION_TEXT_RULES.profiles?.[profileName] || QUESTION_TEXT_RULES.profiles?.default_stem;
  if (!profile) return issues;

  for (const [baseName, labels] of collectQuestionTextLabels(components)) {
    labels.sort((a, b) => Number(b.transform?.y || 0) - Number(a.transform?.y || 0));
    const joined = labels.map(item => item.value).join('');
    const charCount = countLabelChars(joined);
    const shouldSplit = charCount > profile.max_chars;
    const expectedAlign = shouldSplit ? 'left' : 'center';

    if (labels.some(item => String(item.value).includes('\n'))) {
      issues.push({
        check: '题干 label 换行',
        component: baseName,
        levelNum,
        expected: '每行题干必须是独立 MLabel，不允许在 MLabel.value 中嵌入换行符',
        actual: labels.map(item => JSON.stringify(item.value)).join(' / '),
        fix: `Level ${levelNum} [${baseName}] 应拆成多个独立 label`
      });
    }

    if (shouldSplit && labels.length < 2) {
      issues.push({
        check: '题干 label 拆行',
        component: baseName,
        levelNum,
        expected: `超过 ${profile.max_chars} 字时拆成 2 个左对齐 label`,
        actual: `${charCount} 字，${labels.length} 个 label`,
        fix: `Level ${levelNum} [${baseName}] 题干超长，应拆成两行独立 label`
      });
    }

    if (!shouldSplit && labels.length > 1) {
      issues.push({
        check: '题干 label 居中',
        component: baseName,
        levelNum,
        expected: `不超过 ${profile.max_chars} 字时保持 1 个居中 label`,
        actual: `${charCount} 字，${labels.length} 个 label`,
        fix: `Level ${levelNum} [${baseName}] 题干未超长，不应拆行`
      });
    }

    for (const item of labels) {
      if (item.align !== expectedAlign) {
        issues.push({
          check: '题干 label 对齐',
          component: item.name,
          levelNum,
          expected: expectedAlign,
          actual: item.align,
          fix: `Level ${levelNum} [${item.name}] alignType 应为 ${expectedAlign}`
        });
      }
    }

    if (labels.length > 1) {
      const firstW = labels[0].transform?.w;
      for (const item of labels.slice(1)) {
        if (!isApprox(item.transform?.w, firstW, 1)) {
          issues.push({
            check: '题干 label 同宽',
            component: item.name,
            levelNum,
            expected: firstW,
            actual: item.transform?.w,
            fix: `Level ${levelNum} 拆行题干的两个 label 应同宽，确保左边缘对齐`
          });
        }
      }
    }
  }

  return issues;
}

function validateWorkflowBaseline(components, levelNum, expectedSkin) {
  const issues = [];
  const warnings = [];
  const gameplayType = inferStandardGameplayType(components);
  if (!gameplayType) {
    warnings.push({
      check: '工作流题型识别',
      component: `Level ${levelNum}`,
      levelNum,
      detail: '未识别为标准选择/填空/拖拽题，跳过 workflow baseline 校验',
      actual: '未找到 choice / fill_blank / drag_item / drag_place 组件'
    });
    return { issues, warnings, baseline: null, gameplayType };
  }

  const baseline = getWorkflowBaseline(gameplayType, expectedSkin?.skin_key);
  if (!baseline) {
    issues.push({
      check: '工作流基准',
      component: `Level ${levelNum}`,
      levelNum,
      expected: `validation_baselines.${gameplayType}__${expectedSkin?.skin_key}`,
      actual: '缺少基准配置',
      fix: `在 courseware_workflow_rules.json 中补齐 ${gameplayType} + ${expectedSkin?.skin_name || expectedSkin?.skin_key} 的 expected_config`
    });
    return { issues, warnings, baseline: null, gameplayType };
  }

  const gameplayRule = WORKFLOW_RULES.gameplay_types?.[gameplayType] || {};
  for (const componentId of gameplayRule.required_component_ids || []) {
    if (!hasComponentId(components, componentId)) {
      issues.push({
        check: '工作流必需组件',
        component: `Level ${levelNum}`,
        levelNum,
        expected: componentId,
        actual: '缺失',
        fix: `Level ${levelNum} ${gameplayRule.name || gameplayType} 必须包含组件 ${componentId}`
      });
    }
  }
  for (const componentId of gameplayRule.forbidden_component_ids || []) {
    if (hasComponentId(components, componentId)) {
      issues.push({
        check: '工作流互斥组件',
        component: `Level ${levelNum}`,
        levelNum,
        expected: `不包含 ${componentId}`,
        actual: '已出现',
        fix: `Level ${levelNum} ${gameplayRule.name || gameplayType} 不应混入组件 ${componentId}`
      });
    }
  }

  return { issues, warnings, baseline, gameplayType };
}

function validateYundongPkConfig(config) {
  const issues = [];
  const warnings = [];
  const skinKey = inferYundongSkinKey(config);
  const baseline = getBaselineByKey(`yundong_pk__${skinKey}`);

  if (!baseline) {
    issues.push({
      check: '运动PK皮肤基准',
      component: 'root',
      expected: 'yundong_pk__run / yundong_pk__swim / yundong_pk__racecar',
      actual: skinKey || '未识别',
      fix: '按具体配置 JSON 识别运动PK皮肤失败，请确认配置来自 run/swim/racecar baseline 之一'
    });
    return { issues, warnings, skinKey, baseline: null };
  }

  const expected = baseline.expected_config || {};
  if (expected.data_shape === 'custom_game' && !Array.isArray(config.custom_game)) {
    issues.push({
      check: '运动PK数据结构',
      component: 'root',
      expected: 'custom_game 数组',
      actual: typeof config.custom_game,
      fix: '运动PK配置必须使用 custom_game 结构，不能使用组件化 game 结构'
    });
  }

  for (const key of expected.root_keys || []) {
    if (!(key in config)) {
      issues.push({
        check: '运动PK根字段',
        component: 'root',
        expected: key,
        actual: '缺失',
        fix: `运动PK配置必须保留 baseline JSON 的根字段 ${key}`
      });
    }
  }

  for (const requiredPath of expected.required_paths || []) {
    if (getByPath(config, requiredPath) == null) {
      issues.push({
        check: '运动PK必需路径',
        component: 'root',
        expected: requiredPath,
        actual: '缺失',
        fix: `运动PK配置缺少 ${requiredPath}，应从 ${expected.baseline_json_path} 保留结构`
      });
    }
  }

  const baselineConfig = loadConfigBaseline(expected.baseline_json_path);
  const baselineFirstTopic = getByPath(baselineConfig, 'custom_game[0].topics[0].title_res');
  const configFirstTopic = getByPath(config, 'custom_game[0].topics[0].title_res');
  if (baselineFirstTopic && configFirstTopic) {
    for (const key of Object.keys(baselineFirstTopic)) {
      if (!(key in configFirstTopic)) {
        issues.push({
          check: '运动PK题目结构',
          component: 'custom_game[0].topics[0].title_res',
          expected: key,
          actual: '缺失',
          fix: `运动PK题目 title_res 必须保留 ${expected.baseline_json_path} 中的字段 ${key}`
        });
      }
    }
  }

  return { issues, warnings, skinKey, baseline };
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
  const workflowCheck = validateWorkflowBaseline(components, levelNum, expectedSkin);
  issues.push(...workflowCheck.issues);
  warnings.push(...workflowCheck.warnings);
  const workflowBaseline = workflowCheck.baseline;
  const workflowAssets = workflowBaseline?.expected_config?.component_assets || {};

  issues.push(...validateQuestionTextLabels(components, levelNum, workflowBaseline));

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
        const expectedBackground = workflowBaseline?.expected_config?.background || expectedSkin.background || expectedSkin.skin_assets?.background;
        if (expectedBackground && baseVal !== expectedBackground) {
          issues.push({
            check: '皮肤-背景',
            component: name,
            levelNum,
            expected: `${expectedSkin.skin_name} ${expectedBackground}`,
            actual:   `hash=${actualHash}  url=${baseVal}`,
            fix:      `Level ${levelNum} (${skinMapping.level_range[0]}–${skinMapping.level_range[1]}关) 应使用 ${expectedSkin.skin_name}，当前背景图不匹配`
          });
        } else if (!expectedBackground && !baseVal.includes(expectedSkin.skin_key)) {
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
      const baselineInputSet = getExpectedWorkflowAssets(workflowBaseline, 'input_box');
      const allowedSet = baselineInputSet.size > 0
        ? baselineInputSet
        : new Set(Object.values(expectedSkin.skin_assets.input_box).filter(v => v.startsWith('http')));
      for (const { label, url } of stateUrls) {
        if (url && !allowedSet.has(url)) {
          issues.push({
            check: '皮肤-输入框',
            component: name,
            levelNum,
            expected: `${expectedSkin.skin_name} 输入框 expected_config`,
            actual: `state[${label}] ${url}`,
            fix: `Level ${levelNum} [${name}] 输入框状态资源必须来自 courseware_workflow_rules.json 的 expected_config.component_assets.input_box`
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
      const keyboardAllowed = new Set([
        ...flattenAssetUrls(workflowAssets.keyboard),
        ...flattenAssetUrls(WORKFLOW_RULES.shared_assets?.keyboard_disabled_states)
      ]);
      if (keyboardAllowed.size > 0) {
        for (const { label, url } of stateUrls) {
          if (url && !keyboardAllowed.has(url)) {
            issues.push({
              check: '工作流-键盘资源',
              component: name,
              levelNum,
              expected: `${expectedSkin?.skin_name || ''} 键盘 normal/pressed + 共用 disabled expected_config`,
              actual: `state[${label}] ${url}`,
              fix: `Level ${levelNum} [${name}] 键盘资源必须来自 courseware_workflow_rules.json 的 expected_config.component_assets.keyboard`
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

    if (cid === COMPONENT_ID_CHOICE) {
      validateComponentUrlsAgainstSet({
        comp,
        allowedSet: getExpectedWorkflowAssets(workflowBaseline, 'choice_button'),
        issues,
        levelNum,
        check: '工作流-选择按钮资源',
        expected: `${expectedSkin?.skin_name || ''} 选择按钮 expected_config`,
        fix: `Level ${levelNum} [${name}] 选择按钮状态资源必须来自 courseware_workflow_rules.json 的 expected_config.component_assets.choice_button`
      });
    }

    if (cid === COMPONENT_ID_DRAG_ITEM) {
      validateComponentUrlsAgainstSet({
        comp,
        allowedSet: getExpectedWorkflowAssets(workflowBaseline, 'drag_item'),
        issues,
        levelNum,
        check: '工作流-拖拽物资源',
        expected: `${expectedSkin?.skin_name || ''} 拖拽物 expected_config`,
        fix: `Level ${levelNum} [${name}] 拖拽物状态资源必须来自 courseware_workflow_rules.json 的 expected_config.component_assets.drag_item`
      });
    }

    if (cid === COMPONENT_ID_DRAG_PLACE) {
      validateComponentUrlsAgainstSet({
        comp,
        allowedSet: getExpectedWorkflowAssets(workflowBaseline, 'drag_place'),
        issues,
        levelNum,
        check: '工作流-放置框资源',
        expected: `${expectedSkin?.skin_name || ''} 放置框 expected_config`,
        fix: `Level ${levelNum} [${name}] 放置框状态资源必须来自 courseware_workflow_rules.json 的 expected_config.component_assets.drag_place`
      });
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
    console.log(`已获取配置，关卡数: ${(config.game || config.custom_game || []).length}`);
  }

  const family = inferConfigFamily(config);
  if (family === 'yundong_pk') {
    const { issues, warnings, skinKey, baseline } = validateYundongPkConfig(config);
    console.log('\n' + '═'.repeat(50));
    console.log('  运动PK配置合规性校验报告');
    console.log('═'.repeat(50));
    console.log(`  数据结构 : custom_game`);
    console.log(`  识别皮肤 : ${skinKey || '未识别'}`);
    console.log(`  基准 JSON: ${baseline?.expected_config?.baseline_json_path || '无'}`);
    console.log(`  关卡数   : ${(config.custom_game || []).length}`);
    console.log(`  ❌ 错误  : ${issues.length}`);
    console.log(`  ⚠️  警告  : ${warnings.length}`);
    console.log('─'.repeat(50));
    for (const iss of issues) {
      console.log(`❌ [${iss.check}] ${iss.fix}`);
      console.log(`   期望: ${iss.expected}`);
      console.log(`   实际: ${iss.actual}`);
    }
    for (const w of warnings) {
      console.log(`⚠️  [${w.check}] ${w.detail}`);
      console.log(`   实际: ${w.actual}`);
    }
    console.log('─'.repeat(50));
    if (issues.length === 0) {
      console.log('\n✅ 运动PK配置通过 workflow baseline 校验\n');
      process.exit(0);
    }
    console.log(`\n❌ 共 ${issues.length} 个错误需要修复，${warnings.length} 个警告需要确认\n`);
    process.exit(1);
  }

  if (family === 'unknown') {
    console.error('\n无法识别配置数据结构：既没有 game 数组，也没有 custom_game 数组');
    process.exit(1);
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
