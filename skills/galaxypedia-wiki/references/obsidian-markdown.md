# Obsidian Markdown 规则

本参考吸收 `kepano/obsidian-skills` 的 `obsidian-markdown` 思路，但服务于 Galaxypedia 的现有 schema。写 wiki 页面时优先遵守 `SCHEMA.md` 和 frontmatter 模板；本文件只补充 Obsidian 语法约定。

## 链接

- vault 内部页面优先用 wikilink：`[[wiki/concepts/example.md]]`。
- 需要自定义显示文本时用：`[[wiki/concepts/example.md|显示文本]]`。
- 指向同页标题：`[[#标题]]`。
- 指向其他页标题：`[[wiki/summaries/example.md#Key Claims]]`。
- 外部网页、论文 DOI、GitHub URL 使用 Markdown 链接：`[text](https://example.com)`。
- 用户可点击的文件引用，回答中优先用 wikilink，不用纯路径。

## 嵌入

- 本地图片、PDF、音视频使用 Obsidian embed：`![[image.png]]`。
- 指定图片宽度：`![[image.png|600]]`。
- 嵌入 PDF 页：`![[paper.pdf#page=3]]`。
- 不要直接嵌入外部图片 URL；需要长期保存时先下载到 vault，再改为本地 embed。

## Callouts

使用 callout 标注重要判断，不滥用：

```markdown
> [!warning] Contradiction
> 新来源与旧来源存在冲突，需列出双方来源。
```

常用类型：`note`、`tip`、`warning`、`info`、`example`、`quote`、`question`、`danger`。

## Frontmatter / Properties

- 新建 wiki 页面使用 `skills/galaxypedia-wiki/references/frontmatter.md`。
- YAML 保持 flat；不要随意引入嵌套对象。
- wikilink 放入 YAML 时必须加引号。
- 日期使用 `YYYY-MM-DD`。
- 不批量迁移旧页面 frontmatter。

## Tags

- tag 放在 frontmatter 的 `tags` 数组中优先于正文散落 tag。
- 正文 inline tag 只在确有检索价值时使用。
- tag 使用小写、短横线或层级：`#wiki/source-index`。

## 注释、高亮、数学和图

- Obsidian 注释：`%% hidden comment %%`，只用于维护提示，不写入来源事实。
- 高亮：`==重要文本==`，少量使用。
- 数学：行内 `$...$`，块级 `$$...$$`。
- Mermaid 适合轻量流程图；可视化知识结构优先使用 `.canvas`。

## 选择 Markdown 还是 Canvas

- 页面正文中的小流程：Mermaid。
- 可点击、可移动、需要分组的结构图：JSON Canvas。
- 自动全量链接网络：Obsidian Graph View。
- 长期知识正文：Markdown wiki 页面。
