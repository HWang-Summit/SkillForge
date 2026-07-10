# 严格来源匹配策略

本 skill 的核心质量控制是“先限定目标会议/期刊，再做领域分类”。不允许先全网泛检再事后宽松过滤。

## 可进入严格纳入集的匹配状态

- `exact`
- `alias`
- `manual_verified`

`fuzzy_only` 不得进入严格纳入集。

## 必须硬区分的来源

- `Bioinformatics` 不等同于 `BMC Bioinformatics`。
- `Remote Sensing of Environment` 不等同于 MDPI `Remote Sensing`。
- `IEEE TGRS`、`IEEE JSTARS`、`IEEE GRSL` 分别独立匹配。
- `IEEE T-PAMI` 只匹配 `IEEE Transactions on Pattern Analysis and Machine Intelligence`。
- `Nature` 不等同于 `Nature Communications`、`Nature Machine Intelligence`、`Nature Computational Science` 或其他 Nature 子刊。
- `ApJ`、`ApJL`、`ApJS` 分别独立匹配。
- arXiv、bioRxiv、EarthArXiv 不作为独立目标来源；只能作为正式目标来源论文的补充链接。

## 处理原则

1. 期刊优先使用完整刊名精确匹配。
2. 会议可使用标准简称和全称别名，但必须有词边界保护，避免误匹配。
3. 来源匹配失败时记录到排除或审计报告，不要静默丢弃。
4. 对不确定来源标记 `manual_required`，不要强行纳入。
