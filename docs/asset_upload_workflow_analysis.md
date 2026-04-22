# CoursewareMaker 素材批量上传工作流

> **版本**: 1.0  
> **更新时间**: 2026-04-16  
> **脚本路径**: `D:\codexProject\scripts\courseware_bulk_upload_assets.mjs`

---

## 📋 概述

CoursewareMaker素材批量上传工具，用于将本地图片、音频、视频等素材批量上传到CoursewareMaker平台的资源库。

### 核心功能

- ✅ 从Chrome获取登录态（Token）
- ✅ 获取腾讯云COS临时凭证
- ✅ 批量上传文件到COS
- ✅ 自动注册资源到CoursewareMaker
- ✅ 支持并发上传（默认5个并发）
- ✅ 自动分类和打标签

---

## 🔄 工作流程

```
开始
  ↓
┌─────────────────────────┐
│ 1. 从Chrome获取认证信息   │ → GAMEMAKER_TOKEN + 用户信息
│    (通过CDP)             │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│ 2. 获取COS临时AK/SK      │ → accessKeyId, accessKeySecret, securityToken
│    (调用API)             │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│ 3. 扫描本地文件夹        │ → 获取所有PNG文件列表
│    (按文件名排序)        │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│ 4. 批量上传到COS         │ → 并发上传，生成COS URL
│    (签名+PUT请求)        │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│ 5. 注册资源到平台        │ → POST /beibo/game/config/resource
│    (一次性批量注册)      │
└───────────┬─────────────┘
            ↓
           完成
```

---

## 🚀 使用方法

### 基本用法

```bash
node D:\codexProject\scripts\courseware_bulk_upload_assets.mjs <文件夹路径>
```

**示例**：
```bash
node D:\codexProject\scripts\courseware_bulk_upload_assets.mjs "D:\通前下载\写作-第一部分"
```

### 完整参数

```bash
node D:\codexProject\scripts\courseware_bulk_upload_assets.mjs <文件夹路径> \
  [--category image] \
  [--ext .png] \
  [--topic-id 1] \
  [--tag-id 7] \
  [--concurrency 5] \
  [--port 9222]
```

---

## ⚙️ 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `<文件夹路径>` | *必填* | 包含素材文件的本地文件夹 |
| `--category` | `image` | 素材类别：`image`/`audio`/`video`/`spine` |
| `--ext` | `.png` | 文件扩展名（带点） |
| `--topic-id` | `1` | 主题ID：`1`=通用 |
| `--tag-id` | `7` | 标签ID：`7`=贴画 |
| `--concurrency` | `5` | 并发上传数量（1-10） |
| `--port` | `9222` | Chrome调试端口 |

---

## 📦 素材类型对照表

### Category 类型

| category | type值 | 说明 |
|----------|-------|------|
| `image` | `1` | 图片（PNG/JPG等） |
| `audio` | `2` | 音频（MP3/WAV等） |
| `video` | `3` | 视频（MP4/WebM等） |
| `spine` | `4` | Spine动画 |

### 主题ID (topic-id)

| ID | 名称 |
|----|------|
| `1` | 通用 |
| ... | （其他主题）|

### 标签ID (tag-id)

| ID | 名称 |
|----|------|
| `7` | 贴画 |
| ... | （其他标签）|

---

## 🔧 技术细节

### 1. 认证流程

**从Chrome获取Token**：
```javascript
// 通过CDP从localStorage读取
{
  token: localStorage.getItem("GAMEMAKER_TOKEN"),
  user: JSON.parse(localStorage.getItem("GAMEMAKER_USER_INFO") || "{}")
}
```

**获取COS临时凭证**：
```javascript
GET https://sci-gateway-pre.speiyou.com/config/argument/storage/ops/cos/v1/ak?channel=courseware-maker-1252161091
Headers: { beibotoken: TOKEN }
```

**返回**：
```json
{
  "code": 0,
  "result": {
    "accessKeyId": "xxx",
    "accessKeySecret": "xxx",
    "securityToken": "xxx",
    "expiration": "2026-04-16T12:00:00Z"
  }
}
```

### 2. COS上传

