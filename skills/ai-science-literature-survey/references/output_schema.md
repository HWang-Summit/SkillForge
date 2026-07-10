# 输出字段说明

## 核心题录字段

- `title`：论文题目。
- `abstract`：摘要。只采集摘要，不解析全文。
- `authors`：作者列表。
- `year`：发表年份。
- `venue_or_journal`：原始来源名。
- `publication_status`：发表状态。
- `official_url`：官方页面或 DOI 页面。
- `doi`：DOI。
- `arxiv_url`：补充 arXiv 链接；arXiv-only 不独立纳入。

## 严格来源字段

- `target_venue_key`：目标来源唯一键。
- `target_venue_name`：规范化目标来源名称。
- `target_venue_type`：`conference` 或 `journal`。
- `target_venue_tier`：`core`、`tier1` 或 `tier2`。
- `venue_match_status`：`exact`、`alias`、`manual_verified` 等。

## 检索审计字段

- `retrieval_round`：检索轮次。
- `retrieval_source`：检索来源，例如 Crossref venue-restricted。
- `query_text`：实际检索关键词。
- `venue_filter`：来源限定条件。
- `year_filter`：年份或日期范围。
- `retrieval_date`：检索日期。

## 分类字段

- `primary_domain`：一级领域。
- `secondary_domain`：可选交叉领域。
- `subdomain`：二级主题。
- `method_tags`：AI 方法标签。
- `application_tags`：应用关键词标签。
- `relevance_score`：规则打分。
- `screening_status`：`include`、`candidate`、`manual_required` 或 `exclude`。
- `exclusion_reason`：排除原因。
