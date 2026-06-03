---
name: galaxypedia-suite
description: 当进行 Galaxypedia 风格的 Obsidian wiki 工作时使用，包括摄入 raw 来源、查询或总结 wiki、检查 wiki 健康状态、用 Defuddle 清洗网页文章 URL、从 Zotero 摄入论文、创建 JSON Canvas 图谱，以及维护 Galaxypedia Markdown、脚本或 agent 规则。该技能会路由到 wiki-ingest、wiki-query、wiki-lint、defuddle、zotero-ingest、json-canvas 和 karpathy-guidelines 等内部模块。不要用它直接执行 MinerU 解析；PDF、Office、图片或远程文档解析应使用已安装的 MinerU 技能。
---

# Galaxypedia 技能套件

这是 Galaxypedia 技能套件的公开自动触发入口。它让 Codex 和 Claude Code 只暴露一个主技能，同时把详细流程保存在内部 reference 模块中，按需读取。

## 入口检查

1. 如果当前项目有 `SCHEMA.md`，任何 wiki 操作前先读它。
2. 如果当前项目有 `AGENTS.md` 或 `CLAUDE.md`，编辑前先读对应 agent 指南。
3. 如果当前项目有 `wiki/index.md`，创建或更新 wiki 页面前先读它。
4. 除非项目本地规则另有说明，把 `raw/` 视为不可变来源层。
5. 文档解析使用已安装的 MinerU 技能；本套件只在流程需要时路由到 MinerU。

## 路由

只读取当前任务需要的 reference 模块：

| 用户意图 | 读取 |
| --- | --- |
| 摄入、处理来源、更新 manifest/index/log、创建 summary/entity/concept 页面 | `references/wiki-ingest.md` |
| 基于 wiki 查询、解释、总结、比较或回答问题 | `references/wiki-query.md` |
| lint、健康检查、死链、孤儿页、重复页面、manifest/source-index 一致性 | `references/wiki-lint.md` |
| 将网页、文章、博客、新闻或 HTML 文档页 URL 清洗到 `raw/articles/` | `references/defuddle.md` |
| Zotero item、DOI、collection、本地论文元数据或 Zotero PDF 附件摄入 | `references/zotero-ingest.md` |
| Obsidian `.canvas`、JSON Canvas、topic map、workflow map、source provenance 可视化 | `references/json-canvas.md` |
| 维护 Markdown、脚本、agent 规则、项目指令或技能设计 | `references/karpathy-guidelines.md` |

## 共享参考

仅在 routed module 需要时读取：

- Frontmatter 约定：`references/frontmatter.md`
- 页面模板：`references/templates.md`
- Obsidian Markdown 语法：`references/obsidian-markdown.md`

## 边界

- 除非用户明确要求，不要把本套件拆成多个根目录技能。
- 不要静默覆盖项目内 `SCHEMA.md`、`AGENTS.md` 或 `CLAUDE.md` 的规则。
- 不要编辑 `wiki/log.md` 历史记录；只能追加。
- 不要修改 `raw/` 下已有文件；只有本地工作流允许时才创建派生 Markdown。
- 如果新证据与既有 wiki 内容冲突，保留双方有来源的说法，并询问用户如何解决。

## 报告

完成 routed task 后，说明创建、更新、跳过的内容，以及仍需用户判断的问题。报告必须绑定到实际读取或修改过的文件。
