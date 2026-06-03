---
name: galaxypedia-wiki-ingest
description: 摄入 Galaxypedia 来源。读取 raw/ 来源，按需触发 MinerU，检查 manifest，创建/更新 summary、entity、concept、index 和 log。
---

# Wiki Ingest

使用这个 skill 处理 `/ingest`、摄入来源、处理 PDF/Markdown/URL、把资料整合进 wiki 等任务。

## 入口检查

1. 读 `SCHEMA.md`、`skills/galaxypedia-wiki/SKILL.md`。
2. 读 `skills/galaxypedia-wiki/references/frontmatter.md` 和 `templates.md`。
3. 读 `wiki/index.md`，确认已有页面。
4. 确认 `raw/.manifest.json` 存在；没有则创建最小结构。
5. 确认 `wiki/meta/source-index.md` 存在；没有则创建 source provenance 目录页。
6. 如果用户给的是多个来源，先列出将处理的文件和顺序；除非用户明确说“全部直接摄入”，否则先确认。

## 来源预处理

正式摄入来源必须是 `raw/` 下可读 Markdown。

- `raw/**/*.md`：直接摄入。
- PDF、Office、图片、本地非 Markdown 文件：先读 `skills/galaxypedia-mineru-import/SKILL.md`，用 MinerU 生成 `raw/.../*.mineru.md` 和同名资源目录，再摄入生成的 Markdown。
- 远程 URL：先判断类型。网页文章、博客、HTML 文档页读 `skills/galaxypedia-defuddle/SKILL.md`，清洗并保存为 `raw/articles/*.md`；PDF、Office、图片 URL 读 `skills/galaxypedia-mineru-import/SKILL.md`。
- Zotero 文献、DOI、item key、collection 或 Zotero PDF 附件：先读 `skills/galaxypedia-zotero-ingest/SKILL.md`，从本地 Zotero 只读解析 metadata、collection 和可读 PDF 路径，再用 MinerU 生成 `raw/papers/<collection-path>/*.mineru.md`。
- `raw/` 下已有非 Markdown：只新增 `.mineru.md`，不要修改原文件。
- 如果 MinerU 已经生成过 `.mineru.md`，优先摄入现有 Markdown；只有用户要求重新解析、或源文件明显更新时才重新跑 MinerU。
- 如果 Markdown 中包含 `![[...]]` 本地图片嵌入，阅读与论文论证相关的图、表、流程图；不要把图片当作可忽略附件。

## 来源分层

- 原始 PDF、Office、图片、网页快照是第一层 source。
- MinerU 生成的 `.mineru.md` 是可摄入 source，仍属于 `raw/`，默认长期保留。
- Zotero PDF 由 Zotero 管理，不复制进 `raw/`；Zotero ingest 的稳定 raw source 是 MinerU 生成的 Markdown。
- Zotero collection 是动态分类。摄入时 collection 可决定初始 raw 路径；摄入后 collection 变化只更新 `wiki/meta/zotero-index.md`，不自动移动已摄入 raw 文件。
- `wiki/summaries/` 是知识层摘要，不是 raw 的替代品。
- `wiki/index.md` 是 wiki 知识页目录，不列出全部 raw 文件。
- `wiki/meta/source-index.md` 是 raw source 到 wiki 页面之间的人工可读追溯目录。
- 不要把 MinerU 临时状态、API token、上传 URL 或签名 URL 写入 `raw/`、`wiki/` 或日志。

## Manifest

`raw/.manifest.json` 用于避免重复摄入，是 `raw/` 下唯一允许维护的元数据文件。

格式：

```json
{
  "version": 1,
  "sources": {
    "raw/papers/example.mineru.md": {
      "hash": "sha256...",
      "ingested_at": "YYYY-MM-DD",
      "pages_created": [],
      "pages_updated": [],
      "mineru_output": "raw/papers/example.mineru.md"
    }
  }
}
```

摄入前：

1. 对最终 Markdown 来源计算 SHA-256。
2. 如果 manifest 中同路径 hash 相同，跳过并报告“已摄入且未变化”。用户明确说 force/re-ingest 时才继续。
3. 如果 hash 不同或不存在，继续摄入。

摄入后：

1. 记录 hash、日期、创建页面、更新页面、MinerU 输出路径。
2. 保留旧 source 文件记录，不删除历史条目。
3. 重摄入同一 source 时，保留该 source 当前关联的全部 wiki 页面，不要只记录本次 touched pages 导致 provenance 变弱。
4. Zotero 来源额外保留 flat provenance：`source_system`、`zotero_item_key`、`zotero_attachment_key`、`doi`、`title`、`authors`、`year`、`venue`、`zotero_collections`、`primary_collection`、`source_pdf_path`、`pdf_link_mode`、`raw_path_status`、`previous_raw_paths`。

