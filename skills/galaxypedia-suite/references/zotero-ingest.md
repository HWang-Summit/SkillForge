# zotero-ingest 模块

迁移自 Galaxypedia `skills/zotero-ingest/SKILL.md`。本文件是 `galaxypedia-suite` 的内部参考模块，不是 SkillForge v0.1.0 中独立安装的根目录技能。

# Zotero Ingest

使用这个 skill 处理“从 Zotero 摄入论文/文献/PDF”、按 Zotero collection 列文献、按 DOI/title/item key 查找文献、刷新 Zotero 当前分类索引等任务。

## 必读上下文

1. 先读 `SCHEMA.md` 和 `the `galaxypedia-suite` router`。
2. 如果要解析 PDF，继续读 `the installed MinerU skill`。
3. 如果要把 MinerU Markdown 写入 wiki，继续读 `references/wiki-ingest.md`。

## 边界

- Zotero 是文献数据库和 PDF 管理层；Galaxypedia 是知识消化层。
- 只读 Zotero 数据库，不修改 `zotero.sqlite`、Zotero storage 或 Zotero collection。
- 不把 Zotero PDF 复制到 `raw/`；`raw/` 中保存的是 MinerU 生成的 `.mineru.md` 和图片资源。
- Zotero collection 是动态分类。摄入时 collection 决定初始 raw 路径；摄入后 collection 变化不自动移动 raw 文件。
- raw 路径迁移必须显式执行，并同步 manifest、source-index、frontmatter、`## Sources` 和日志；第一版不自动迁移。

## 脚本

项目级工具位于 `scripts/zotero_ingest.py`。

默认路径：

```bash
python scripts/zotero_ingest.py --zotero-db /Users/wanghao/Zotero/zotero.sqlite --zotero-data-dir /Users/wanghao/Zotero list-collections
```

常用命令：

```bash
python scripts/zotero_ingest.py list-collections
python scripts/zotero_ingest.py list-items --collection "My paper"
python scripts/zotero_ingest.py find --query "HCGrid"
python scripts/zotero_ingest.py export --item-key SWCEAHVR
python scripts/zotero_ingest.py export --doi 10.1093/mnras/staa3800
python scripts/zotero_ingest.py plan-batch --collection "<collection-selector>"
python scripts/zotero_ingest.py refresh-index
```

脚本输出 JSON。`export` 的关键字段包括：

- `title`, `authors`, `year`, `venue`, `doi`, `url`
- `item_key`, `selected_pdf.attachment_key`, `selected_pdf.resolved_path`
- `collections`, `primary_collection`
- `recommended_raw_output`

`<collection-selector>` 是动态 Zotero collection selector，不是固定分类名。支持：

- 完整 collection path：`人工智能/LLM`
- 叶子 collection 名：`LLM`（仅在不歧义时）
- slug path：`artificial-intelligence/llm`
- Zotero collection key：`KV33VDQK`
- collection ID

## PDF 选择

优先级：

1. 可读 Zotero stored PDF：`storage:<filename>.pdf`。
2. 当前系统可读的 linked PDF。
3. 不可读 stored PDF。
4. 不可读 linked PDF。

路径解析：

- `storage:<filename>.pdf` → `/Users/wanghao/Zotero/storage/<attachment-key>/<filename>.pdf`
- macOS/Linux 绝对 linked path 仅在文件存在时可用。
- Windows linked path 在 macOS 上标记为不可读，提示用户在 Zotero 侧改为 stored copy，或后续配置 linked base directory。
- 相对 linked path 需要 `--linked-base-dir`；没有该参数时不猜测。

如果同一条目有多个 PDF，使用脚本返回的 `selected_pdf`。如果没有可读 PDF，不要调用 MinerU；先报告 Zotero 附件问题。

## Collection 到 Raw 路径

- 使用当前 Zotero collection 生成新摄入文件的初始路径：
  - Zotero collection path: `My paper/Radio Astronomy`
  - raw output: `raw/papers/my-paper/radio-astronomy/<paper>.mineru.md`
- 使用完整层级 slug，避免同名叶子 collection 冲突。
- 非 ASCII collection 名如果无法稳定转写，脚本使用 collection key fallback，并在 JSON 中保留原始中文路径。
- 同一文献属于多个 collection 时，只在 primary collection 下保存一份 MinerU 输出。
- primary collection 规则：层级最深优先；同深度按 slug path 字典序。

摄入后 Zotero collection 变化时：

- 运行 `python scripts/zotero_ingest.py refresh-index` 更新 `wiki/meta/zotero-index.md`。
- 不移动既有 `raw/papers/.../*.mineru.md`。
- 不修改已有 summary 的 source path，除非用户明确要求迁移 raw 路径。

## 单篇摄入流程

1. 用 `find` 或 `list-items` 确认目标文献。
2. 用 `export --item-key ...` 或 `export --doi ...` 获取 JSON。
3. 检查 `selected_pdf.readable`；为 false 时停止并报告 PDF 不可读。
4. 调用 MinerU：

```bash
conda run -n galaxypedia python scripts/mineru_parse.py "<selected_pdf.resolved_path>" --out "<recommended_raw_output>"
```

5. MinerU 成功后，按 `wiki-ingest` 摄入生成的 `.mineru.md`。
6. 摄入时把 Zotero provenance 写入 `raw/.manifest.json`、`wiki/meta/source-index.md` 和 summary frontmatter。

## Collection 批量摄入流程

批量摄入默认递归包含子 collection，且按顺序逐篇解析。不要并发调用 MinerU。

1. 先刷新或查看当前 collection：

```bash
python scripts/zotero_ingest.py list-collections
```

2. 生成批量计划：

```bash
python scripts/zotero_ingest.py plan-batch --collection "<collection-selector>"
```

常用选项：

```bash
python scripts/zotero_ingest.py plan-batch --collection "<collection-selector>" --no-recursive
python scripts/zotero_ingest.py plan-batch --collection "<collection-selector>" --no-skip-existing
```

3. 检查 JSON 中的 `summary`、`planned_items`、`skipped_items` 和 `warnings`。
4. 向用户报告可摄入数量、跳过数量、不可读 PDF、路径冲突和已摄入项。
5. 按 `planned_items` 顺序逐篇执行每个 `mineru_command`。
6. 每篇 MinerU 成功后，立即按 `wiki-ingest` 摄入生成的 `.mineru.md`。
7. 如果某篇 MinerU 失败，记录失败并继续下一篇；最终报告成功、跳过、失败清单。

批量规则：

- `plan-batch` 只读 Zotero 和 manifest，只输出计划，不写 raw/wiki。
- 无可读 PDF 的条目进入 `skipped_items`。
- 非论文型条目进入 `skipped_items`。
- 已在 manifest 记录的 Zotero item 默认进入 `skipped_items`；需要重跑时使用 `--no-skip-existing`。
- 多条目推荐到同一 raw output 时，后续项追加 item key 后缀，并在 `warnings` 中记录。

## Provenance 字段

Zotero 来源至少记录：

- `source_system: zotero`
- `zotero_item_key`
- `zotero_attachment_key`
- `doi`
- `title`
- `authors`
- `year`
- `venue`
- `zotero_collections`
- `primary_collection`
- `source_pdf_path`
- `pdf_link_mode`
- `raw_path_status: stable`
- `previous_raw_paths: []`

`wiki/meta/source-index.md` 记录摄入时 provenance；`wiki/meta/zotero-index.md` 记录当前 Zotero 动态映射。
