# 运动PK游戏（赛跑/游泳/赛车）新建与导入流程

> 基于 2026-04-17 16:03-16:04 浏览器操作的完整网络日志分析
> 2026-05-08 补充：`create_game_auto.js` 修复后已跑通“新建空壳 → PUT 导入配置 → 严格比对”。

## 捕获的关键信息

- **新建游戏名称**: 测试测试记录
- **新建游戏 game_id**: `fe5da00c-3a33-11f1-bdd1-76b63c7cf458`
- **新建游戏 数据库id**: `11839`
- **使用的模板 template_id**: `47995925-fb37-11ef-8c1b-ce918f8037e8`
- **组件 component_id**: `21dcca07-c1e6-11ef-895a-4eb2c30c826b` (运动PK赛)
- **组件版本**: `0.1.0`
- **游戏类型**: `game_type: 2` (定制游戏)

## 当前已验证自动化流程

```bash
# 1. 创建运动PK空壳游戏
node scripts/create_game_auto.js \
  "测试运动PK新建" \
  "47995925-fb37-11ef-8c1b-ce918f8037e8" \
  ""

GAME_ID=$(cat latest_game_id.txt)

# 2. 校验配置
python3 scripts/validate_yundong_pk_config.py "配置.json" 赛跑

# 3. 导入配置并保存
python3 scripts/upload_game_config.py "$GAME_ID" "配置.json"
```

实测结果：

- 新建 `game_id`: `0ada627b-4a89-11f1-a80e-6effa3ce9c89`
- 新建元数据: `game_type=2`
- 编辑器入口: `#/customEditor?game_id=0ada627b-4a89-11f1-a80e-6effa3ce9c89`
- 导入接口: `PUT /beibo/game/config/game`
- 导入结果: `code=0, msg=success`
- 线上配置与本地配置标准化比对: `exact_equal=true`

---

## 完整流程（6步）

### Step 1: 获取定制游戏模板列表
- **API**: `GET /beibo/game/config/templates?page=1&page_size=40&template_type=2`
- **作用**: 获取可用的定制游戏模板列表
- **返回**: 模板列表，包含 template_id、组件信息等
- **运动PK赛模板ID**: `47995925-fb37-11ef-8c1b-ce918f8037e8`

### Step 2: 查询模板关联的组件信息
- **API**: `GET /beibo/game/config/component?component_id=21dcca07-c1e6-11ef-895a-4eb2c30c826b`
- **作用**: 获取运动PK赛组件的完整配置结构（edit_custom_data）
- **返回**: 组件名称、版本、配置模板结构、图片等
- **关键信息**:
  - component_name: "运动PK赛"
  - component_en_name: "yundongPK"
  - version: "0.1.0"
  - component_url: 组件zip包地址

### Step 3: 导航到编辑器（选择模板）
- **页面跳转**: `/#/customEditor?template_id=47995925-fb37-11ef-8c1b-ce918f8037e8`
- **触发动作**: 
  - 获取模板详情 (`GET /beibo/game/config/template?template_id=...`)
  - 加载资源库 (`POST /beibo/game/config/resources`，tag=6,7,8,9,10 分别加载不同类型资源)
  - 获取组件版本列表 (`GET /beibo/game/config/componentVersions?component_id=...`)

### Step 4: 创建游戏（核心步骤）
- **API**: `POST /beibo/game/config/game`
- **请求头**: `beibotoken` + `Content-Type: application/json;charset=UTF-8`
- **请求体**: 
  ```json
  {
    "user": "江昊（jiang hao）",
    "configuration": { ... },  // 完整的游戏配置对象
    "game_type": 2,
    "game_name": "测试测试记录",
    "template_id": "47995925-fb37-11ef-8c1b-ce918f8037e8"
  }
  ```
- **响应**: 
  ```json
  {
    "code": 0,
    "result": { "game_id": "fe5da00c-3a33-11f1-bdd1-76b63c7cf458" },
    "msg": "success"
  }
  ```

