---
name: zotero-galaxypedia-bridge
description: 将论文 PDF 安全转换为 Galaxypedia canonical bundle，并通过运行中的官方 Zotero + Galaxypedia 插件本地 API 建立相对链接附件。用于外部或 Zotero PDF 摄入、MinerU 解析、AI collection 分类提案、附件迁移、重试、对账和审计。
---

# Zotero–Galaxypedia Bridge

Bridge 只摄入用户指定的论文文件、条目或明确批次，不自动镜像整个 Zotero 文库。inbox 单文件
用单文件 stage，不扩展为目录扫描写入。Bundle 建立和 `linked` 只证明桥接进度，wiki 摄入完成
须核验知识页及来源记录。全库只读审计保留，但不触发摄入、写入知识索引或刷新历史 zotero-index。
所有带 `--apply` 的写操作先省略该参数生成计划，展示影响并得到明确确认后执行。

只用于带 `X-Zotero-Galaxypedia-API: 1` 标记且 capability probe 通过的官方 Zotero + Galaxypedia 插件。每次 `stage-*`、`commit-bundle` 或可能读取 API 的恢复操作前，先按 `zotero-dev-library` 从可访问本机 `127.0.0.1` 的主机执行环境 probe `/api/galaxypedia/v1/capabilities`。受限 runner 的 `fetch failed`/`EPERM` 必须在主机侧重试，不能误判为 API 停机；probe 未成功或缺少插件标记、capability 不完整或版本不兼容时停止，不向未验证端点写入。设置 `ZOTERO_GALAXYPEDIA_BRIDGE` 为当前 Zotero 项目中的 `tools/zotero-galaxypedia-bridge.mjs`，并设置 `GALAXYPEDIA_ROOT`；不要把本机绝对路径写入 SkillForge。

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
# 单文件测试或单篇处理
node "$ZOTERO_GALAXYPEDIA_BRIDGE" stage-papers-inbox \
  --source raw/papers/_inbox/example.pdf \
  --vault-root "$GALAXYPEDIA_ROOT" --apply
```

`--source` 只处理指定的 vault-relative inbox PDF；省略它才扫描明确指定的整个 inbox 批次。扫描只处理普通 PDF，忽略隐藏、非 PDF、`.part`、`.partial` 与 `.crdownload` 文件，并拒绝符号链接。新 hash 使用 `stage-legacy-pdf` 的同一安全路径；已 `linked`/`ingested`、已暂存或待修复的 hash 仅报告，绝不重新解析、降级 manifest 状态或删除 `_inbox` 重复文件。对新 stage，`_inbox` PDF 会在 commit 成功创建并读回 relative linked attachment 后才删除；失败、待分类或重复文件保留。

## 两阶段流程

### 1. Stage

先预览对应 `stage-*`，确认后执行 `stage-* --apply`。开始复制前 Bridge 先登记 `pending_copy`，开始 MinerU 前登记 `pending_parse`；成功后才登记 `pending_classification`。它不会创建 Zotero 条目、collection 或附件，也不会删除来源。可用 `--mineru-timeout <seconds>`（默认 600）和 `--mineru-interval <seconds>`（默认 5）调整 MinerU 调用；解析过程的标准输出/错误直接保留在终端，便于诊断。

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

提案必须精确匹配 `version`、`pdf_sha256` 和 bundle。对已有 collection，展示 commit 计划并取得明确确认后可执行：

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

## 全库 PDF 内容身份巡检与确认修复

当用户要求检查 Zotero 条目 title、附件显示 title 与 PDF 实际内容是否一致时，使用当前
Zotero 项目的 Bridge；不得只按文件名判断，也不得直接在 Zotero UI 或 SQLite 中批量修改。

先 probe Galaxypedia 插件 API，再生成只读报告。它扫描所有可本地读取的未删除 PDF attachment，比较
父条目 title/DOI、附件显示 title、PDF SHA-256 和已有 Bridge/MinerU 证据：

```sh
node "$ZOTERO_GALAXYPEDIA_BRIDGE" audit-content-identity \
  --vault-root "$GALAXYPEDIA_ROOT" \
  --report "$GALAXYPEDIA_ROOT/outputs/zotero-content-audit.json"
```

默认不运行 MinerU；`needs_parse` 仅表示尚无内容证据。只有用户明确要求解析缺失内容时才加入
`--parse-missing`。该模式会在 `outputs/zotero-content-audits/` 以 PDF hash 缓存 MinerU
证据，但不创建 bundle、不改 manifest、不写 Zotero。

报告后必须让用户逐项决定，再写 `version: 1`、`decisions` 数组的 JSON。每一项必须绑定
`parent_item_key`、`attachment_key`、`pdf_sha256`，并且只能选择：

- `rename_attachment_title` + `target_title`：仅当父条目 metadata 已和 PDF 内容证据一致时。
- `update_parent_metadata` + `metadata.title`（可选 `metadata.doi`）和可追溯
  `verification.source`（可选 HTTP(S) `source_url`）：目标值必须与 PDF 内容证据一致，
  不能仅依据 MinerU 自动产生或采纳。
- `acknowledge_exception` + 人工 `rationale`：记录确认保留的不一致，不写 Zotero。

生成计划后，展示精确对象与变更，再取得第二次明确确认，才可执行：

```sh
node "$ZOTERO_GALAXYPEDIA_BRIDGE" plan-content-identity-repair \
  --vault-root "$GALAXYPEDIA_ROOT" \
  --audit "$GALAXYPEDIA_ROOT/outputs/zotero-content-audit.json" \
  --decisions "$GALAXYPEDIA_ROOT/outputs/zotero-content-decisions.json" \
  --identity-plan "$GALAXYPEDIA_ROOT/outputs/zotero-content-repair-plan.json"

node "$ZOTERO_GALAXYPEDIA_BRIDGE" apply-content-identity-repair \
  --vault-root "$GALAXYPEDIA_ROOT" \
  --identity-plan "$GALAXYPEDIA_ROOT/outputs/zotero-content-repair-plan.json" --apply
```

执行会重新验证 audit hash、计划完整性、PDF hash、item/attachment version/ETag，并在 PATCH
后读回。出现任何变化立即停止；不移动或重命名 PDF 实体，不改 collection，不创建/删除附件，
不清空回收站。例外台账会在条目/附件版本或 PDF hash 改变时自动失效。

## Zotero 回收站清理

用户明确要求永久清空 Zotero 回收站并同步清理 Obsidian 时，改用 `zotero-galaxypedia-removal-sync`。它调用本 Bridge 的 `plan-trash-removal` 与 `purge-trash-removal`，对整个回收站使用版本化快照，检查 summary backlink、共享页面、manifest 与 source-index；存在 blocker 时绝不清空。
