---
name: galaxypedia-notion-literature-notes
description: 将 Galaxypedia/Obsidian 中已摄入的论文、summary、concept/entity 页面整理为 Notion 文献阅读笔记，并维护 Notion 侧“文献阅读笔记 -> 分类 -> 单篇笔记”的阅读层。
---

# Galaxypedia Notion Literature Notes

使用这个 skill 处理以下任务：

- 把 Galaxypedia 已摄入论文写成 Notion 文献阅读笔记。
- 将 Obsidian/Galaxypedia 的论文 summary、concept/entity 页面同步为 Notion 阅读层。
- 在 Notion 的 `海流色太的云` 下维护 `文献阅读笔记 -> 分类 -> 单篇笔记` 结构。
- 给 Notion 笔记补充原文 PDF、本地 raw、MinerU Markdown 或 Zotero 附件入口。

## 核心定位

- Galaxypedia 的 `raw/` 和 `wiki/` 是长期事实源。
- Notion 是阅读、研究范式沉淀和跨主题浏览层，不替代 `raw/.manifest.json`、`wiki/index.md` 或 `wiki/meta/source-index.md`。
- 默认不把 Notion 反向写入 wiki；只有用户明确要求“双向链接/记录 Notion URL”时，才更新对应 wiki 页面和 `wiki/log.md`。
- 不复制、移动或修改既有 `raw/` 文件。

## 入口检查

1. 先读 `SCHEMA.md` 和 `skills/galaxypedia-wiki/SKILL.md`。
2. 根据来源类型读取相关 skill：
   - 未摄入 PDF/Office/图片：先读 `skills/galaxypedia-mineru-import/SKILL.md`，生成稳定 `raw/.../*.mineru.md` 后再继续。
   - Zotero 来源：先读 `skills/galaxypedia-zotero-ingest/SKILL.md`，确认 item、attachment、PDF path 和 raw path。
   - 已摄入来源：读 `wiki/index.md`，再读对应 summary 和 3-5 个最相关 concept/entity/comparison 页面。
3. 如果任务涉及维护项目规则或 skill，本 skill 之外还要读 `skills/galaxypedia-karpathy-guidelines/SKILL.md`。
4. 如果 Notion MCP 可用，先搜索并读取目标父页面；如果不可用，输出可粘贴的 Notion-flavored Markdown。

## Notion 结构

默认根页面：

```text
海流色太的云
└── 文献阅读笔记
    ├── 生物医学机器学习
    ├── 射电天文成像
    ├── 科学机器学习
    └── 其他分类
```

规则：

- 如果 `文献阅读笔记` 不存在，在 `海流色太的云` 下创建。
- 如果领域分类不存在，在 `文献阅读笔记` 下创建。
- 单篇阅读笔记放在最具体的领域分类下。
- 不默认创建 Notion database。用户明确要求规模化管理、筛选、状态或标签时，再讨论 database schema。
- 如果历史笔记直接挂在根页面下，可以移动到新的分类页；移动前先确认它确实是文献阅读笔记。

## 单篇笔记模板

Notion 单篇阅读笔记使用中文为主，除非用户明确要求英文。标题优先使用用户给定标题；否则使用“主题/论文简称 + 研究范式/阅读笔记”。

```markdown
# 原文入口

- 原文 PDF（本机）：[打开本地 PDF](file:///absolute/path/to/paper.pdf)
- 本机 PDF 路径：`/absolute/path/to/paper.pdf`
- Galaxypedia MinerU Markdown：`raw/papers/example.mineru.md`
- Zotero：item `ITEMKEY`，attachment `ATTACHMENTKEY`
- 如果 Notion 网页端不能打开 `file://` 链接，在本机终端运行：`open /absolute/path/to/paper.pdf`

---

# 文献信息

- 论文：
- 作者：
- 年份/会议/期刊：
- 方法名：
- 本地来源：

# 一句话结论

# 研究问题的重新定义

# 研究范式

## 1. ...

# 方法管线

# 实验设计

# 案例/证据

