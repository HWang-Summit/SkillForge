---
name: pdf-render-contact-sheet
description: 当用户需要把任意 PDF 渲染为逐页 PNG、生成 contact sheet 总览图、检查 PDF 页面视觉布局、空白页、截断、页面顺序、图表或文字过小、导出/排版异常时使用。适用于报告、讲义、论文、文档导出版等 PDF；不用于 OCR、正文抽取、公式/表格解析或 PDF 转 Markdown。
---

# PDF Render Contact Sheet

这个 skill 用于对 PDF 做本地视觉 QA：把 PDF 渲染为逐页图片，并生成一张带页码标签的 contact sheet，方便快速检查页面渲染和版面问题。

典型产物：

- `rendered_pdf_pages/page-01.png`、`page-02.png` ...
- `rendered_pdf_pages/contact.png`
- 按页码组织的视觉检查结论

## 使用边界

适合使用本 skill：

- 检查报告、讲义、论文、导出版文档等 PDF 是否渲染正常。
- 快速查看是否有空白页、截断、页面顺序异常、图表或文字过小。
- 检查导出后的 PDF 是否存在页面布局、分页、图片显示或排版异常。
- 在修改源文件前，先建立可复查的页面 PNG 和 contact sheet。

不要用于：

- OCR 或扫描件文字识别。
- 正文语义抽取、公式/表格结构解析。
- PDF 转 Markdown。
- 替代 `mineru-pdf-parse` 做内容解析。

## 工作流

1. 确认输入 PDF 路径。
   - 如果用户说 `main.pdf`，但实际只存在 `paper/build/main.pdf`，可使用实际存在的路径，并说明选择。
   - 渲染和检查阶段不要修改输入 PDF 或源文件。
2. 运行 `run_pdf_contact_sheet.sh`。
   - 不要直接调用裸 `python` 或 `python3`。
   - 运行后先看 `Selected Python command:`，确认没有误用不合适的系统 Python。
3. 先查看 `contact.png`，再打开可疑的单页 PNG。
4. 报告输出目录、生成文件，以及按页码列出的视觉问题。
5. 如果用户要求修复源文件，先基于视觉检查结论做最小修改，再重新编译 PDF、重新渲染并复查。

## Codex 命令

从目标项目根目录运行：

```bash
"$HOME/.codex/skills/pdf-render-contact-sheet/scripts/run_pdf_contact_sheet.sh" \
  --pdf paper/build/main.pdf \
  --out rendered_pdf_pages \
  --dpi 150 \
  --thumb-width 300 \
  --cols 3
```

## Claude Code 命令

从目标项目根目录运行：

```bash
"$HOME/.claude/skills/pdf-render-contact-sheet/scripts/run_pdf_contact_sheet.sh" \
  --pdf paper/build/main.pdf \
  --out rendered_pdf_pages \
  --dpi 150 \
  --thumb-width 300 \
  --cols 3
```

## 常用参数

- `--pdf <path>`：输入 PDF，必填。
- `--out rendered_pdf_pages`：输出目录，默认 `rendered_pdf_pages`。
- `--dpi 150`：渲染分辨率；快速预览可用 `72`，细节检查建议 `150` 或更高。
- `--thumb-width 300`：contact sheet 中每页缩略图宽度。
- `--cols 3`：contact sheet 列数。
- `--pdftoppm /path/to/pdftoppm`：显式指定 Poppler 的 `pdftoppm`。

## 依赖和环境

本 skill 是纯本地渲染工具，不需要 API token，也不读取 `$HOME/.skillforge/env`。

依赖：

- Poppler 的 `pdftoppm`
- Python 3
- Pillow

如需安装依赖，优先安装到将运行脚本的环境中：

```bash
conda install -n <env> -c conda-forge poppler pillow
```

可通过环境变量固定运行环境：

```bash
PDF_RENDER_PYTHON=/path/to/python
PDF_RENDER_CONDA_ENV=base
```

`run_pdf_contact_sheet.sh` 的 Python 选择顺序：`PDF_RENDER_PYTHON`、常见 conda Python、`CONDA_EXE run -n "${PDF_RENDER_CONDA_ENV:-base}" python`、`python`、`python3`。

## 视觉 QA 检查项

查看 `contact.png` 和可疑单页 PNG 时，重点检查：

- 空白页、页末或页首大面积空白。
- 页面内容被截断、图片缺失、页面顺序异常。
- 图表、坐标轴、图例、表格或正文过小。
- 高亮、批注、修订痕迹或导出残留。
- 横版/竖版页面方向异常。
- 结尾页只有孤立图片、少量文字或异常分页。

如果 contact sheet 上疑似有问题，先打开对应单页 PNG 确认，再作为正式问题报告。

## 源文件修改规则

- 渲染和检查本身不修改 PDF 或源文件。
- 用户要求修复时，优先做最小源文件改动，例如调整分页、图片尺寸、浮动体位置、表格布局或导出设置。
- 修改后重新生成 PDF，再重新运行本 skill 复查受影响页面。