**URL格式**：
```
https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/<key>
```

**Key格式**：
```
assets/<category>/<empNo>/<date>/<random-hex>.<ext>
```

**示例**：
```
assets/image/12345/2026-04-16/a1b2c3d4e5f6.png
```

**签名算法**：
- 使用COS V4签名算法（HMAC-SHA1）
- 包含：accessKeyId, keyTime, headerList, signature
- 需要`x-cos-security-token`头

### 3. 资源注册

**API端点**：
```
POST https://sszt-gateway.speiyou.com/beibo/game/config/resource
```

**请求体**：
```json
[
  {
    "name": "素材名称",
    "url": "https://courseware-maker-xxx.cos.xxx/xxx.png",
    "tag": [7],
    "type": 1,
    "topic": [1],
    "desc": "",
    "category": "image",
    "subject": []
  }
]
```

**返回**：
```json
{
  "code": 0,
  "msg": "success"
}
```

---

## 📝 使用场景

### 场景1: 上传贴画素材

```bash
# 上传D盘"写作素材"文件夹下的所有PNG
node D:\codexProject\scripts\courseware_bulk_upload_assets.mjs "D:\写作素材"
```

### 场景2: 上传音频素材

```bash
# 上传音频文件（MP3）
node D:\codexProject\scripts\courseware_bulk_upload_assets.mjs "D:\音频素材" \
  --category audio \
  --ext .mp3 \
  --tag-id 8
```

### 场景3: 自定义并发数

```bash
# 使用10个并发上传
node D:\codexProject\scripts\courseware_bulk_upload_assets.mjs "D:\图片素材" \
  --concurrency 10
```

---

## ✅ 前置条件

### 1. Chrome调试模式已启动

```bash
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome-debug"
```

### 2. 已登录CoursewareMaker

访问并登录：
```
https://coursewaremaker.speiyou.com/
```

### 3. 文件准备

- 文件夹内包含要上传的素材文件
- 文件命名规范（最好使用有意义的名称，扩展名会被去除）
- 确保文件格式正确

---

## 📊 执行输出

### 成功示例

```
Uploading 15 file(s) as 张三 (12345)
[1/15] 背景图1.png -> https://courseware-maker-xxx.cos.xxx/xxx.png
[2/15] 背景图2.png -> https://courseware-maker-xxx.cos.xxx/xxx.png
[3/15] 角色1.png -> https://courseware-maker-xxx.cos.xxx/xxx.png
...
[15/15] 道具5.png -> https://courseware-maker-xxx.cos.xxx/xxx.png
Done. Registered 15 resource(s).
```

### 错误示例

**Chrome未登录**：
```
Error: Could not read GAMEMAKER_TOKEN from the controlled browser
```

**文件夹为空**：
```
Error: No .png files found in D:\素材文件夹
```

**COS上传失败**：
```
Error: COS PUT failed for 图片1.png: HTTP 403 Access Denied
```

---

## 🔍 集成到完整工作流

在完整的游戏创建流程中，素材上传应该在**生成配置之前**完成。

### 更新后的完整流程

```
1. 资源同步（可选）
   ↓
1.5. 素材批量上传（新增！）← 在这里
   ↓
2. 生成游戏配置
   ↓
3. 创建游戏
   ↓
4. 导入配置
   ↓
5. 生成分享链接
   ↓
6. 发布游戏
```

### 为什么在生成配置之前？

1. **资源引用**：配置生成时需要引用资源库中的素材URL
2. **避免重复**：先上传，配置生成时直接使用已有资源
3. **一致性**：确保配置中引用的资源在平台上都存在

---

## 🎯 完整示例：从素材到游戏

```bash
# Step 0: 准备素材文件
# 将所有PNG放在 D:\游戏素材\新一年级\

# Step 1: 批量上传素材
node D:\codexProject\scripts\courseware_bulk_upload_assets.mjs "D:\游戏素材\新一年级"

# Step 2: 同步资源库（让配置生成脚本能找到新上传的素材）
python D:\codexProject\sync_courseware_resources.py

# Step 3: 生成配置（此时会引用刚上传的素材）
python D:\codexProject\build_yundong_pk_config.py 题目表.xlsx

# Step 4: 创建游戏
node D:\codexProject\create_game_auto.js "游戏名称" "模板ID" ""

# Step 5: 导入配置
GAME_ID=$(cat D:\codexProject\latest_game_id.txt)
node D:\codexProject\save_game_config_via_cdp.js "$GAME_ID" "配置.json"

# Step 6: 发布游戏
node D:\codexProject\publish_game_auto.js "$GAME_ID" 2026 "2" "1"
```

