---
name: zotero-local-pdf-attach
description: 将本地 PDF 分批、可恢复地作为 Zotero Desktop 托管副本附加到已有文献条目，并生成匹配清单、去重检查和全量审计报告。用户需要把下载 PDF 加入本地 Zotero、避免重复附件、处理大批量文件导致卡顿、从中断处继续、核对 PDF 与父条目关系时使用。适用于 Codex 自动操作 Zotero Developer Console，或 Claude Code 生成可粘贴脚本的半自动流程。
---

# Zotero 本地 PDF 附加

使用此技能把 PDF 复制到 Zotero 管理的 storage 中。不要编辑 `zotero.sqlite`、直接改写 storage，或通过“链接文件”代替托管副本。

## 边界与安全规则

- 仅处理本地 Zotero Desktop，不上传附件到 Zotero 云端。
- 先运行 `prepare` 和 `plan`，确认匹配与批次；只有用户明确要求导入时才生成并执行 Console 脚本。
- 父条目匹配顺序固定为：`zotero_item_key`、`record_id`、DOI、唯一规范化标题。任何非唯一或缺失匹配均进入人工复核。
- 相同父条目与相同源 SHA-256 的历史成功记录会跳过；对未登记的既有 PDF，Console 脚本会比对文件内容后跳过同文件。发现不同 PDF 时只标记复核，绝不自动删除、替换或新增第二份。
- 默认每批最多 20 个文件且总大小不超过 512 MiB，批次结束后冷却 45 秒。不要在机器繁忙时提高这些限制。

## 快速流程

设 `SKILL_DIR` 为本技能目录，`OUT` 为单次任务输出目录：

```bash
python3 "$SKILL_DIR/scripts/zotero_local_pdf_attach.py" prepare \
  --tracking outputs/pdf_download/pdf_download_tracking.json \
  --pdf-root . --out outputs/zotero_pdf_task

python3 "$SKILL_DIR/scripts/zotero_local_pdf_attach.py" plan \
  --manifest outputs/zotero_pdf_task/pdf_manifest.jsonl \
  --results outputs/zotero_pdf_task/import_results.jsonl \
  --out outputs/zotero_pdf_task
```

检查 `manual_review.jsonl`、`batches.json` 与终端汇总。确认后针对第一个批次生成脚本：

```bash
python3 "$SKILL_DIR/scripts/zotero_local_pdf_attach.py" render-console-script \
  --manifest outputs/zotero_pdf_task/pdf_manifest.jsonl \
  --batches outputs/zotero_pdf_task/batches.json \
  --results outputs/zotero_pdf_task/import_results.jsonl \
  --batch-id batch-0001 --out outputs/zotero_pdf_task
```

在 Zotero 中打开“工具 > 开发者 > 运行 JavaScript”，粘贴生成的 `console_batch-0001.js` 并运行。脚本只导入该批次，追加写入 `import_results.jsonl`，并返回 JSON 汇总。等待冷却时间后重新运行 `plan` 生成下一批。

任务结束后执行：

```bash
python3 "$SKILL_DIR/scripts/zotero_local_pdf_attach.py" audit \
  --manifest outputs/zotero_pdf_task/pdf_manifest.jsonl \
  --results outputs/zotero_pdf_task/import_results.jsonl \
  --out outputs/zotero_pdf_task
python3 "$SKILL_DIR/scripts/zotero_local_pdf_attach.py" report \
  --audit outputs/zotero_pdf_task/attachment_audit.jsonl \
  --out outputs/zotero_pdf_task
```

若 `audit` 报告 `local_api_unavailable`（某些 Zotero 版本不会通过本地 API 暴露新附件），按 20 条一批生成只读 Console 核验脚本：

```bash
python3 "$SKILL_DIR/scripts/zotero_local_pdf_attach.py" render-audit-console-script \
  --manifest outputs/zotero_pdf_task/pdf_manifest.jsonl \
  --results outputs/zotero_pdf_task/import_results.jsonl \
  --audit outputs/zotero_pdf_task/attachment_audit.jsonl \
  --out outputs/zotero_pdf_task
```

在 Developer Console 运行生成的 `console_audit-*.js` 后，再运行 `report`。该脚本只读取并核验，不会新增、删除或修改附件。

## Codex 与 Claude Code

**Codex**：确认 Zotero 已启动、Developer Console 可用。每次只粘贴并执行一个 `console_batch-*.js`；读取返回 JSON 后，等待冷却、重新运行 `plan`，再继续下一批。连续两批出错或 Zotero 无响应时停止。

**Claude Code**：不得尝试操作 Zotero 图形界面。生成脚本后，向用户给出中文交接：脚本绝对路径、批次编号、文件数/容量、在 Developer Console 的粘贴步骤及运行后需回传的 JSON。用户完成一个批次后，再运行 `plan`、`audit` 或 `report`。

## 输入与输出

`--tracking` 支持 JSON、CSV、XLSX。每条应包含 `record_id`、`title`、`doi`、`pdf_path`；可选 `pdf_status`（仅 `downloaded` 纳入）和 `zotero_item_key`。详细字段、状态值和恢复处理见 [references/数据契约.md](references/数据契约.md)。

`prepare`、`plan`、`audit` 均为只读 Zotero 操作；所有 `render-*` 命令只生成文件。真正的写入只发生在用户于 Zotero Desktop 执行导入脚本时；核验脚本只读取附件。