#### configuration 对象的核心结构:
```json
{
  "additional_custom_game": [],
  "common": {
    "additional_settlement_component": { ... },
    "custom": {
      "additional_environment": {
        "character": {
          "audios": { "audioIP1": "...", "audioIP1_wrong": "...", ... },
          "images": { "headNormal1": { "image": "...", "x": -503, "y": 78 }, ... },
          "spine": { "IP1": { "spine": "...", "x": -875, "y": 92.5 }, ... }
        },
        "scene": {
          "ShowCelebrate": true,
          "audios": { "audioCelebrate": "...", "bgm1": "...", "bgm2": "..." },
          "images": { "bgBack1": "...", "bgBack2": "...", ... },
          "isRepeat": true,
          "showSelectIP": true,
          "spine": { "crossLine_back": { ... }, "crossLine_front": { ... }, "fireworks": { ... } }
        }
      },
      "component": {
        "component_id": "21dcca07-c1e6-11ef-895a-4eb2c30c826b",
        "component_name": "运动PK赛",
        "component_url": "...yundongPK.zip",
        "name": "yundongPK",
        "version": "0.1.0"
      },
      "environment": { ... }  // 与 additional_environment 相同
    },
    "global_config": {
      "font_url": "...FZY4JW.ttf",
      "score_config": { "additional_score": [], "score": [], "type": "average" },
      "transparent_canvas": false
    },
    "level_settlement": { ... },
    "levels": { ... },
    "settlement_component": { ... }
  },
  "components": [
    {
      "component_id": "21dcca07-c1e6-11ef-895a-4eb2c30c826b",
      "component_url": "...yundongPK.zip"
    }
  ],
  "custom_game": [
    {
      "id": "gamenext_level_uuid_<随机UUID>",
      "topics": [
        {
          "CustomTopicConfig": { "maxQuestionNum": 1, "minQuestionNum": 1 },
          "title_res": {
            "audioSpine": { "scale": 1, "spine": "" },
            "btnAudio": "",
            "icon": "",
            "options": [
              {
                "item": {
                  "bgOptionCorrect": "",
                  "bgOptionNormal": "",
                  "bgOptionWrong": "",
                  "correctSpine": { "scale": 1, "spine": "" },
                  "icon": "",
                  "opstionText": { "MLabel": "", "fontSize": 70 }
                }
              }
            ],
            "titleAuido": "",
            "titleBg": "",
            "titleText": { "MLabel": "", "fontSize": 70 }
          }
        }
      ]
    }
  ]
}
```

### Step 5: 锁定游戏
- **API**: `POST /beibo/game/config/lock`
- **请求体**:
  ```json
  {
    "id": "fe5da00c-3a33-11f1-bdd1-76b63c7cf458",
    "version": "0.0",
    "type": "game"
  }
  ```
- **时间**: 创建成功后立即执行

### Step 6: 保存游戏（含截图上传）
- **6a. 上传截图到COS**:
  - `PUT https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/screenshot/{game_id}-game.jpg`
  - 需要COS签名Authorization头

- **6b. 保存游戏配置**:
  - **API**: `PUT /beibo/game/config/game`
  - **请求体**: 完整的游戏对象（含id、game_id、game_name、configuration等所有字段）
  - **关键**: configuration 字段是**对象**，不是字符串

- **6c. 解锁游戏**:
  - **API**: `POST /beibo/game/config/unlock`
  - **请求体**:
    ```json
    {
      "id": "fe5da00c-3a33-11f1-bdd1-76b63c7cf458",
      "version": "0.0",
      "type": "game"
    }
    ```

---

## 与之前 create_game_auto.js 的差异

| 对比项 | 旧脚本问题 | 修复后脚本 / 实际浏览器流程 |
|--------|-----------|---------------|
| **创建API** | POST /beibo/game/config/game | 相同 ✅ |
| **game_type** | 硬编码 `1`，会把运动PK建成普通游戏 | 运动PK模板自动使用 `2` ✅ |
| **编辑器入口** | `#/editor?game_id=...` | `#/customEditor?game_id=...` ✅ |
| **配置路径** | 传 `""` 会报“配置文件不存在” | 允许空配置，先建壳再导入 ✅ |
| **user 字段** | 只读 `USER_INFO`，实际为空时写成“用户” | 读取 `GAMEMAKER_USER_INFO` 并输出 `姓名（拼音）` ✅ |
| **configuration来源** | 可为空壳 `{}`，后续通过 `upload_game_config.py` 注入 | 浏览器完整流程会带默认配置；自动化已验证空壳 + 导入也可用 |
| **锁定** | 创建后锁定 | 相同 ✅ |
| **保存** | 曾尝试 `POST`，可能被当成新建/另存版本 | 更新已有游戏使用 `PUT + credentials: include` ✅ |
| **截图** | 无 | 上传截图到COS |

### 结论
修复后的 `create_game_auto.js` 可以创建运动PK空壳游戏，关键是 `game_type=2` 和 `customEditor` 入口正确。后续用 `upload_game_config.py` 通过 `PUT` 导入完整 `custom_game` 配置，已验证可直接写入原 `game_id`。

---

## 自动化方案

### 方案A: 沿用现有脚本（推荐 - 已验证可用）
```bash
# 1. 创建空壳游戏
node create_game_auto.js "游戏名" "47995925-fb37-11ef-8c1b-ce918f8037e8" ""
# 2. 注入配置
python3 scripts/upload_game_config.py "$GAME_ID" "config.json"
```

### 方案B: 新建脚本（带默认配置创建 - 可选）
创建 `create_yundongpk_game.js`，在创建时直接传入完整的默认configuration，
后续只需更新 custom_game 部分的题目数据即可。

---

## 关键发现

1. **模板ID固定**: 运动PK赛模板 = `47995925-fb37-11ef-8c1b-ce918f8037e8`
2. **组件ID固定**: 运动PK赛组件 = `21dcca07-c1e6-11ef-895a-4eb2c30c826b`
3. **默认配置可复用**: 创建时传入的 configuration 是模板的默认配置，不同皮肤（赛跑/游泳/赛车）的差异在 `custom.environment` 和 `custom.additional_environment` 中
4. **game_type=2**: 定制游戏固定值
5. **version初始值**: "0.0"
6. **截图非必需**: 创建和保存可以不上传截图，截图只是用于列表页显示
