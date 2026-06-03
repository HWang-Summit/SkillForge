# wiki-lint 模块

迁移自 Galaxypedia `skills/wiki-lint/SKILL.md`。本文件是 `galaxypedia-suite` 的内部参考模块，不是 SkillForge v0.1.0 中独立安装的根目录技能。

# Wiki Lint

使用这个 skill 做 `/lint`、健康检查、结构检查、索引一致性检查。

## 检查范围

1. `wiki/index.md` 是否列出所有 wiki 页面。
2. index 中的链接是否存在。
3. wiki 页面是否有入链或合理入口。
4. 页面中提到的既有实体/概念是否缺少 wikilink。
5. 是否存在明显重复概念页或实体页。
6. 是否有 “currently/recently/as of/当前/最近” 等时间敏感声明。
7. 是否有矛盾声明没有 callout。
8. `raw/.manifest.json` 是否为合法 JSON，记录的 source 是否存在。
9. `wiki/meta/source-index.md` 是否存在，且与 manifest 和 wiki 页面 `## Sources` 一致。
10. `.canvas` 文件是否为合法 JSON，边引用是否有效，file node 是否指向真实 vault 文件。

## 执行顺序

1. 读 `SCHEMA.md` 和 `wiki/index.md`。
2. 用 `find wiki -name '*.md'` 获取实际页面列表。
3. 解析 index 链接，找未索引页面和死链。
4. 扫描 wikilinks，统计入链，找孤儿页。
5. 抽样或针对性扫描页面内容，找过时声明、空标题、缺失来源、frontmatter 缺口。
6. 校验 `raw/.manifest.json`：JSON 合法、source 路径存在、生成页面路径存在。
7. 校验 `wiki/meta/source-index.md`：source 路径存在，关联 wiki 页面存在，manifest 中已摄入 source 有对应条目。
8. 如存在 `wiki/canvas/*.canvas`，校验 JSON、node/edge id、edge 端点和 file node 路径。
9. 先做机械修复，再输出需要用户判断的问题。

## 处理策略

- 机械修复可以做：补 index 缺失条目、修正明显的总页数。
- 判断性问题只报告：孤儿页是否删除、矛盾如何解决、旧页面是否迁移 frontmatter。
- 不自动删除页面。
- 不自动改写旧页面 frontmatter。
- 不自动合并近似页面；只报告候选重复项和建议。
- 不把 lint 变成大规模格式化。每次只修复能证明正确的小问题。

## 问题分级

- `error`：死链、index 指向不存在页面、manifest JSON 损坏。
- `warning`：孤儿页、缺失来源、source-index 缺项、frontmatter 缺口、时间敏感声明。
- `suggestion`：可增强交叉引用、候选重复概念、可拆分长页面。

## 报告格式

```markdown
# Lint Report YYYY-MM-DD

## Summary
- Pages scanned:
- Issues found:
- Mechanical fixes:
- Needs review:

## Mechanical Fixes
-

## Needs Review
-

## Manifest
-

## Source Index
-
```

如果创建 lint 报告页面，放在 `wiki/meta/lint-report-YYYY-MM-DD.md`，并更新 `wiki/index.md`、追加 `wiki/log.md`。

## 何时运行

- 连续摄入 5-10 个 sources 后。
- 大幅修改 `skills/`、`SCHEMA.md` 或索引结构后。
- 用户觉得查询质量下降、出现找不到页面、重复页面或引用混乱时。
