---
name: galaxypedia-json-canvas
description: 创建和维护 Obsidian JSON Canvas（.canvas）文件。用户要求 canvas、白板、概念图、架构图、工作流图、topic map、source provenance 可视化时使用。
---

# JSON Canvas

本 skill 用于生成和更新 Obsidian 原生 `.canvas` 文件。参考 JSON Canvas 1.0 结构和 `kepano/obsidian-skills` 的 json-canvas 规则，但按 Galaxypedia 项目约束裁剪。

## 项目定位

- `.canvas` 是可视化派生层，不替代 `wiki/index.md`、`wiki/meta/source-index.md` 或 Obsidian Graph View。
- 全量 wiki 链接网络交给 Graph View；Canvas 只表达人工设计过的局部结构。
- 第一优先用途：项目 skills / 工作流架构图。
- 第二优先用途：局部主题图、source provenance 图、研究工作流图。
- 默认输出到 `wiki/canvas/`。
- 除非用户明确要求，不要在每次 ingest 后自动更新 canvas。

## 文件结构

`.canvas` 是 JSON 文件，顶层结构：

```json
{
  "nodes": [],
  "edges": []
}
```

节点和边都必须有唯一 `id`。推荐使用稳定、可读、短横线命名的 id；如果需要随机 id，用 16 位小写 hex。

## 节点类型

### file node

用于指向 vault 内已有文件，优先用于 skills、wiki 页面和 raw source：

```json
{
  "id": "skill-wiki-ingest",
  "type": "file",
  "x": 0,
  "y": 0,
  "width": 360,
  "height": 220,
  "file": "skills/galaxypedia-wiki-ingest/SKILL.md",
  "color": "4"
}
```

### text node

用于说明边界、流程、图例或注意事项：

```json
{
  "id": "note-boundary",
  "type": "text",
  "x": 0,
  "y": 0,
  "width": 360,
  "height": 160,
  "text": "# 说明\n\nCanvas 是派生视图，不替代 wiki/index.md。"
}
```

JSON 字符串中的换行必须是 `\n`，不要写成未转义的真实换行。

### group node

用于给一组节点加视觉容器：

```json
{
  "id": "group-ingest",
  "type": "group",
  "x": -40,
  "y": -40,
  "width": 900,
  "height": 500,
  "label": "Ingest workflow",
  "color": "4"
}
```

## 边

边连接节点：

```json
{
  "id": "edge-router-to-ingest",
  "fromNode": "skill-galaxypedia-wiki",
  "fromSide": "right",
  "toNode": "skill-wiki-ingest",
  "toSide": "left",
  "toEnd": "arrow",
  "label": "routes ingest"
}
```

`fromSide` / `toSide` 只能用 `top`、`right`、`bottom`、`left`。`fromEnd` / `toEnd` 只能用 `none` 或 `arrow`。

## 颜色约定

Obsidian Canvas 预设色：

- `"1"`：红，警告或禁止事项。
- `"2"`：橙，流程或中间层。
- `"3"`：黄，说明或注意。
- `"4"`：绿，摄入或创建。
- `"5"`：青，查询、检查、可视化。
- `"6"`：紫，入口、路由、agent 规则。

也可以使用 hex 色值，但项目图优先用预设色以适配主题。

## 布局规则

- 坐标以左上角为原点，`x` 向右，`y` 向下；可使用负坐标。
- 节点宽高优先用 300-420px 宽、160-260px 高。
- 节点之间保留 60-120px 间距。
- 布局应表达流程：左侧入口，中间处理，右侧输出；辅助能力放下方。
- 文件节点优先指向真实文件；不存在的文件不要创建 file node。

## Galaxypedia 图谱类型

### Skills map

默认路径：`wiki/canvas/galaxypedia-skills-map.canvas`。

用于展示：

- `galaxypedia-wiki` 总入口。
- `galaxypedia-wiki-ingest` 如何连接 `galaxypedia-mineru-import`、`galaxypedia-defuddle`、`zotero-galaxypedia-bridge`；旧 `galaxypedia-zotero-ingest` 仅标记为历史只读兼容入口。
- `galaxypedia-wiki-query`、`galaxypedia-wiki-lint`、`galaxypedia-karpathy-guidelines` 的职责边界。
- `galaxypedia-json-canvas` 作为可视化派生层能力。

### Source provenance map

默认路径：`wiki/canvas/source-provenance.canvas`。

只在用户要求时生成。用于展示 raw source → summary → concept/entity/comparison 的追溯关系。

### Topic map

默认路径格式：`wiki/canvas/<topic>-topic-map.canvas`。

只在用户要求时生成。用于展示一个研究主题内的实体、概念和关键来源。

## 验证清单

创建或修改 canvas 后必须验证：

1. JSON 可解析。
2. 顶层只有或至少包含 `nodes`、`edges` 数组。
3. 所有 node / edge id 唯一。
4. 每条 edge 的 `fromNode`、`toNode` 都指向存在的 node。
5. node 类型只能是 `text`、`file`、`link`、`group`。
6. file node 的 `file` 路径在 vault 中存在。
7. link node 的 `url` 非空。
8. 不把临时截图、conversation 文件放入正式 canvas。

## 禁止事项

- 不生成全量 wiki 页面 canvas，除非用户明确要求。
- 不把 Canvas 当作 source of truth；它只是派生视图。
- 不为每次 ingest 自动改 canvas。
- 不在 `.canvas` 中写入 API token、签名 URL、绝对本机隐私路径。
