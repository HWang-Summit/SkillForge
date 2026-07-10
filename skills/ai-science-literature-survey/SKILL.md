---
name: ai-science-literature-survey
description: 面向 Bioinformatics、Geospatial & Earth Informatics、Astroinformatics 的 AI for Science 文献严格检索、题录级采集、目标会议/期刊限定、领域分类、去重、校验和中文报告生成。Use when the user asks for strict target-venue literature surveys, configurable year/date ranges, AI顶会/高水平期刊检索矩阵, title/abstract-only paper collection, or reusable Codex/Claude Code literature-search automation.
---

# AI Science 文献严格检索

## 工作边界

使用本 skill 做目标会议/期刊严格限定的题录级文献调研。默认采集题目、摘要、作者、年份、来源、DOI、官方链接和补充链接；不下载 PDF，不解析全文，不做论文质量评分。

目标来源矩阵统一放在 `references/venue_matrix.yaml`，默认覆盖 core、tier1、tier2，不区分 v1/v2。年份不写死；用户未指定时默认检索从“当前年份 - 3”的 1 月 1 日到运行当天。

## 常用命令

在项目根目录运行：

```bash
python skills/ai-science-literature-survey/scripts/run_survey.py \
  --output-dir 文献调研输出 \
  --year-from 2023 \
  --year-to 2026 \
  --skip-official
```

只检索指定来源：

```bash
python skills/ai-science-literature-survey/scripts/run_survey.py \
  --venues tpami,jstars,aaai \
  --date-from 2024-01-01 \
  --date-to 2026-07-10 \
  --output-dir 文献调研输出 \
  --skip-official
```

校验输出：

```bash
python skills/ai-science-literature-survey/scripts/validate_outputs.py \
  --output-dir 文献调研输出
```

比较两次运行：

```bash
python skills/ai-science-literature-survey/scripts/compare_runs.py \
  --old 输出_旧 \
  --new 输出_新 \
  --out 两次运行对比
```

## 输出结构

```text
<output-dir>/
  最终交付版/
    最终主表.csv
    严格纳入论文.csv
    最终分类表.xlsx
    最终分析摘要报告.md
  过程审计/
    来源覆盖报告.md
    会议期刊占比报告.md
    关键词扩展记录.md
    排除记录及原因.csv
    重点论文回归检查.md
    运行日志.jsonl
    错误日志.md
```

## 使用规则

- 联网检索前先确认调用环境允许网络访问；无网络时使用 `--offline-from-cache --report-only` 仅基于已有原始输出重建中文交付文件。
- 需要修改目标来源时，先改 `references/venue_matrix.yaml`，不要直接改检索脚本。
- 需要修改分类关键词时，改 `references/domain_keywords.yaml` 和 `references/method_keywords.yaml`。
- 对来源边界有疑问时，先读 `references/matching_policy.md`。
- 对输出字段含义有疑问时，读 `references/output_schema.md`。
