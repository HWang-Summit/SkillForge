---
name: galaxypedia-wiki-query
description: 查询 Galaxypedia wiki。按 quick、standard、deep 模式读取索引和相关页面，综合回答并可把高价值答案回存。
---

# Wiki Query

使用这个 skill 回答“基于 wiki 的问题”。如果 wiki 没有足够内容，明确说明缺口，不要用模型记忆伪装成 wiki 事实。

## 查询模式

| 模式 | 触发 | 读取范围 | 用途 |
| --- | --- | --- | --- |
| quick | “quick/快速/简单查一下” | `wiki/index.md` | 快速事实、页面定位 |
| standard | 默认 | index + 3-5 个相关页 | 大多数问题 |
| deep | “deep/全面/综合/比较全部” | 所有相关页 | 跨来源综合、比较、缺口分析 |

## 工作流

1. 读 `SCHEMA.md` 和 `wiki/index.md`。
2. 根据问题选择 quick/standard/deep。
3. 从 index 中挑选候选页，优先标题精确匹配，其次摘要关键词匹配。
4. standard 模式读取 3-5 个最相关页面；deep 模式读取所有必要页面。
5. 普通查询只读 wiki 页面；需要核对原文、图片、表格、精确引用或矛盾时，沿 wiki 页面的 `## Sources`、`wiki/meta/source-index.md` 或 `raw/.manifest.json` 回到 raw。
6. 综合回答，事实性结论后附来源页面。
7. 如果知识不足，说清楚缺什么来源。
8. 高价值答案可询问是否回存为 `wiki/comparisons/` 或 `wiki/meta/` 页面；用户同意后再写入、更新 index、source-index（如涉及来源）和 log。

## 候选页选择

- 精确标题命中优先于关键词命中。
- summary 页适合回答“某篇来源说了什么”。
- concept 页适合回答“某概念是什么、如何演化、有哪些来源支持”。
- entity 页适合回答“某人/组织/项目在 wiki 中出现在哪里、与哪些概念相关”。
- comparison 页适合回答“二者差异、取舍、综合判断”。

如果 index 中存在多个近似条目，先说明将读哪些页面，避免把同名或近名概念混在一起。

## Raw 回溯规则

默认查询层是 `wiki/`，不是 `raw/`。这样可以保持查询快速、聚焦，并复用已整理的知识结构。

只有以下情况才读 raw：

- 用户明确要求核对原文、看 raw、看图表、精确引用。
- wiki 页面出现矛盾，需要回到原始来源判断。
- wiki 覆盖不足，但 `wiki/meta/source-index.md` 显示存在相关 raw source。
- 用户要求重新摄入或检查某个 source 的 provenance。

回溯路径优先级：

1. 当前候选 wiki 页的 `## Sources`。
2. `wiki/meta/source-index.md`。
3. `raw/.manifest.json`。

读取 raw 后，回答中要区分“wiki 综合结论”和“raw 原文核验结果”。

## 回答质量分级

回答时在内部按以下等级判断，不必每次都显式输出：

- `solid`：wiki 中有多个相关页面或来源，结论可追溯。
- `partial`：只有单一来源或覆盖不完整，应指出缺口。
- `missing`：wiki 没有足够材料，不能假装已知。

只有 `solid` 或有长期复用价值的 `partial` 答案适合回存。

## 引用方式

- 使用 Obsidian wikilinks 引用 wiki 页面，例如：`（来源：[[wiki/summaries/example.md]]）`。
- 外部网页、GitHub、DOI 等使用 Markdown links；不要把 vault 内文件写成不可点击纯路径。
- 不引用未读页面。
- 不把外部网络知识混入 wiki 答案，除非用户明确要求补充外部检索。
- 回答末尾列出 `Sources consulted`，只列实际读取过的 wiki/raw 页面。

## 回存规则

适合回存：

- 多页综合。
- 有长期复用价值的比较。
- 明确回答了一个反复会问的问题。
- 查询暴露了一个应长期维护的研究问题。

不适合回存：

- 简单定位。
- 一次性聊天。
- wiki 覆盖不足且没有可靠来源的推测。

回存前必须告诉用户目标路径，例如 `wiki/comparisons/x-vs-y.md` 或 `wiki/meta/question-name.md`；用户同意后再写入。
