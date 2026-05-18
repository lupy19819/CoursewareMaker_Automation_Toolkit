# Validation Fixtures

本目录只存放“案例回归”材料，不替代规则脚本校验。

校验优先级：

1. 规则脚本校验：必须执行，用来判断本次配置是否符合当前游戏规则。
2. 参考配置不变量：必须执行，只比较固定模板骨架和固定资源，不比较题目动态字段。
3. 关卡级参考 profile：按 `reference_configs/level_references/index.json` 逐关匹配结构和题型形态，例如同一个游戏内 L1 是 4 槽、L2 是 3 槽，或一关是纯音频题干、另一关是音频+文字/配图题干时必须分开校验。profile 同时记录 `format_signature`（模板承载能力）和 `content_signature`（本关实际非空内容），覆盖题干文字/音频/配图、选项文字/音频/图片。
4. 案例回归：可选执行，用来发现生成脚本退化。案例缺失时记录 warning，不得视为规则校验通过。
5. 回读比对和预览：主工作流执行，保存后必须做。

每个游戏目录至少保留 `fixture.json`，用于让 `workflow/audit_workflow.py` 知道该分支已经被登记；完整回归案例再继续补齐以下文件：

- `input.json` 或 `input.xlsx`：最小题目输入。
- `reference.json`：该案例使用的参考配置或路径说明。
- `expected.config.json`：生成后的期望配置。
- `expected.build-meta.json`：生成元数据。
- `README.md`：说明覆盖的规则点和运行命令。

关卡级参考库由以下命令生成；新增/替换参考配置后必须重跑：

```bash
python3 scripts/build_reference_level_index.py
```

目录约定：

```text
validation_fixtures/
  yundong_pk/run/
  yundong_pk/swim/
  yundong_pk/racecar/
  template_game/monster/
  template_game/fanboat/
  template_game/train/
  template_game/road_adventure/
  template_game/spelling/
  template_game/magic_spelling/
  template_game/bridge/
  template_game/amusement_park/
  standard_component/standard_component/
  standard_component/choice/
  standard_component/fill_compute/
  standard_component/drag/
```
