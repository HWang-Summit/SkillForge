---
name: galaxypedia-wiki-ingest
description: 摄入 Galaxypedia 的 raw Markdown、论文 PDF、Office、图片或 URL，并维护 wiki 页面、manifest、source-index 与日志。论文 PDF 位于 raw/papers 时必须经 Zotero-Galaxypedia Bridge 的解析、分类提案和确认写入流程；其他文件型来源使用 MinerU。
---

# Galaxypedia Wiki Ingest

将此 skill 作为 `/ingest` 的统一入口。先读 `SCHEMA.md`、`galaxypedia-wiki`、frontmatter/template 参考和 `wiki/index.md`。

## 先分流，不要猜测

| 输入 | 处理 |
| --- | --- |
| `raw/**/*.md`（包括 `raw/papers/*/paper.mineru.md`） | 直接按本 skill 摄入。 |
| `raw/papers/` 内的 PDF | 只有 manifest 状态为 `linked`/`ingested` 且已有 `paper.mineru.md` 才直接摄入；其余一律走 Bridge。 |
| 非 `raw/papers/` 的 PDF、Office、图片或文件型 URL | 调用 `galaxypedia-mineru-import`，再摄入其 Markdown。 |
| 网页/HTML URL | 调用 `galaxypedia-defuddle`，再摄入 Markdown。 |
| Zotero item key 或 Zotero 附件 | 用 Bridge 的 `stage-zotero-item`，不是旧 SQLite ingest。 |

不要因 Zotero collection 改名或移动而移动 paper bundle；`raw/papers/pdf-<sha-prefix>/` 是稳定路径。不要让非论文资料写入 Zotero。

## Papers Bridge 工作流

`raw/papers` 的每篇论文只保留一个 hash bundle：标题型 PDF、`paper.mineru.md` 和 `paper.mineru/` 资源目录。Bridge 可执行文件由本机 `ZOTERO_GALAXYPEDIA_BRIDGE` 指向；从 Galaxypedia 根目录通过包装器调用：

```bash
python scripts/zotero_ingest.py bridge stage-pdf <external.pdf> --apply
python scripts/zotero_ingest.py bridge stage-legacy-pdf raw/papers/<legacy>.pdf --apply
python scripts/zotero_ingest.py bridge stage-zotero-item <item-key> --apply
```

`stage-*` 只复制/复用 bundle、运行或复用 MinerU、登记 `pending_classification`，并输出标题、DOI、年份和真实 collection tree。它绝不创建 Zotero 条目、附件或 collection，也不删除来源。

随后由 Codex/Claude 根据 title、abstract、DOI、关键词和 MinerU 正文开头生成 `classification-proposal.json`。提案存到项目 `outputs/`，不要写入 `raw/`，且必须包含：

```json
{
  "version": 1,
  "pdf_sha256": "stage 输出的 hash",
  "bundle": "raw/papers/pdf-...",
  "classification": {
    "action": "existing_secondary",
    "collection_key": "候选二级 collection key",
    "confidence": 0.0,
    "rationale": "依据",
    "alternatives": []
  }
}
```

分类优先级是现有二级 collection、现有一级 collection、建议新二级、建议新一级、`needs_review`。低置信度或存在多个同等候选时使用 `needs_review`，不要写 collection。已存在条目只追加确认的 collection，绝不删除既有 collection。

用户明确确认新 collection 后，才允许创建：

```bash
python scripts/zotero_ingest.py bridge commit-bundle raw/papers/pdf-... \
  --classification-file outputs/classification-proposal.json \
  --apply --allow-create-collection
```

没有 `--allow-create-collection` 时，Bridge 会拒绝创建一级或二级 collection。`commit-bundle` 会校验 bundle/hash/collection tree，创建或复用 Zotero 条目，追加 collection，创建 relative linked PDF attachment，读回验证；成功后才回收旧附件或来源。完成后立即摄入 bundle 的 `paper.mineru.md`，不再调用 MinerU。

如果 PDF 已有有效 `paper.mineru.md` 且 manifest 状态为 `linked`/`ingested`，直接摄入它。若 bundle 是 `pending_parse`、`pending_classification`、`content_mismatch` 或 `needs_review`，停止 wiki 写入并报告该状态。

## Wiki 写入

对最终 Markdown 计算 hash；相同 manifest hash 默认跳过，只有明确 re-ingest 才重做。完整读取正文及相关的 Obsidian 图像嵌入，然后：

1. 创建或更新同语言 summary；只在有复用价值时更新 entity、concept、comparison。
2. 更新 `wiki/index.md`、`wiki/meta/source-index.md`、`wiki/log.md` 和 `raw/.manifest.json`。
3. 保留来源、PDF hash、MinerU 输出、Zotero item/attachment key、分类 action 与 collection path 的 provenance。

不修改 raw 源文件，不覆盖矛盾的既有观点，不写入 token、上传 URL 或签名 URL。批量超过十篇时分批报告进度。
