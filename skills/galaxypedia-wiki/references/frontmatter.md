# Frontmatter 规范

新建 wiki 页面时使用 flat YAML frontmatter。旧页面不批量迁移，后续编辑时按需补齐。

## 通用字段

```yaml
---
type: summary
title: "Human Readable Title"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - summary
status: seed
related: []
sources:
  - "raw/papers/example.mineru.md"
---
```

## type

- `summary`：单个来源摘要。
- `entity`：人物、组织、项目、软件、数据集。
- `concept`：概念、方法、理论、算法。
- `comparison`：跨来源对比或综合。
- `meta`：wiki 元信息、lint 报告、维护说明。

## status

- `seed`：刚创建，内容较少。
- `developing`：已有实质内容，但仍可扩展。
- `mature`：覆盖较完整，链接和来源充分。
- `evergreen`：稳定长期有效。

## 类型扩展

summary：

```yaml
source_type: paper
author: ""
date_published: ""
confidence: medium
key_claims: []
```

entity：

```yaml
entity_type: person
role: ""
first_mentioned: ""
```

concept：

```yaml
aliases: []
domain: ""
complexity: intermediate
```

comparison：

```yaml
subjects: []
dimensions: []
verdict: ""
```

## 规则

- YAML 保持扁平，不使用嵌套对象。
- 日期使用 `YYYY-MM-DD`。
- YAML 中的 wikilink 必须加引号。
- 每次编辑页面内容时更新 `updated`。
