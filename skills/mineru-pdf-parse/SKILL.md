---
name: mineru-pdf-parse
description: 当用户需要使用 MinerU 解析 PDF、本地或远程 PDF 转 Markdown、解析论文 PDF、提取 PDF 中的图片、公式或表格时使用。不要在普通网页文章、HTML 页面清洗或 Galaxypedia wiki ingest 中自动使用，除非用户明确要求 MinerU。
---

# MinerU PDF Parse

这个 skill 用于把本地 PDF 或远程 PDF URL 交给 MinerU 解析，并把 Markdown 结果保存到当前项目的 `minerU/outputs/`。它是全局通用工具，不依赖特定项目，也不会写入 Galaxypedia 的 `raw/`、wiki、manifest 或日志。

## 触发边界

使用本 skill 的典型场景：

- 用户明确提到 MinerU、PDF 解析、PDF 转 Markdown。
- 用户给出 `.pdf` 本地路径，希望提取文本、图片、公式或表格。
- 用户给出 PDF URL，希望转换成 Markdown。
- 用户希望解析论文 PDF、技术报告 PDF 或 arXiv PDF。

不要主动用于以下场景：

- 普通网页文章或 HTML 页面清洗。
- 已经是 Markdown 的资料整理。
- Galaxypedia `/ingest` 流程，除非用户明确要求用全局 MinerU skill。

## 使用前检查

- 先确认当前工作目录是否是用户想保存结果的项目根目录。
- 如果不是项目根目录，运行脚本时传入 `--project-root <项目根目录>`。
- MinerU 是云端解析服务。未公开论文、审稿材料、含隐私或授权受限内容的 PDF，上传前必须提醒用户自行确认是否允许云端处理。
- 不要记录、打印或写入 `MINERU_API_TOKEN`。

## Codex 命令

从目标项目根目录运行：

```bash
python "$HOME/.codex/skills/mineru-pdf-parse/scripts/mineru_parse.py" <pdf-or-url> --mode auto
```

如果当前目录不是项目根目录：

```bash
python "$HOME/.codex/skills/mineru-pdf-parse/scripts/mineru_parse.py" <pdf-or-url> --project-root /path/to/project --mode auto
```

## Claude Code 命令

从目标项目根目录运行：

```bash
python "$HOME/.claude/skills/mineru-pdf-parse/scripts/mineru_parse.py" <pdf-or-url> --mode auto
```

如果当前目录不是项目根目录：

```bash
python "$HOME/.claude/skills/mineru-pdf-parse/scripts/mineru_parse.py" <pdf-or-url> --project-root /path/to/project --mode auto
```

## 常用参数

- `--mode auto|agent|precision`：默认 `auto`。检测到 `MINERU_API_TOKEN` 时使用 `precision`，否则使用 `agent`。常规任务使用 `auto`，不要手动指定 `agent`，除非用户明确要求免费轻量模式。
- `--language ch|en`：解析语言。中文 PDF 用 `ch`，英文论文建议用 `en`。
- `--page-range 1-5`：只解析指定页码范围。
- `--ocr`：扫描版或图片型 PDF 启用 OCR。
- `--out minerU/outputs/example.mineru.md`：指定输出文件，必须位于项目的 `minerU/outputs/` 下。
- `--force`：覆盖指定输出；未使用时如果文件已存在会自动追加 `-1`、`-2` 后缀。
- `--timeout 1800`：解析大 PDF 时增加等待时间。

## 输出结构

默认输出到当前项目：

```text
minerU/outputs/example.mineru.md
minerU/outputs/example.mineru/images/...
```

Markdown 图片链接保持普通相对链接：

```markdown
![](example.mineru/images/figure.jpg)
```

如果需要图片、图表资源或完整资源目录，必须确保运行脚本的 Codex/Claude Code 进程环境中能读取到 `MINERU_API_TOKEN`，让 `--mode auto` 自动进入 precision 模式。agent 模式通常只返回 Markdown，不返回图片资源。

## 依赖和 Token

脚本依赖 Python 3 和 `requests`。如缺少依赖，在目标环境中安装：

```bash
pip install requests
```

精准解析需要环境变量：

```bash
export MINERU_API_TOKEN='你的 MinerU API Token'
```

脚本只从运行进程环境读取 `MINERU_API_TOKEN`，不会读取仓库配置文件或 shell 启动文件。如果终端里有 token 但 Codex/Claude Code 没有，通常是 GUI 或 agent 进程没有继承 shell 环境；请在启动 Codex、Claude Code 或 cc-switch 的环境中设置该变量，或从带 token 的 shell 启动相关进程。

不要把 token 写入项目文件、skill 文件、README、日志或聊天内容。
