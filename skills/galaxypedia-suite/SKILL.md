---
name: galaxypedia-suite
description: Galaxypedia 兼容入口。当用户显式调用旧的 galaxypedia-suite，或需要从一个入口路由 Galaxypedia wiki 摄入、查询、Notion 阅读笔记、lint、Defuddle、Zotero、MinerU、JSON Canvas、维护规则任务时使用。新任务优先触发独立的 galaxypedia-* 技能。
---

# Galaxypedia Suite

这是旧 `$galaxypedia-suite` 调用的兼容入口。SkillForge 现在把 Galaxypedia 工作流拆成多个可独立触发的根技能；本入口只负责识别用户意图并路由到对应技能，不承载具体执行流程。

## 入口检查

1. 如果当前项目有 `SCHEMA.md`，任何 wiki 操作前先读它。
2. 如果当前项目有 `AGENTS.md` 或 `CLAUDE.md`，编辑前先读对应 agent 指南。
3. 如果当前项目有 `wiki/index.md`，创建或更新 wiki 页面前先读它。
4. 除非项目本地规则另有说明，把 `raw/` 视为不可变来源层。

## 路由

根据用户意图改用对应独立技能：

| 用户意图 | 读取 |
| --- | --- |
| Galaxypedia 总入口、路由、schema/frontmatter/template 约定 | `galaxypedia-wiki` |
| 摄入、处理来源、更新 manifest/index/log、创建 summary/entity/concept 页面 | `galaxypedia-wiki-ingest` |
| 基于 wiki 查询、解释、总结、比较或回答问题 | `galaxypedia-wiki-query` |
| 将已摄入论文、summary、concept/entity 页面整理为 Notion 文献阅读笔记 | `galaxypedia-notion-literature-notes` |
| lint、健康检查、死链、孤儿页、重复页面、manifest/source-index 一致性 | `galaxypedia-wiki-lint` |
| 将网页、文章、博客、新闻或 HTML 文档页 URL 清洗到 `raw/articles/` | `galaxypedia-defuddle` |
| Zotero item、DOI、collection、本地论文元数据或 Zotero PDF 附件摄入 | `galaxypedia-zotero-ingest` |
| PDF、Office、图片或文件型 URL 解析为 Galaxypedia `raw/` source | `galaxypedia-mineru-import` |
| Obsidian `.canvas`、JSON Canvas、topic map、workflow map、source provenance 可视化 | `galaxypedia-json-canvas` |
| 维护 Markdown、脚本、agent 规则、项目指令或技能设计 | `galaxypedia-karpathy-guidelines` |

## 执行规则

- 新任务优先使用独立技能；只有用户显式调用 `$galaxypedia-suite` 时才停留在本入口。
- 需要 frontmatter、模板或 Obsidian Markdown 细节时，读取 `skills/galaxypedia-wiki/references/` 下的共享参考。
- 不要静默覆盖项目内 `SCHEMA.md`、`AGENTS.md` 或 `CLAUDE.md` 的规则。
- 不要编辑 `wiki/log.md` 历史记录；只能追加。
- 不要修改 `raw/` 下已有文件；只有本地工作流允许时才创建派生 Markdown。
- 如果新证据与既有 wiki 内容冲突，保留双方有来源的说法，并询问用户如何解决。

## 报告

完成 routed task 后，说明创建、更新、跳过的内容，以及仍需用户判断的问题。报告必须绑定到实际读取或修改过的文件。
