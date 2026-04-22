# 运动PK游戏（赛跑/游泳/赛车）新建流程分析

> 基于 2026-04-17 16:03-16:04 浏览器操作的完整网络日志分析

## 捕获的关键信息

- **新建游戏名称**: 测试测试记录
- **新建游戏 game_id**: `fe5da00c-3a33-11f1-bdd1-76b63c7cf458`
- **新建游戏 数据库id**: `11839`
- **使用的模板 template_id**: `47995925-fb37-11ef-8c1b-ce918f8037e8`
- **组件 component_id**: `21dcca07-c1e6-11ef-895a-4eb2c30c826b` (运动PK赛)
- **组件版本**: `0.1.0`
- **游戏类型**: `game_type: 2` (定制游戏)

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

| 对比项 | 之前的脚本 | 实际浏览器流程 |
|--------|-----------|---------------|
| **创建API** | POST /beibo/game/config/game | 相同 ✅ |
| **请求体** | 只传 game_name + template_id + game_type | 传了完整的 configuration 对象 |
| **configuration来源** | 空（后续通过 save_game_config_via_cdp.js 注入） | 直接从模板获取默认配置 |
| **锁定** | 创建后锁定 | 相同 ✅ |
| **保存** | 通过CDP注入配置后保存 | 保存包含默认配置的完整对象 |
| **截图** | 无 | 上传截图到COS |

### 结论
之前的 `create_game_auto.js` 创建的是**空壳游戏**（无configuration），需要后续通过 `save_game_config_via_cdp.js` 注入配置。
浏览器的完整流程是**带默认配置创建**，可以直接在编辑器中编辑。

两种方式都能工作，但完整流程更接近真实使用场景，创建出来的游戏可以直接在编辑器中打开编辑。

---

## 自动化方案

### 方案A: 沿用现有脚本（推荐 - 已验证可用）
```bash
# 1. 创建空壳游戏
node create_game_auto.js "游戏名" "47995925-fb37-11ef-8c1b-ce918f8037e8" ""
# 2. 注入配置
node save_game_config_via_cdp.js "$GAME_ID" "config.json"
```

### 方案B: 新建脚本（带默认配置创建 - 更完整）
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
