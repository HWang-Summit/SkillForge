# 页面模板

以下模板用于新建页面。旧页面不需要批量迁移。

## Summary

```markdown
---
type: summary
title: "Title"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - summary
status: seed
related: []
sources:
  - "raw/papers/source.md"
source_type: paper
author: ""
date_published: ""
confidence: medium
key_claims: []
---

# Title

2-3 句说明这个来源讲了什么、为什么值得进入 wiki。

## Key Claims

-

## Entities Mentioned

-

## Concepts Introduced

-

## Notes

-

## Sources

- `raw/papers/source.md`

## See also

-
```

## Concept

```markdown
---
type: concept
title: "Concept"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - concept
status: seed
related: []
sources: []
aliases: []
domain: ""
complexity: intermediate
---

# Concept

一句话定义。

## Definition

## How It Works

## Why It Matters

## Examples

## Sources

## See also
```

## Entity

```markdown
---
type: entity
title: "Entity"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - entity
status: seed
related: []
sources: []
entity_type: organization
role: ""
first_mentioned: ""
---

# Entity

一句话说明这个实体是谁/是什么。

## Overview

## Key Facts

## Connections

## Sources

## See also
```

## Comparison

```markdown
---
type: comparison
title: "Comparison"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - comparison
status: seed
related: []
sources: []
subjects: []
dimensions: []
verdict: ""
---

# Comparison

## Overview

## Comparison

| Dimension | A | B |
| --- | --- | --- |

## Verdict

## Sources

## See also
```
