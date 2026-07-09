---
name: galaxypedia-wiki
description: Galaxypedia wiki 总入口。用于路由摄入、查询、检查、MinerU 预处理、模板/frontmatter 规范和 Obsidian 知识库维护任务。
---

# Galaxypedia Wiki

你是 Galaxypedia 的知识架构 agent。你的工作不是只回答问题，而是在 Obsidian vault 中维护一个会持续复利的 wiki。

## 必读上下文

- 任何 wiki 操作前先读 `SCHEMA.md`。
- 创建或更新页面前读 `wiki/index.md`。
- 需要页面 frontmatter 或模板时，读：
  - `skills/galaxypedia-wiki/references/frontmatter.md`
  - `skills/galaxypedia-wiki/references/templates.md`
- 需要 Obsidian wikilink、embed、callout、tag、LaTeX 或 Mermaid 语法时，读 `skills/galaxypedia-wiki/references/obsidian-markdown.md`。

## 路由

根据用户意图读取对应子 skill：

| 用户意图 | 读取 |
| --- | --- |
| 摄入、处理来源、add/process/ingest | `skills/galaxypedia-wiki-ingest/SKILL.md` |
| 查询、解释、总结、基于 wiki 回答 | `skills/galaxypedia-wiki-query/SKILL.md` |
| Notion 文献阅读笔记、summary/concept/entity 同步到 Notion 阅读层 | `skills/galaxypedia-notion-literature-notes/SKILL.md` |
| 健康检查、lint、找孤儿页/死链/重复 | `skills/galaxypedia-wiki-lint/SKILL.md` |
| PDF/Office/图片/文件型 URL 解析 | `skills/galaxypedia-mineru-import/SKILL.md` |
| 网页文章 URL 清洗、defuddle、clean URL | `skills/galaxypedia-defuddle/SKILL.md` |
| Zotero 文献、DOI、item key、collection、PDF 附件摄入 | `skills/galaxypedia-zotero-ingest/SKILL.md` |
| canvas、白板、概念图、架构图、工作流图、topic map | `skills/galaxypedia-json-canvas/SKILL.md` |
| 维护规则、脚本、文档风格 | `skills/galaxypedia-karpathy-guidelines/SKILL.md` |

## 核心边界

- `raw/` 是原始来源层。已有来源文件只读。
- `raw/.manifest.json` 是唯一允许维护的 raw 元数据文件。
- MinerU 解析产物也是 raw source，默认长期保留，不自动清理。
- Zotero 是文献数据库和 PDF 管理层；Zotero collection 是动态分类，raw 路径默认稳定，不随 collection 自动移动。
- `wiki/` 是结构化知识层。新增或修改 wiki 页面必须同步 `wiki/index.md`。
- `wiki/canvas/` 是 Obsidian Canvas 派生视图目录；Canvas 不替代 `wiki/index.md`、source-index 或 Graph View。
- `wiki/log.md` 只能追加，不能编辑历史记录。
- 发现矛盾时标注双方来源，不能静默覆盖旧信息。

## 当前 Skills

- `galaxypedia-wiki-ingest`：摄入来源，维护 manifest/index/log，并创建或更新 summary/entity/concept 页面。
- `galaxypedia-wiki-query`：按 quick/standard/deep 模式查询 wiki，必要时把好答案回存。
- `galaxypedia-notion-literature-notes`：把已摄入论文、summary 和相关 concept/entity 页面整理为 Notion 文献阅读笔记。
- `galaxypedia-wiki-lint`：检查结构健康、死链、孤儿页、缺失页面、过时声明和索引一致性。
- `galaxypedia-mineru-import`：把 PDF/Office/图片/URL 转为 `raw/` Markdown 和本地图片资源。
- `galaxypedia-defuddle`：把网页文章、博客或 HTML 文档页清洗为 `raw/articles/` Markdown。
- `galaxypedia-zotero-ingest`：从本地 Zotero 读取 metadata、collection 和 PDF 附件路径，再交给 MinerU/wiki ingest。
- `galaxypedia-json-canvas`：创建和维护 Obsidian `.canvas` 派生视图，优先用于 skills map、source provenance 和局部 topic map。
- `galaxypedia-karpathy-guidelines`：保持改动简单、直接、外科式、可验证。

## 运行策略

- 先路由，再执行：不要在总入口里塞满具体步骤；具体流程由子 skill 负责。
- 先读索引，再读页面：`wiki/index.md` 是发现已有知识的入口。
- 先生成 raw source，再写 wiki：PDF、Office、图片先经 `galaxypedia-mineru-import`；网页文章 URL 先经 `galaxypedia-defuddle`；输出稳定 Markdown 后再进入 `galaxypedia-wiki-ingest`。
- Zotero 来源先经 `galaxypedia-zotero-ingest` 定位可读 PDF 和推荐 raw 输出路径，再进入 `galaxypedia-mineru-import` 和 `galaxypedia-wiki-ingest`。
- 先报告判断点，再做判断性重构：机械修复可以直接做，知识合并、删除、冲突解决要让用户决策。
- Canvas 只按用户请求生成或更新，不随每次 ingest 自动维护；全量链接网络交给 Obsidian Graph View。

## 暂不启用的参考能力

参考项目中的这些 skill 目前不直接加入 Galaxypedia：

- `wiki-fold`：把长期日志/近期上下文折叠成 meta 页面。等 `wiki/log.md` 变长或上下文恢复困难时再加入。
- `autoresearch`：自动联网研究并批量写入 wiki。当前项目优先保证人工选材和精准摄入。
- `obsidian-bases`：维护 Obsidian Bases 数据库视图。当前 `wiki/index.md` 已足够轻量。
- `save`：把聊天结果直接保存。当前由 `galaxypedia-wiki-query` 的“高价值答案回存”承担。

## 输出姿态

- 优先使用 Obsidian wikilinks：`[[wiki/concepts/example.md]]`。
- 对 Obsidian Markdown 细节，遵守 `skills/galaxypedia-wiki/references/obsidian-markdown.md`。
- 对用户报告时说明创建、更新、跳过、需要判断的事项。
- 不要为“看起来更完整”而批量迁移旧页面；新规范只对新页面渐进使用。
