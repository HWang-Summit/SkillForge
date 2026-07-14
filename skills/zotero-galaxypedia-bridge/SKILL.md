---
name: zotero-galaxypedia-bridge
description: 将论文 PDF 安全转换为 Galaxypedia canonical bundle，并通过运行中的 Zotero 开发版本地 API 建立相对链接附件。用于外部或 Zotero PDF 摄入、MinerU 解析、AI collection 分类提案、附件迁移、重试、对账和审计。
---

# Zotero–Galaxypedia Bridge

只用于带 `X-Zotero-Development-API: 1` 标记的开发版 API。需要时先用 `zotero-dev-library` 探测端点。设置 `ZOTERO_GALAXYPEDIA_BRIDGE` 为开发版 Zotero 项目中的 `tools/zotero-galaxypedia-bridge.mjs`，并设置 `GALAXYPEDIA_ROOT`；不要把本机绝对路径写入 SkillForge。

不要直接改 Zotero SQLite/storage、创建 stored attachment 或用旧的单阶段 `ingest-*` 命令处理新的论文流程。PDF 的唯一事实源是：

```text
raw/papers/pdf-<sha-prefix>/
  <year> - <title>.pdf
  paper.mineru.md
  paper.mineru/
```

collection 改名或移动不应移动 bundle。

## 两阶段流程

### 1. Stage

先执行对应 `stage-* --apply`。它会创建/复用 bundle、运行或复用 MinerU，并登记 `pending_classification`；不会创建 Zotero 条目、collection 或附件，也不会删除来源。

```sh
node "$ZOTERO_GALAXYPEDIA_BRIDGE" stage-pdf <external.pdf> \
  --vault-root "$GALAXYPEDIA_ROOT" --apply
node "$ZOTERO_GALAXYPEDIA_BRIDGE" stage-legacy-pdf raw/papers/<legacy>.pdf \
  --vault-root "$GALAXYPEDIA_ROOT" --apply
node "$ZOTERO_GALAXYPEDIA_BRIDGE" stage-zotero-item <item-key> \
  --vault-root "$GALAXYPEDIA_ROOT" --apply
```

读取输出的 hash、bundle、metadata、MinerU Markdown 和真实 collection tree。根据 title、abstract、DOI、关键词及正文开头生成 `outputs/classification-proposal.json`。优先已有二级 collection；低置信度或多个合理候选写 `needs_review`，不得 commit。

### 2. Commit

提案必须精确匹配 `version`、`pdf_sha256` 和 bundle。对已有 collection，用户已明确要求摄入时可执行：

```sh
node "$ZOTERO_GALAXYPEDIA_BRIDGE" commit-bundle raw/papers/pdf-... \
  --vault-root "$GALAXYPEDIA_ROOT" \
  --classification-file outputs/classification-proposal.json --apply
```

只有用户明确确认创建一级或二级 collection 时，才额外传入 `--allow-create-collection`。commit 会验证 proposal 和 collection tree，创建/复用条目、仅追加 collection、创建并读回验证 relative linked attachment；成功后才回收旧附件或来源。

commit 成功后，把 `paper.mineru.md` 交给 `galaxypedia-wiki-ingest`，不要再次调用 MinerU。

## Recovery and audit

`pending_parse` 可在修复 MinerU 后重试；`content_mismatch` 与 `needs_review` 必须人工决定，绝不强行链接。使用：

```sh
node "$ZOTERO_GALAXYPEDIA_BRIDGE" reconcile --vault-root "$GALAXYPEDIA_ROOT"
node "$ZOTERO_GALAXYPEDIA_BRIDGE" audit --vault-root "$GALAXYPEDIA_ROOT"
```

审计与对账为只读。不得删除 bundle、附件或来源来“修复”问题；先报告 hash、item key、attachment key 与状态。
