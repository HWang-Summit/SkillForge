---
name: zotero-galaxypedia-bridge
description: 将论文 PDF 安全转换为 Galaxypedia canonical bundle，并通过运行中的 Zotero 开发版本地 API 建立相对链接附件。用于外部或 Zotero PDF 摄入、MinerU 解析、AI collection 分类提案、附件迁移、重试、对账和审计。
---

# Zotero–Galaxypedia Bridge

只用于带 `X-Zotero-Development-API: 1` 标记的当前指定 Zotero 构建。每次 `stage-*`、`commit-bundle` 或可能读取 API 的恢复操作前，先按 `zotero-dev-library` 从可访问本机 `127.0.0.1` 的主机执行环境 probe 端点。受限 runner 的 `fetch failed`/`EPERM` 必须在主机侧重试，不能误判为 API 停机；probe 未成功或缺少标记时停止，不向未验证端点写入。设置 `ZOTERO_GALAXYPEDIA_BRIDGE` 为当前 Zotero 项目中的 `tools/zotero-galaxypedia-bridge.mjs`，并设置 `GALAXYPEDIA_ROOT`；不要把本机绝对路径写入 SkillForge。

写入前由主机侧 shell 从 `${SKILLFORGE_ENV_FILE:-$HOME/.skillforge/env}` 加载 `ZOTERO_LOCAL_API_TOKEN`，不要只依赖交互式 `~/.zshrc`，也绝不输出 token。

不要直接改 Zotero SQLite/storage、创建 stored attachment 或用旧的单阶段 `ingest-*` 命令处理新的论文流程。PDF 的唯一事实源是：

```text
raw/papers/pdf-<sha-prefix>/
  <year> - <title>.pdf
  paper.mineru.md
  paper.mineru/
```

collection 改名或移动不应移动 bundle。

## Manual papers inbox

手动下载的论文放入 `raw/papers/_inbox/`（可递归分目录），而不是 `raw/papers` 根目录或手工创建的 `pdf-<hash>` 目录。它是临时输入区，不是 canonical source。按需扫描，不使用后台监听：

```sh
node "$ZOTERO_GALAXYPEDIA_BRIDGE" stage-papers-inbox \
  --vault-root "$GALAXYPEDIA_ROOT" --apply
```

扫描只处理普通 PDF，忽略隐藏、非 PDF、`.part`、`.partial` 与 `.crdownload` 文件，并拒绝符号链接。新 hash 使用 `stage-legacy-pdf` 的同一安全路径；已 `linked`/`ingested`、已暂存或待修复的 hash 仅报告，绝不重新解析、降级 manifest 状态或删除 `_inbox` 重复文件。对新 stage，`_inbox` PDF 会在 commit 成功创建并读回 relative linked attachment 后才删除；失败、待分类或重复文件保留。

## 两阶段流程

### 1. Stage

先执行对应 `stage-* --apply`。开始复制前 Bridge 先登记 `pending_copy`，开始 MinerU 前登记 `pending_parse`；成功后才登记 `pending_classification`。它不会创建 Zotero 条目、collection 或附件，也不会删除来源。可用 `--mineru-timeout <seconds>`（默认 600）和 `--mineru-interval <seconds>`（默认 5）调整 MinerU 调用；解析过程的标准输出/错误直接保留在终端，便于诊断。

```sh
node "$ZOTERO_GALAXYPEDIA_BRIDGE" stage-pdf <external.pdf> \
  --vault-root "$GALAXYPEDIA_ROOT" --apply
node "$ZOTERO_GALAXYPEDIA_BRIDGE" stage-legacy-pdf raw/papers/<legacy>.pdf \
  --vault-root "$GALAXYPEDIA_ROOT" --apply
node "$ZOTERO_GALAXYPEDIA_BRIDGE" stage-papers-inbox \
  --vault-root "$GALAXYPEDIA_ROOT" --apply
node "$ZOTERO_GALAXYPEDIA_BRIDGE" stage-zotero-item <item-key> \
  --vault-root "$GALAXYPEDIA_ROOT" --apply
```

