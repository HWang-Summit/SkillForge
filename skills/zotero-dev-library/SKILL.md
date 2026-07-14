---
name: zotero-dev-library
description: 通过本地开发 API 与 CLI 安全读取和管理正在运行的 Zotero 开发版。用于条目、collection、metadata、标签、成员关系、回收站和既有相对链接附件的查询或修改；拒绝未带开发版标记的端点。
---

# Zotero Development Library

仅操作运行中的 Zotero 开发版，绝不直接修改 `zotero.sqlite`、storage 或正式版实例。

## 连接与边界

1. 在每次读写前运行 `scripts/probe-dev-api.mjs`；它读取 `ZOTERO_LOCAL_API_URL`，默认本机 `/api` 端点。
2. 缺少 `X-Zotero-Development-API: 1` 时立即停止，不得回退到普通或未标记端点。
3. 写入仅从执行环境读取 `ZOTERO_LOCAL_API_TOKEN`；可由本机私密 `${SKILLFORGE_ENV_FILE:-$HOME/.skillforge/env}` 提供，不打印、记录或要求用户贴到聊天中。
4. 设置 `ZOTERO_PROJECT_ROOT` 为开发版 Zotero 项目根目录，再使用其 `tools/zotero-cli.mjs`。SkillForge 不保存该机器路径。

```sh
node <skill-dir>/scripts/probe-dev-api.mjs
node "$ZOTERO_PROJECT_ROOT/tools/zotero-cli.mjs" item get <item-key>
node "$ZOTERO_PROJECT_ROOT/tools/zotero-cli.mjs" collection get <collection-key>
```

## 读写规则

- 读取时报告 key、标题/collection 名、library 和匹配数量。
- 创建单一条目或 collection 前说明将创建的对象；更新、删除、恢复、标签、成员关系、批量操作或 `--force` 前，先展示精确对象与命令并获得明确确认。
- CLI 已处理 Token 与乐观并发头；不要改用裸 API 写请求。
- 每次成功写入后读回对象；遇到 version/ETag 冲突时停止、重新读取，不默认强制覆盖。

支持 item/collection metadata、creators、tags、notes、relations、collection membership、trash/restore 以及已有相对链接 PDF 附件。不承诺 stored-file 上传、任意文件系统操作、PDF 标注或全文索引写入。

## Relative linked PDF

先确认父条目、相对路径以及 Zotero 的 Linked Attachment Base Directory。链接文件必须已存在且为相对 `.pdf` 路径：

```sh
node "$ZOTERO_PROJECT_ROOT/tools/zotero-cli.mjs" attachment list <parent-item-key>
node "$ZOTERO_PROJECT_ROOT/tools/zotero-cli.mjs" attachment link <parent-item-key> \
  --relative-path 'pdf-a1b2c3d4e5f6a7b8/paper.pdf'
```

读回新附件验证。删除附件是高风险写入：它只会将 Zotero 附件移入回收站，不应假设会删除 linked PDF。涉及 Galaxypedia 的 PDF、MinerU、分类和 bundle 时，改用 `zotero-galaxypedia-bridge`。
