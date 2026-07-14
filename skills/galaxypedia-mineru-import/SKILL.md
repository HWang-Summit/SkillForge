---
name: galaxypedia-mineru-import
description: 使用 MinerU 解析 Galaxypedia 中非论文 Bridge 管理的 PDF、Office、图片或文件型 URL，保存为 raw Markdown 与资源目录。raw/papers 的论文 PDF 必须改由 galaxypedia-wiki-ingest 路由到 Zotero-Galaxypedia Bridge。
---

# Galaxypedia MinerU Import

此 skill 只是文件解析预处理器，不创建 wiki 页面，也不写 Zotero。

## 允许的输入

- `raw/articles/`、`raw/books/`、`raw/notes/` 或其他非 `raw/papers/` 的 PDF、Office、图片和文件型 URL：使用 MinerU。
- 已有 Markdown：不要再次解析。
- 网页/HTML：使用 `galaxypedia-defuddle`，不是 MinerU。

任何 `raw/papers/` PDF、外部论文 PDF、Zotero 条目或 Zotero PDF 附件都不要直接运行本 skill。交给 `galaxypedia-wiki-ingest`：它会先走 Bridge，保证 canonical bundle、MinerU 结果、Zotero 条目和 relative linked attachment 一致。已有 `raw/papers/pdf-*/paper.mineru.md` 时也必须复用，禁止二次 MinerU。

## 执行

在 Galaxypedia 根目录使用项目级脚本：

```bash
conda run -n galaxypedia python scripts/mineru_parse.py <file-or-url> --category articles --mode auto
conda run -n galaxypedia python scripts/mineru_parse.py <file-or-url> --out raw/notes/example.mineru.md --mode auto
```

输出必须位于 `raw/`。脚本保存同名资源目录，并把图片引用转换为 Obsidian 嵌入。完成后把生成的 Markdown 交回 `galaxypedia-wiki-ingest`。

不修改 `wiki/`，不删除原始来源或解析结果，不记录 token、上传 URL 或请求体。`--mode auto` 优先；私密或受监管文件上传 MinerU 前先取得用户确认。