对 `stage-zotero-item`，Zotero 中已有条目的 title、DOI、年份和 creators 是 canonical metadata；MinerU 的 title/DOI/年份、摘要和关键词单独保存为内容验证与分类证据，绝不自动回写或覆盖 Zotero metadata。若 title 或 DOI 矛盾，状态为 `content_mismatch`，不请求分类 tree、不能 commit。

对外部或 `_inbox` PDF，MinerU 题录只是候选，不能把正文或参考文献中的年份/DOI当作最终 metadata。先用 Crossref、出版商等可追溯来源写出绑定 hash/path 的 JSON，再显式回填；该操作不写 Zotero：

```sh
node "$ZOTERO_GALAXYPEDIA_BRIDGE" verify-metadata raw/papers/pdf-... \
  --vault-root "$GALAXYPEDIA_ROOT" --metadata-file outputs/verified-metadata.json --apply
```

JSON 必须有 `version: 1`、`pdf_sha256`、`bundle`、`metadata.title/doi/year`，以及 `verification.source`（可附 `source_url`、`rationale`）。Bridge 仅接受 `pending_classification` 的非 Zotero bundle；title 必须仍与 MinerU PDF title 一致，Zotero canonical metadata 不允许此命令覆盖。

读取输出的 hash、bundle、metadata、MinerU Markdown 和真实 collection tree。根据 title、abstract、DOI、关键词及正文开头生成分类提案。批量 `_inbox` stage 时按 `outputs/classification-proposals/<pdf-sha256>.json` 一篇一份；单篇可使用 `outputs/classification-proposal.json`。优先已有二级 collection；低置信度或多个合理候选写 `needs_review`，不得 commit。

### 2. Commit

提案必须精确匹配 `version`、`pdf_sha256` 和 bundle。对已有 collection，用户已明确要求摄入时可执行：

```sh
node "$ZOTERO_GALAXYPEDIA_BRIDGE" commit-bundle raw/papers/pdf-... \
  --vault-root "$GALAXYPEDIA_ROOT" \
  --classification-file outputs/classification-proposal.json --apply
```

只有用户明确确认创建一级或二级 collection 时，才额外传入 `--allow-create-collection`。commit 会验证 proposal 和 collection tree，创建/复用条目、仅追加 collection、创建并读回验证 relative linked attachment；成功后才回收旧附件或来源。默认 Zotero 附件迁移会在新 attachment 验证、旧 attachment 回收后删除 hash 一致的旧 linked PDF，使 canonical bundle 成为唯一物理 PDF；显式 `--keep-source` 才保留来源。历史保留源文件的 bundle 可显式收敛：

```sh
node "$ZOTERO_GALAXYPEDIA_BRIDGE" cleanup-source raw/papers/pdf-... \
  --vault-root "$GALAXYPEDIA_ROOT" --apply
```

commit 成功后，把 `paper.mineru.md` 交给 `galaxypedia-wiki-ingest`，不要再次调用 MinerU。

## Recovery and audit

`pending_copy` 或 `pending_parse` 在修复来源或 MinerU 后只能显式恢复，不进行自动云端重试；恢复只复制/解析，不创建或修改 Zotero：

```sh
node "$ZOTERO_GALAXYPEDIA_BRIDGE" resume-stage raw/papers/pdf-... \
  --vault-root "$GALAXYPEDIA_ROOT" --apply
```

`content_mismatch` 与 `needs_review` 必须人工决定，绝不强行链接。使用：

```sh
node "$ZOTERO_GALAXYPEDIA_BRIDGE" reconcile --vault-root "$GALAXYPEDIA_ROOT"
node "$ZOTERO_GALAXYPEDIA_BRIDGE" audit --vault-root "$GALAXYPEDIA_ROOT"
```

审计与对账为只读。不得删除 bundle、附件或来源来“修复”问题；先报告 hash、item key、attachment key 与状态。
