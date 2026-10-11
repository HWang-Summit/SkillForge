# 页面模板

以下模板用于新建页面。旧页面不需要批量迁移。

## Domain (dynamic navigation)

```markdown
---
type: domain
title: "Domain"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - domain
status: developing
related: []
sources: []
---

# Domain

One-sentence scope; do not invent source-derived claims.

## Topics

- [[wiki/topics/example-topic.md|Example Topic]]
```

## Topic (dynamic navigation)

```markdown
---
type: topic
title: "Topic"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - topic
status: developing
related: []
sources: []
---

# Topic

One-sentence scope; create only for multiple sources or a source plus reusable concept/entity.

## Domain

- [[wiki/domains/example-domain.md|Example Domain]]

## Summaries

- [[wiki/summaries/example-source.md|Example Source]]

## Concepts

## Entities
```

New or updated knowledge pages link back to a confirmed Topic in the body or
`## See also`. A page may link to several Topics. Paper-derived pages without
a credible match can remain unclassified. Formal daily-source pages instead
link directly to Daily Knowledge and appear in its pending-organizing list;
see `references/daily-knowledge.md`. Do not create an empty Topic.

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

## Source Area (provenance navigation)

```markdown
---
type: meta
title: "Source Area"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - meta
  - source-area
status: developing
meta_kind: source-area
source_layer: papers
source_namespace: astroinformatics
related: []
sources: []
---

# Source Area

Scope of this source type or stable storage namespace, not a scientific Topic.

## Raw Sources and Corresponding Summaries

| Raw Markdown | Recorded Bridge State | Wiki Summary |
| --- | --- | --- |
| [[raw/papers/example/paper.mineru.md\|Raw source]] | `ingested` | [[wiki/summaries/example.md\|Example Summary]] |

## Parent

- [[wiki/source-areas/papers.md|Paper Sources]]
```

Source types may be empty. Namespace leaves require actual sources. Read
`references/source-areas.md` for selection, coverage, and maintenance rules.

## Daily Domain fallback

Use the ordinary `domain` frontmatter and the stable Daily Knowledge path.
A confirmed daily Topic links to this Domain and its knowledge pages.
With no suitable Topic, add reciprocal body navigation instead:

```markdown
# 日常知识

## Topics

## 待整理内容

- [[wiki/summaries/example-daily-source.md|待整理的日常来源]]
```

The pending knowledge page links back in `## See also`:

```markdown
- [[wiki/domains/daily-knowledge.md|日常知识]]
```

Once a trusted Topic exists, replace only the organizing fallback relations.
Keep scientific/source content, language, and existing research links unchanged.
