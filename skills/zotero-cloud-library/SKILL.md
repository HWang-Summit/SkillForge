---
name: zotero-cloud-library
description: 已弃用的 Zotero Web API 写入兼容技能。当前开发版的论文、metadata 与 collection 读写通过 Zotero Desktop 本地开发 API 和 Zotero-Galaxypedia Bridge 完成，官方云端同步仍由 Zotero Desktop 自己负责。
---

# Deprecated: Zotero Cloud Library

不要用 Zotero Web API 向当前开发工作流写入论文 metadata、collection 或附件，也不要把 API key 加入此流程。直接 Web API 写入会绕开本地 canonical PDF bundle、MinerU 解析、AI 分类提案和 relative linked attachment 验证。

新的论文流程由 `galaxypedia-wiki-ingest` 和 Bridge 管理：先 `stage-*`，再生成可审计的分类提案，最后 `commit-bundle --apply`。对新一级/二级 collection，必须获得用户明确确认并传入 `--allow-create-collection`。

官方云端同步并未被禁用：由 Zotero Desktop 的同步机制处理本地条目、metadata 和 collection。相对 linked PDF 的文件本身不由 Zotero 云端附件同步；它的事实源是 `raw/papers`。

仅在用户明确要求维护一个独立、官方 Web API 管理的非开发库时，才单独恢复或重写 Web API 流程；不得混用两个写入通道。
