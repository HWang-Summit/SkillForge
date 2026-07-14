---
name: zotero-local-pdf-attach
description: 已弃用的 Zotero Desktop storage 附件导入兼容技能。当前 Galaxypedia 开发工作流使用 raw/papers 中唯一 PDF bundle 和 relative linked attachment；仅在用户明确维护历史 Zotero storage 托管附件时使用。
---

# Deprecated: Zotero Local PDF Attach

不要将新的论文 PDF 导入 Zotero storage，也不要用本 skill 为 Galaxypedia 论文新增附件。这样会产生第二份 PDF，破坏 `raw/papers` 是唯一保存位置的约束。

新的附件流程：

1. 用 `galaxypedia-wiki-ingest` 触发 Bridge 的 `stage-pdf`、`stage-legacy-pdf` 或 `stage-zotero-item`。
2. 由 Codex/Claude 生成并审查分类提案。
3. 用 `commit-bundle --apply` 创建 Zotero relative linked attachment；新 collection 还需要用户确认和 `--allow-create-collection`。

此 skill 保留仅为历史托管副本的审计/恢复说明。除非用户明确要求处理既有 Zotero storage 附件，否则停止并改用上述流程。不要编辑 `zotero.sqlite` 或直接改写 storage。
