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
| `raw/papers/_inbox/` | 手动投放的论文 PDF 待处理区；调用 Bridge `stage-papers-inbox`，绝不直接写 wiki。 |
| `raw/papers/` 内 canonical bundle 的 PDF | 只有 manifest 状态为 `linked`/`ingested` 且已有 `paper.mineru.md` 才直接摄入；其余一律走 Bridge。 |
| 非 `raw/papers/` 的 PDF、Office、图片或文件型 URL | 调用 `galaxypedia-mineru-import`，再摄入其 Markdown。 |
| 网页/HTML URL | 调用 `galaxypedia-defuddle`，再摄入 Markdown。 |
| Zotero item key 或 Zotero 附件 | 用 Bridge 的 `stage-zotero-item`，不是旧 SQLite ingest。 |

不要因 Zotero collection 改名或移动而移动 paper bundle；`raw/papers/pdf-<sha-prefix>/` 是稳定路径。不要让非论文资料写入 Zotero。

## Papers Bridge 工作流

`raw/papers/_inbox/` 是手动下载论文的临时投放区；其下可按主题建子目录，但只放待处理的普通 PDF。`raw/papers/pdf-<sha-prefix>/` 才是每篇论文唯一的 hash bundle，包含标题型 PDF、`paper.mineru.md` 和 `paper.mineru/` 资源目录。不要把新 PDF 直接放在 `raw/papers` 根目录，也不要手动创建 `pdf-<hash>` bundle。Bridge 可执行文件由本机 `ZOTERO_GALAXYPEDIA_BRIDGE` 指向；从 Galaxypedia 根目录通过包装器调用：

```bash
python scripts/zotero_ingest.py bridge stage-pdf <external.pdf> --apply
python scripts/zotero_ingest.py bridge stage-legacy-pdf raw/papers/<legacy>.pdf --apply
python scripts/zotero_ingest.py bridge stage-papers-inbox --apply
python scripts/zotero_ingest.py bridge stage-zotero-item <item-key> --apply
python scripts/zotero_ingest.py bridge resume-stage raw/papers/pdf-... --apply
```

`stage-papers-inbox` 递归扫描 `_inbox`，忽略隐藏、非 PDF 与下载临时文件；它只对新 hash stage。已 `linked`/`ingested`、已暂存或需要修复的 hash 只报告而不降级状态、不重跑 MinerU，也不删除 `_inbox` 重复文件。`stage-*` 在复制前登记 `pending_copy`、在 MinerU 前登记 `pending_parse`、成功后登记 `pending_classification`，并输出标题、DOI、年份和真实 collection tree。它绝不创建 Zotero 条目、附件或 collection，也不删除来源。Zotero 条目来源时，条目的 title、DOI、年份和 creators 为 canonical metadata；MinerU 仅作为内容验证、分类和 wiki 证据，wiki 不得修改 Zotero metadata。

对外部或 `_inbox` PDF，若 MinerU 的 DOI/年份未可信核验，不能直接 commit。先调用 Bridge `verify-metadata <bundle> --metadata-file <verified.json> --apply`，以绑定 hash/path 的 Crossref、出版商等来源记录回填题录；该命令不写 Zotero，且不能覆盖 Zotero 来源的 canonical metadata。

随后由 Codex/Claude 根据 title、abstract、DOI、关键词和 MinerU 正文开头生成分类提案。单篇可使用 `outputs/classification-proposal.json`；批量 `_inbox` stage 时，每篇必须写入 `outputs/classification-proposals/<pdf-sha256>.json`，不要写入 `raw/`，且必须包含：

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

Zotero 来源默认在新 relative attachment 验证、旧 attachment 回收后删除旧 linked PDF，使 `raw/papers/pdf-<hash>/` 成为唯一物理 PDF。历史上显式保留源文件的完成 bundle 只能通过 Bridge `cleanup-source <bundle> --apply` 清理；不要手工删除。

如果 PDF 已有有效 `paper.mineru.md` 且 manifest 状态为 `linked`/`ingested`，直接摄入它。若 bundle 是 `pending_copy` 或 `pending_parse`，停止 wiki 写入并在修复来源/MinerU 后调用 Bridge `resume-stage --apply`；不自动重试。若状态为 `pending_classification`、`content_mismatch` 或 `needs_review`，同样停止 wiki 写入并报告该状态。

## Wiki 写入

对最终 Markdown 计算 hash；相同 manifest hash 默认跳过，只有明确 re-ingest 才重做。完整读取正文及相关的 Obsidian 图像嵌入，然后：

1. 创建或更新同语言 summary；只在有复用价值时更新 entity、concept、comparison。
2. 更新 `wiki/index.md`、`wiki/meta/source-index.md`、`wiki/log.md` 和 `raw/.manifest.json`。
3. 保留来源、PDF hash、MinerU 输出、Zotero item/attachment key、分类 action 与 collection path 的 provenance。

不修改 raw 源文件，不覆盖矛盾的既有观点，不写入 token、上传 URL 或签名 URL。批量超过十篇时分批报告进度。