## Source Index

`wiki/meta/source-index.md` 维护 raw source 与 wiki 页面之间的人工可读关系。

每个 source 条目至少记录：

- raw source 路径。
- source 类型和摄入状态。
- 摄入日期和 hash。
- MinerU output，如果有。
- 对应 summary 页面。
- 相关 entity、concept、comparison 或 meta 页面。
- Zotero 来源的 item key、attachment key、DOI、摄入时 collections、source PDF path 和 raw path status。

普通查询不从 source-index 开始；source-index 只用于核对原文、重摄入、来源审计和追溯。

## 单来源摄入流程

1. 完整读取最终 Markdown 来源，包括 Obsidian 图片嵌入指向的本地图片。
2. 判断来源主语言，并用该语言写 wiki 展示内容：英文来源写英文页面，中文来源写中文页面；产品名、命令名、API 和通用技术术语可保留原文。
3. 给用户一段摘要，并询问要强调的角度。用户说“直接摄入/just ingest”时可跳过等待。
4. 搜索 `wiki/index.md`，避免重复页面。
5. 在 `wiki/summaries/` 创建来源摘要页。
6. 为关键实体创建或更新 `wiki/entities/` 页面。
7. 为关键概念创建或更新 `wiki/concepts/` 页面。
8. 只在有明确综合价值时创建 `wiki/comparisons/` 页面。
9. 更新 `wiki/index.md` 的条目和总页数。
10. 更新 `wiki/meta/source-index.md`，记录 source 到 summary/entity/concept/comparison 的关系。
11. 追加 `wiki/log.md`，列出 source、created、updated。
12. 更新 `raw/.manifest.json`。

## 批量摄入流程

批量摄入时不要把每篇资料都做成完全孤立的操作：

1. 列出 sources，识别哪些需要 MinerU，哪些可直接摄入。
2. 逐个生成最终 Markdown source，并记录成功/失败。
3. 对每个 source 判断主语言并创建同语言 summary；实体/概念页可以暂缓到本批次的综合阶段统一更新。
4. 批次结束后做一次交叉引用 pass：找共同实体、共同概念、明显冲突和互补关系。
5. 最后统一更新 `wiki/index.md`、`wiki/meta/source-index.md`，追加一次 `wiki/log.md`，更新 `raw/.manifest.json`。

如果批量超过 10 个 source，分批报告进度，避免长时间无反馈。

## 页面质量

- 新页面使用 frontmatter 模板；Obsidian 语法遵守 `skills/galaxypedia-wiki/references/obsidian-markdown.md`。
- 页面展示语言默认跟随 raw 来源主语言：英文来源用英文，中文来源用中文；混合来源按主语言，语言均衡时按用户当前提问语言。
- 语言规则适用于 frontmatter `title`、H1、正文、`wiki/index.md` 展示名和简介；文件名仍使用小写 kebab-case，优先保持路径稳定。
- 页面保持聚焦；超过约 300 行时建议拆分。
- 直接引用来源时使用短 blockquote。
- 内部 wiki 关系优先用 wikilink；外部 URL 用 Markdown link；本地图片/PDF 用 `![[...]]` embed。
- 所有事实性总结尽量能追溯到 `## Sources`。
- summary 页回答：“这份来源说了什么、为什么重要、和已有 wiki 的连接是什么。”
- concept/entity 页只写可复用知识，不堆单篇来源的长摘要。

## 上下文纪律

- 先用 `wiki/index.md` 缩小范围，再读 3-5 个最相关的既有页面。
- 需要读更多页面时，说明原因：例如跨领域综合、同名实体消歧、明显冲突。
- 优先做小幅 patch，不为改一个条目重写整页。
- 不能确认的事实标记为待核查，不要靠模型记忆补齐。

## 完成报告

摄入完成后报告：

- 使用的最终 source，例如 `raw/papers/example.mineru.md`。
- 创建的 wiki 页面。
- 更新的 wiki 页面。
- source-index 是否更新。
- manifest 是否更新。
- 是否发现冲突、缺口或需要用户判断的点。

## 禁止事项

- 不修改既有 raw 来源文件。
- 不跳过 `wiki/index.md`。
- 不编辑 `wiki/log.md` 历史记录。
- 不在矛盾时直接覆盖旧观点。
