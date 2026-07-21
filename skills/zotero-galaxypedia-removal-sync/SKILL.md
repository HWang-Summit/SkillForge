---
name: zotero-galaxypedia-removal-sync
description: 当用户明确要求清空 Zotero 回收站并同步删除对应 Galaxypedia/Obsidian 文献资产时使用。先生成死链与共享知识页检查计划，验证后才永久清空回收站。
---

# Zotero–Galaxypedia Removal Sync

只在用户明确要求“清理/永久删除 Zotero 回收站并同步 Obsidian”时使用。它不是后台监听器；普通 ingest、audit、reconcile、Zotero 删除或 collection 调整均不得触发。

使用当前开发 API，且只操作 `X-Zotero-Development-API: 1` 标记的端点。不要写 SQLite 或 storage。令 `ZOTERO_GALAXYPEDIA_BRIDGE` 指向当前 Zotero 项目的 `tools/zotero-galaxypedia-bridge.mjs`，令 `GALAXYPEDIA_ROOT` 指向 vault；SkillForge 不保存本机绝对路径。

每次运行前从主机侧 shell 加载 `${SKILLFORGE_ENV_FILE:-$HOME/.skillforge/env}`。token 不得显示、写入计划或提交到仓库。先按 `zotero-dev-library` probe；受限 runner 的 localhost 错误应在主机侧重试。

## 两阶段操作

先生成只读计划。计划会读取整个 Zotero 回收站，并保存回收站 key 快照、库版本、manifest hash、受影响 bundle、未关联条目及 blocker：

```sh
node "$ZOTERO_GALAXYPEDIA_BRIDGE" plan-trash-removal \
  --vault-root "$GALAXYPEDIA_ROOT" \
  --plan-file "$GALAXYPEDIA_ROOT/outputs/zotero-removal-plan.json"
```

检查 `ready: true`。计划会把 `replaced_attachments` 单列：它们是已被 canonical relative attachment 替代的旧 Zotero 附件，只执行 Zotero 回收站清理，不删除 Obsidian bundle、MinerU 或 summary。若存在 blocker（共享概念/实体/人工页面、summary backlink、DOI/item key/raw source 引用），停止；不要删除段落或绕过检查。

只有用户再次明确确认永久清理，且计划 `ready: true` 时才执行：

```sh
set -a
. "${SKILLFORGE_ENV_FILE:-$HOME/.skillforge/env}"
set +a
node "$ZOTERO_GALAXYPEDIA_BRIDGE" purge-trash-removal \
  --vault-root "$GALAXYPEDIA_ROOT" \
  --plan-file "$GALAXYPEDIA_ROOT/outputs/zotero-removal-plan.json" \
  --apply
```

`purge` 会重新检查 API、回收站版本/key 快照和 manifest hash。若任一变化、死链检查失败、共享知识页受影响或 Obsidian 事务失败，则不永久删除 Zotero 内容。成功时删除论文专属 bundle、MinerU、summary 与索引记录，再永久清空整个 Zotero 回收站；未关联 Obsidian 的回收站条目只在 Zotero 中删除。

不要手工编辑计划 JSON，也不要用 `zotero-cli trash purge` 绕过 Bridge 的 Obsidian 检查。永久删除后的最小台账仅保留 item key、PDF hash、时间和结果。