---

## ⚠️ 注意事项

### 1. 文件命名

- ✅ **推荐**：`背景图1.png`、`角色-小明.png`
- ❌ **避免**：`IMG_0001.png`、`未命名.png`
- 资源名称会去掉扩展名，所以文件名要有意义

### 2. 资源分类

根据素材用途选择正确的category：
- 图片 → `--category image`
- 音频 → `--category audio`
- 视频 → `--category video`

### 3. 并发控制

- 默认5个并发通常足够
- 网络好可以增加到10
- 不建议超过10（可能触发API限流）

### 4. 重复上传

- 脚本不会检查资源是否已存在
- 每次运行都会创建新资源（即使文件相同）
- 建议先检查资源库，避免重复上传

### 5. 资源清理

- 上传的资源会永久保存在COS和平台
- 如需删除，需在CoursewareMaker平台手动删除

---

## 🐛 故障排除

### 问题1: Token获取失败

**错误**：
```
Error: Could not read GAMEMAKER_TOKEN from the controlled browser
```

**原因**：
- Chrome未启动调试模式
- 未登录CoursewareMaker
- 端口不是9222

**解决**：
1. 确认Chrome以调试模式启动
2. 访问并登录 `https://coursewaremaker.speiyou.com/`
3. 检查端口：`curl http://localhost:9222/json/version`

---

### 问题2: COS凭证获取失败

**错误**：
```
Error: Failed to get COS credential: HTTP 401
```

**原因**：
- Token过期
- 权限不足

**解决**：
1. 重新登录CoursewareMaker
2. 确认账号有资源上传权限

---

### 问题3: 文件上传失败

**错误**：
```
Error: COS PUT failed for xxx.png: HTTP 403
```

**原因**：
- COS凭证过期
- 文件过大
- 网络问题

**解决**：
1. 重新运行脚本（会获取新凭证）
2. 检查文件大小（建议<10MB）
3. 检查网络连接

---

### 问题4: 资源注册失败

**错误**：
```
Error: Resource create failed: HTTP 500
```

**原因**：
- 服务器错误
- 请求体格式错误

**解决**：
1. 检查上传的文件是否全部成功
2. 重试资源注册步骤

---

## 📚 API参考

### COS临时凭证API

```
GET https://sci-gateway-pre.speiyou.com/config/argument/storage/ops/cos/v1/ak
  ?channel=courseware-maker-1252161091
Headers:
  beibotoken: <TOKEN>
  referer: https://coursewaremaker.speiyou.com/
  origin: https://coursewaremaker.speiyou.com
```

### COS上传API

```
PUT https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/<key>
Headers:
  authorization: <COS-Signature>
  content-type: image/png
  content-length: <file-size>
  x-cos-storage-class: STANDARD
  x-cos-security-token: <security-token>
```

### 资源注册API

```
POST https://sszt-gateway.speiyou.com/beibo/game/config/resource
Headers:
  beibotoken: <TOKEN>
  content-type: application/json;charset=UTF-8
Body: [
  {
    "name": "资源名称",
    "url": "COS-URL",
    "tag": [7],
    "type": 1,
    "topic": [1],
    "desc": "",
    "category": "image",
    "subject": []
  }
]
```

---

## 📝 脚本位置

```
D:\codexProject\scripts\courseware_bulk_upload_assets.mjs
```

---

## 🔗 相关文档

- [完整自动化指南](COURSEWAREMAKER_AUTOMATION_GUIDE.md)
- [资源同步工具](sync_courseware_resources.py)
- [配置生成工具](build_yundong_pk_config.py)

---

**最后更新**: 2026-04-16  
**版本**: 1.0
