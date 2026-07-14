---
name: galaxypedia-zotero-ingest
description: 已弃用的 Galaxypedia Zotero SQLite 只读查询兼容技能。仅在需要审计历史 SQLite metadata 或历史索引时使用；新的 Zotero PDF 摄入、解析、分类和写入必须使用 galaxypedia-wiki-ingest 与 Zotero-Galaxypedia Bridge。
---

# Deprecated: Galaxypedia Zotero Ingest

不要将此 skill 用于新的论文摄入、PDF 解析、Zotero 写入或 collection 分类。当前开发版的本地 API 加 Bridge 已替代其 SQLite/local-storage 工作流。

仅在用户明确要求核对历史 SQLite 元数据、旧的 `wiki/meta/zotero-index.md`，或排查旧摄入记录时运行只读命令：

```bash
python scripts/zotero_ingest.py list-collections
python scripts/zotero_ingest.py find --query "<query>"
python scripts/zotero_ingest.py export --item-key <item-key>
python scripts/zotero_ingest.py refresh-index
```

不要修改 `zotero.sqlite`、Zotero storage、PDF 路径或 collection。新流程的入口是 `galaxypedia-wiki-ingest`：它使用 `stage-*`、AI 分类提案与 `commit-bundle`，并以 `raw/papers/pdf-<sha-prefix>/` 作为唯一 PDF bundle。
