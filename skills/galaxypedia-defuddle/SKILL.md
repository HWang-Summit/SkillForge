---
name: galaxypedia-defuddle
description: 当清洗网页文章、博客、文档页 URL 并保存为 Galaxypedia raw/articles Markdown 来源时使用。用于在 ingest 前去除广告、导航、页脚和网页噪声。
---

# Defuddle

使用这个 skill，把网页文章 URL 清洗成适合摄入的 `raw/articles/*.md`。
Defuddle 是 `/ingest` 的网页预处理器，不是 wiki 写入器。

## 边界

- 只处理网页文章、博客、新闻、文档页等 HTML 内容。
- PDF、Office 文档、图片或明显指向文件下载的 URL 交给 `skills/galaxypedia-mineru-import/SKILL.md`。
- 输出只能保存到 `raw/articles/`，作为后续 `galaxypedia-wiki-ingest` 的 source。
- 不修改 `wiki/`、`wiki/index.md` 或 `wiki/log.md`。
- 不保存 cookie、认证 header、会话信息或含凭证的 URL query。

## Ingest 触发

当 `/ingest` 收到远程 URL 时先判断类型：

- 网页文章、博客、HTML 文档页：优先尝试 Defuddle。
- PDF、Office、图片 URL：使用 MinerU。
- 无法判断时：先说明判断依据；偏网页内容则 Defuddle，偏文件内容则 MinerU。

如果 URL 已经被保存为 `raw/articles/*.md`，不要重复清洗，直接进入 `galaxypedia-wiki-ingest`。

## 命令

检查是否安装：

```bash
command -v defuddle >/dev/null 2>&1 && defuddle --version || echo "defuddle not installed"
```

清洗 URL 并输出到 stdout：

```bash
defuddle "https://example.com/article"
```

保存到 `raw/articles/` 时使用小写 kebab-case 文件名，并附加日期：

```bash
# 示例文件名：raw/articles/example-article-2026-05-30.md
defuddle "https://example.com/article" > raw/articles/example-article-2026-05-30.md
```

保存后在文件顶部加入 source frontmatter：

```markdown
---
source_url: "https://example.com/article"
fetched: YYYY-MM-DD
processor: defuddle
---
```

## Fallback

如果 `galaxypedia-defuddle` 未安装：

1. 明确报告：`galaxypedia-defuddle` 不可用，本次无法做网页清洗。
2. 如果用户提供的 URL 是 PDF/Office/图片，改用 MinerU。
3. 如果是普通网页，询问是否允许用浏览器/网页抓取能力或让用户先用 Obsidian Web Clipper 保存到 `raw/articles/`。
4. 不要凭模型记忆伪造网页内容。

## 完成后

导入成功后继续使用生成的 `raw/articles/*.md` 作为本次 ingest source，并切回 `skills/galaxypedia-wiki-ingest/SKILL.md`。