# 可迁移的方法论

# 风险与追问

# 我的阅读标记
```

可以按论文特点调整小节名，但必须保留：

- `# 原文入口`
- `# 文献信息`
- `# 一句话结论`
- `# 研究范式`
- `# 风险与追问`

## PDF 与来源入口

默认策略是不上传 PDF 到 Notion，而是在笔记顶部保留可追溯入口：

- `file://` 本地 PDF 链接。
- PDF 绝对路径。
- Galaxypedia raw 或 MinerU Markdown 路径。
- 本机 `open ...pdf` 命令。
- 如果 manifest/source-index 有 Zotero provenance，记录 item key、attachment key、source PDF path。

原因：

- Notion 网页端对 `file://` 支持不稳定，但本机路径和 `open` 命令可兜底。
- 当前工具链不能稳定直接上传本地二进制 PDF。
- 保持 `raw/` 作为事实源，避免 Notion 形成第二份不受控 PDF 副本。

如果用户明确要求 PDF 附件：

1. 先说明当前自动上传本地二进制 PDF 的限制。
2. 如果有公开直链或签名 URL，可用 Notion attachment 工具导入。
3. 如果只有本地 PDF，建议用户在 Notion UI 手动上传，或后续单独实现 Notion File Upload API 脚本。

## Obsidian/Galaxypedia 到 Notion 的转换规则

优先从 wiki 结构化页面生成 Notion 笔记，而不是重新读整篇 PDF：

1. 从 `wiki/index.md` 定位 summary。
2. 阅读 summary 的 `Key Claims`、`Notes`、`Sources`、`See also`。
3. 阅读相关 concept/entity 页面，提取可迁移范式和术语定义。
4. 必要时回到 `raw/...*.mineru.md` 核对图、表、实验设置或原文措辞。
5. 对事实性结论保留本地来源路径，不编造 DOI、URL 或代码仓库。

Notion 笔记写作重点：

- 不要只是摘要；要突出“研究问题如何被重新定义”。
- 方法描述压缩为管线，不复制公式和长表。
- 实验设计聚焦数据集、任务设置、baseline、泛化测试和关键消融。
- 风险与追问要明确区分“论文已证明”和“仍需验证”。
- 可迁移方法论要抽象到其他研究方向可复用的层级。

## 双向链接可选流程

只有用户明确要求时执行：

1. 在对应 wiki summary 增加 `## External notes`。
2. 添加 Notion 页面 URL 和创建日期。
3. 更新该 summary frontmatter `updated`。
4. 追加 `wiki/log.md`，说明新增 Notion 外部阅读笔记链接。
5. 不更新 `raw/.manifest.json`，因为 Notion 笔记不是 raw source。

## Codex 与 Claude Code 兼容

- 本 skill 不依赖 Codex 专属工具名。
- Codex 或 Claude Code 有 Notion MCP 时，按 Notion 工具创建/移动/更新页面。
- 没有 Notion MCP 时，输出完整 Notion-flavored Markdown 和目标层级，让用户手动粘贴。
- Notion-flavored Markdown 要尽量使用普通标题、列表、分割线和 inline code，避免依赖复杂 block。
- 如果工具要求读取 Notion Markdown 规范，先读取对应规范资源，再创建或更新页面。

## 完成报告

完成后报告：

- Notion 页面层级。
- 创建或移动的 Notion 页面 URL。
- PDF 入口采用了哪些形式。
- 是否更新了 Galaxypedia wiki 反向链接。
- 是否有无法自动完成的限制，例如本地 PDF 不能自动上传为 Notion 附件。

## 禁止事项

- 不绕过 `raw -> ingest -> wiki -> Notion note` 的边界。
- 不把未摄入论文直接写成长期 Notion 笔记，除非用户明确要求临时笔记。
- 不把 Notion 页面当作 source-index 或 manifest 的替代。
- 不默认上传、复制或移动 PDF。
- 不静默删除或重排用户已有 Notion 页面；移动页面前必须确认目标页面确实属于文献阅读结构。
