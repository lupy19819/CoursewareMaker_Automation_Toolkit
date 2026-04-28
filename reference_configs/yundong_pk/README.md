# 运动PK 标准参考配置

## 用途
**仅用于校验，不可直接上传覆盖游戏**

1. **结构校验**：对比生成配置与参考配置的 JSON 骨架（字段名、层级、数组长度）
2. **皮肤/美术资源复用**：从参考配置提取以下字段用于填充新配置
   - `additional_environment` → `audioSpine`（喇叭动效 spine）
   - `additional_environment` → `titleBg`（题目背景图，按关卡轮换）
   - `additional_environment` → `bgOptionNormal / bgOptionCorrect / bgOptionWrong`（选项底图三态）
   - `additional_environment` → `bgBack`（关卡背景）

## 文件说明

| 文件 | 玩法 | 来源游戏 |
|---|---|---|
| `赛跑_reference.json` | 赛跑（跑酷） | 国际新小班暑J7跑酷赛跑 `32992acd-3fbe-11f1-906b-da4a8224db76` |
| `游泳_reference.json` | 游泳 | 国际新小班暑J8跑酷游泳 `33e6a1b0-3fbe-11f1-906b-da4a8224db76` |
| `赛车_reference.json` | 赛车 | 国际新小班暑J9跑酷赛车 `c5e2b08a-3fbe-11f1-906b-da4a8224db76` |

## 校验规则

- `correctSpine`：赛跑/游泳/赛车均留空（不配正确动效）
- `audioSpine.spine`：有题目音频时必须非空，从本参考取同玩法的 spine URL
- 选项底图：统一用第1关底图填充所有关卡
- `titleBg`：按关卡索引轮换（参考配置中的 titleBg 列表）

## 更新时机

当有更好的标准游戏时，手动替换对应 JSON 文件并更新本 README。
