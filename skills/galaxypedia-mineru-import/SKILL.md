---
name: galaxypedia-mineru-import
description: 当使用 MinerU 解析 PDF、Office 文档、图片或远程文档 URL，并把提取出的 Markdown 导入 Galaxypedia raw 来源目录时使用。
---

# MinerU Import

使用这个 skill，把外部文档转换为 `raw/` 中的不可变 Markdown 来源。
MinerU 是 `/ingest` 的按需预处理器，不是 wiki 写入器。

## 边界

- 解析后的 Markdown 只能保存到 `raw/articles/`、`raw/books/`、`raw/papers/` 或 `raw/notes/`。
- 如果 MinerU 结果包包含图片，脚本会保存到 Markdown 同名资源目录，并把图片引用改写为 Obsidian `![[...]]` 嵌入。
- 不要修改 `wiki/`、`wiki/index.md` 或 `wiki/log.md`。
- 在 `/ingest` 中触发时，导入成功后继续使用生成的 Markdown 作为本次摄入来源。
- 单独手动运行脚本时，导入成功后提示下一步 `/ingest raw/...`。
- 不要记录 API token、签名上传 URL，或可能包含凭证的请求体。

## Ingest 触发

当 `/ingest` 收到以下来源时，应先触发 MinerU：

- PDF：`.pdf`
- Office 文档：`.doc`、`.docx`、`.ppt`、`.pptx`、`.xls`、`.xlsx`
- 图片：`.png`、`.jpg`、`.jpeg`、`.webp`、`.tif`、`.tiff`
- 远程 URL，仅限指向 PDF、Office 文档或图片等文件型内容的 URL

如果来源已经是 `raw/` 下的 Markdown，不要触发 MinerU。
如果来源是网页文章、博客或 HTML 文档页，优先使用 `skills/galaxypedia-defuddle/SKILL.md`。

## 脚本

`scripts/mineru_parse.py` 是项目级工具，放在根目录 `scripts/`，而不是放在本 skill 目录下。原因是它直接读写本项目 `raw/`，依赖项目根路径和 Conda 环境，并且会被 `/ingest` 和用户手动命令共同调用。

常用命令：

```bash
conda run -n galaxypedia python scripts/mineru_parse.py <file-or-url> --category papers
```

其他用法：

```bash
conda run -n galaxypedia python scripts/mineru_parse.py <file-or-url> --out raw/papers/example.mineru.md
conda run -n galaxypedia python scripts/mineru_parse.py <zotero-pdf> --out raw/papers/my-paper/example.mineru.md
conda run -n galaxypedia python scripts/mineru_parse.py <file-or-url> --mode agent
conda run -n galaxypedia python scripts/mineru_parse.py <url> --mode precision --model-version vlm
```

Zotero 来源先用 `skills/galaxypedia-zotero-ingest/SKILL.md` 和 `scripts/zotero_ingest.py export ...` 解析 metadata、collection 和 PDF path。使用 export JSON 中的 `selected_pdf.resolved_path` 作为输入，`recommended_raw_output` 作为 `--out`。

本项目推荐使用全局 Conda 环境 `galaxypedia`。如果已激活该环境，也可以直接运行 `python scripts/mineru_parse.py ...`。

输出结构示例：

```text
raw/papers/example.mineru.md
raw/papers/example.mineru/images/figure.jpg
```

Markdown 中的 `![](images/figure.jpg)` 会改写为 `![[example.mineru/images/figure.jpg]]`。

## 产物保留

- `.mineru.md` 和同名资源目录是 raw source 的一部分，默认不自动清理。
- 如果重新解析同一来源且未使用 `--force`，脚本会生成带序号的新文件，避免覆盖旧结果。
- 如果用户明确要求清理失败或重复的 MinerU 产物，先列出将删除的文件并获得确认。
- 成功导入后，后续 wiki 写入由 `galaxypedia-wiki-ingest` 负责；本 skill 不创建 summary/concept/entity 页面。

## API 选择

- `agent` 模式使用 MinerU 轻量 API，不需要 token，但文件大小和页数限制更小。
- `precision` 模式使用 MinerU 精准 API，需要环境变量 `MINERU_API_TOKEN`。
- `auto` 模式检测到 `MINERU_API_TOKEN` 时走精准 API，否则走轻量 API。

## Token 设置

不要把 token 发到聊天里，也不要写入 vault。推荐写入本机 zsh 登录配置：

```bash
export MINERU_API_TOKEN='你的-token'
```

当前项目已验证：放在 `~/.zprofile` 中时，登录 shell 可以读取到该环境变量。`~/.zprofile` 适合放环境变量；不要放会打印内容、启动程序或切换目录的命令。

## 敏感文档

MinerU 是云端解析服务。上传私密、受监管或未公开资料前，先确认云端处理是可接受的。
