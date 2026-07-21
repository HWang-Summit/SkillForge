---
name: zotero-dev-library
description: 通过本地开发 API 与 CLI 安全读取和管理正在运行的 Zotero 开发版。用于条目、collection、metadata、标签、成员关系、回收站和既有相对链接附件的查询或修改；拒绝未带开发版标记的端点。
---

# Zotero Development Library

仅操作运行中的、带本地读写 API 的当前指定 Zotero 构建；它可以在调通后作为日常使用版本。绝不直接修改 `zotero.sqlite` 或 storage。

## 连接与边界

1. 在每次读写前，从可访问本机 `127.0.0.1` 的主机执行环境运行 `scripts/probe-dev-api.mjs`；它读取 `ZOTERO_LOCAL_API_URL`，默认本机 `/api` 端点。
2. 若受限 runner 报 `fetch failed`、`EPERM` 或 localhost 被禁止，先在主机执行环境重试完全相同的只读 probe；这不是 API 停机的证据。主机侧 probe 仍失败时才报告当前 Zotero 构建未运行、端口未监听或 API 未启用。
3. probe 必须确认 `X-Zotero-Development-API: 1`。缺少该标记或 probe 未成功时立即停止，不向未验证的端点写入。
4. 写入仅从执行环境读取 `ZOTERO_LOCAL_API_TOKEN`。优先在本机私密 `${SKILLFORGE_ENV_FILE:-$HOME/.skillforge/env}` 中保存并由执行 shell 加载（权限应为仅所有者可读）；不要仅依赖交互式 `~/.zshrc`，也不打印、记录或要求用户贴 token。
5. 设置 `ZOTERO_PROJECT_ROOT` 为当前 Zotero 项目根目录，再使用其 `tools/zotero-cli.mjs`。SkillForge 不保存该机器路径。

```sh
node <skill-dir>/scripts/probe-dev-api.mjs
node "$ZOTERO_PROJECT_ROOT/tools/zotero-cli.mjs" item get <item-key>
node "$ZOTERO_PROJECT_ROOT/tools/zotero-cli.mjs" collection get <collection-key>
```

在需要 token 的主机侧命令前，加载私密环境文件，但绝不回显变量：

```sh
set -a
. "${SKILLFORGE_ENV_FILE:-$HOME/.skillforge/env}"
set +a
node <skill-dir>/scripts/probe-dev-api.mjs
```

若当前 Zotero 构建未运行，启动该构建后重新 probe；开始 stage、commit 或任何 CLI 写入前，必须成功通过该检查。

## 读写规则

- 读取时报告 key、标题/collection 名、library 和匹配数量。
- 创建单一条目或 collection 前说明将创建的对象；更新、删除、恢复、标签、成员关系、批量操作或 `--force` 前，先展示精确对象与命令并获得明确确认。
- CLI 已处理 Token 与乐观并发头；不要改用裸 API 写请求。
- 每次成功写入后读回对象；遇到 version/ETag 冲突时停止、重新读取，不默认强制覆盖。

支持 item/collection metadata、creators、tags、notes、relations、collection membership、trash/restore 以及已有相对链接 PDF 附件。不承诺 stored-file 上传、任意文件系统操作、PDF 标注或全文索引写入。

## 回收站

`zotero-cli trash list` 读取当前开发 API 的完整回收站快照。`zotero-cli trash purge --plan <file>` 是永久删除：它只接受由 Bridge 生成、包含库版本与完整 key 快照的计划，若回收站发生变化即拒绝。

涉及 Galaxypedia/Obsidian 的文献时，不要直接调用 `trash purge`；改用 `zotero-galaxypedia-removal-sync`。该 skill 会先检查 summary backlink、共享知识页、manifest 和 source-index，再决定是否可永久清空。普通条目整理也不能隐式清空回收站。

迁移或新建 relative linked attachment 不隐式更新父条目现有 metadata（包括 title、DOI、日期和 creators）；任何 metadata 更新都必须作为单独、经明确授权的 CLI 操作，并在写后读回验证。

## Relative linked PDF

先确认父条目、相对路径以及 Zotero 的 Linked Attachment Base Directory。链接文件必须已存在且为相对 `.pdf` 路径：

```sh
node "$ZOTERO_PROJECT_ROOT/tools/zotero-cli.mjs" attachment list <parent-item-key>
node "$ZOTERO_PROJECT_ROOT/tools/zotero-cli.mjs" attachment link <parent-item-key> \
  --relative-path 'pdf-a1b2c3d4e5f6a7b8/paper.pdf'
```

读回新附件验证。删除附件是高风险写入：它只会将 Zotero 附件移入回收站，不应假设会删除 linked PDF。涉及 Galaxypedia 的 PDF、MinerU、分类和 bundle 时，改用 `zotero-galaxypedia-bridge`。

Bridge 管理的迁移不要用 CLI 单独删除旧 linked PDF；由 Bridge 在新 relative attachment 读回、旧 attachment 不再活跃且 hash 一致后清理。历史 bundle 需要收敛时用 Bridge `cleanup-source`。
