# CoursewareMaker Resources

`latest_resources.json` 是工作流默认使用的资源清单，必须保留在 git 项目内。

用途：

- 生成脚本按资源名查找 URL。
- 素材上传前检查同名资源。
- 校验题目相关资源是否来自已确认资源映射。

更新方式：

```bash
python3 scripts/sync_courseware_resources.py --split-by-category
```

同步脚本会读取现有 `resources/latest_resources.json`，再从 CoursewareMaker resources API 拉取最新列表并合并。合并规则是按资源 `id` 优先去重；没有 `id` 时用 `category/name/url` 组合去重，并保留 `update_time` 更新的记录。

当前 `latest_resources.json` 首次由以下来源合并：

- git 历史版本 `latest_resources.json`
- 本地最新导出 `编辑器上传素材_resources导出.json`
