#!/usr/bin/env python3
"""Run a strict target-venue AI-for-science literature survey.

This project-local skill script reuses the repository's existing retrieval
engine while moving venue/keyword choices into skill references.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parents[1]
REFERENCES_DIR = SKILL_DIR / "references"


def find_project_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "tools" / "target_venue_strict_literature_survey_2023_2026.py").exists():
            return parent
    raise SystemExit("Cannot locate project root containing tools/target_venue_strict_literature_survey_2023_2026.py")


PROJECT_ROOT = find_project_root()
TOOLS_DIR = PROJECT_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

try:
    import pandas as pd
except Exception as exc:  # pragma: no cover - exercised only in missing dependency envs.
    raise SystemExit(f"pandas is required for this survey workflow: {exc}") from exc

import target_venue_strict_literature_survey_2023_2026 as engine


DOMAIN_ALIASES = {
    "bio": "Bioinformatics",
    "bioinformatics": "Bioinformatics",
    "geospatial": "Geospatial & Earth Informatics",
    "geo": "Geospatial & Earth Informatics",
    "earth": "Geospatial & Earth Informatics",
    "astro": "Astroinformatics",
    "astroinformatics": "Astroinformatics",
    "cross": "Cross-domain",
    "cross-domain": "Cross-domain",
}

DEFAULT_REGRESSION_TITLES = [
    "SpectralGPT: Spectral Remote Sensing Foundation Model",
    "Changen2: Multi-Temporal Remote Sensing Generative Change Foundation Model",
    "Closer to Biological Mechanism: Drug-Drug Interaction Prediction from the Perspective of Pharmacophore",
]


def load_json_yaml(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_csv_arg(value: str | None) -> set[str]:
    if not value:
        return set()
    return {item.strip() for item in value.split(",") if item.strip()}


def resolve_dates(args: argparse.Namespace) -> tuple[str, str]:
    today = date.today()
    if args.date_from or args.date_to:
        date_from = args.date_from or f"{today.year - 3}-01-01"
        date_to = args.date_to or today.isoformat()
        return date_from, date_to
    if args.year_from or args.year_to:
        year_from = args.year_from or today.year - 3
        year_to = args.year_to or today.year
        date_from = f"{year_from}-01-01"
        date_to = today.isoformat() if year_to == today.year else f"{year_to}-12-31"
        return date_from, date_to
    return f"{today.year - 3}-01-01", today.isoformat()


def years_for_policy(policy: dict[str, Any], start_year: int, end_year: int) -> tuple[int, ...]:
    years = list(range(start_year, end_year + 1))
    kind = policy.get("type", "all")
    if kind == "odd_years":
        years = [y for y in years if y % 2 == 1]
    elif kind == "even_years":
        years = [y for y in years if y % 2 == 0]
    elif kind == "explicit":
        allowed = {int(y) for y in policy.get("years", [])}
        years = [y for y in years if y in allowed]
    return tuple(years)


def load_target_venues(date_from: str, date_to: str, args: argparse.Namespace) -> tuple[Any, ...]:
    data = load_json_yaml(args.venue_matrix)
    tiers = parse_csv_arg(args.tiers)
    venue_keys = parse_csv_arg(args.venues)
    domain_filters = {DOMAIN_ALIASES.get(x.lower(), x) for x in parse_csv_arg(args.domains)}
    start_year = int(date_from[:4])
    end_year = int(date_to[:4])
    venues = []
    for raw in data["venues"]:
        if tiers and raw["tier"] not in tiers:
            continue
        if venue_keys and raw["key"] not in venue_keys and raw["name"] not in venue_keys:
            continue
        if domain_filters and raw["bucket"] not in domain_filters:
            continue
        years = years_for_policy(raw.get("years_policy", {"type": "all"}), start_year, end_year)
        if not years:
            continue
        venues.append(
            engine.TargetVenue(
                key=raw["key"],
                name=raw["name"],
                venue_type=raw["type"],
                bucket=raw["bucket"],
                search_group=raw["search_group"],
                aliases=tuple(raw.get("aliases", [])),
                crossref_names=tuple(raw.get("crossref_names", [])),
                official_url=raw.get("official_url", ""),
                years=years,
                tier=raw.get("tier", "core"),
            )
        )
    return tuple(venues)


def configure_engine(args: argparse.Namespace, date_from: str, date_to: str, raw_dir: Path) -> None:
    domain_terms = load_json_yaml(args.domain_keywords)["domain_terms"]
    method_data = load_json_yaml(args.method_keywords)
    engine.DATE_FROM = date_from
    engine.DATE_TO = date_to
    engine.RETRIEVAL_DATE = date.today().isoformat()
    engine.OUT_DIR = raw_dir
    engine.REPORT_DIR = raw_dir / "reports"
    engine.MAXRECALL_MASTER = PROJECT_ROOT / "literature_keyword_maxrecall_outputs" / "literature_master_maxrecall.csv"
    engine.TARGET_VENUES = load_target_venues(date_from, date_to, args)
    engine.DOMAIN_TERMS = domain_terms
    engine.METHOD_TERMS = method_data["method_terms"]
    engine.COMPACT_METHOD_TERMS = method_data.get("compact_method_terms", method_data["method_terms"][:8])
    engine.SEED_EXPANSION_TERMS = method_data.get("seed_expansion_terms", [])


def filter_records_by_year(records: list[dict[str, Any]], date_from: str, date_to: str) -> list[dict[str, Any]]:
    start_year = int(date_from[:4])
    end_year = int(date_to[:4])
    filtered = []
    for record in records:
        try:
            year = int(str(record.get("year", "")).strip()[:4])
        except ValueError:
            filtered.append(record)
            continue
        if start_year <= year <= end_year:
            filtered.append(record)
    return filtered


def write_log(path: Path, event: str, **payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {"event": event, "date": date.today().isoformat(), **payload}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def pct(part: int, total: int) -> str:
    return "0.00%" if not total else f"{part / total * 100:.2f}%"


def table_counts(series: pd.Series, first: str = "项目", second: str = "数量") -> list[str]:
    lines = [f"| {first} | {second} | 占比 |", "|---|---:|---:|"]
    total = int(series.sum()) if len(series) else 0
    if not len(series):
        lines.append("| 无 | 0 | 0.00% |")
        return lines
    for key, value in series.items():
        lines.append(f"| {key} | {int(value)} | {pct(int(value), total)} |")
    return lines


def generate_chinese_release(output_dir: Path, raw_dir: Path, regression_titles: list[str]) -> None:
    final_dir = output_dir / "最终交付版"
    audit_dir = output_dir / "过程审计"
    final_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)

    master_src = raw_dir / "target_strict_master_all.csv"
    included_src = raw_dir / "target_strict_included_only.csv"
    if not master_src.exists() or not included_src.exists():
        raise SystemExit(f"Missing raw outputs under {raw_dir}; run retrieval first or provide an existing raw output directory.")

    copy_if_exists(master_src, final_dir / "最终主表.csv")
    copy_if_exists(included_src, final_dir / "严格纳入论文.csv")
    copy_if_exists(raw_dir / "target_strict_classified.xlsx", final_dir / "最终分类表.xlsx")
    copy_if_exists(raw_dir / "target_venue_year_coverage_report.md", audit_dir / "来源覆盖报告.md")
    copy_if_exists(raw_dir / "target_strict_venue_type_composition.md", audit_dir / "会议期刊占比报告.md")
    copy_if_exists(raw_dir / "target_strict_keyword_expansion_log.md", audit_dir / "关键词扩展记录.md")
    copy_if_exists(raw_dir / "target_strict_excluded_with_reasons.csv", audit_dir / "排除记录及原因.csv")
    copy_if_exists(raw_dir / "target_paper_regression_check.md", audit_dir / "重点论文回归检查.md")
    copy_if_exists(raw_dir / "target_strict_high_relevance_shortlist.md", audit_dir / "高相关论文清单.md")

    master = pd.read_csv(master_src).fillna("")
    included = pd.read_csv(included_src).fillna("")
    candidate_count = int(master["screening_status"].isin(["candidate", "manual_required"]).sum()) if "screening_status" in master else 0
    excluded_count = int((master["screening_status"] == "exclude").sum()) if "screening_status" in master else 0

    lines = [
        "# 最终文献调研分析摘要",
        "",
        f"- 报告日期：{date.today().isoformat()}",
        f"- 最终主表：`{final_dir / '最终主表.csv'}`",
        f"- 严格纳入论文：`{final_dir / '严格纳入论文.csv'}`",
        f"- 最终分类表：`{final_dir / '最终分类表.xlsx'}`",
        "",
        "## 结果概况",
        "",
        f"- 主表记录：{len(master)}",
        f"- 严格纳入记录：{len(included)}",
        f"- 候选或人工复核记录：{candidate_count}",
        f"- 排除记录：{excluded_count}",
        "",
        "## 严格纳入领域分布",
        "",
    ]
    if "primary_domain" in included:
        lines += table_counts(included["primary_domain"].value_counts(), "领域", "数量")
    lines += ["", "## 严格纳入来源类型分布", ""]
    if "target_venue_type" in included:
        lines += table_counts(included["target_venue_type"].value_counts(), "来源类型", "数量")
    if "target_venue_tier" in included:
        lines += ["", "## 严格纳入来源层级分布", ""]
        lines += table_counts(included["target_venue_tier"].value_counts(), "层级", "数量")
    if "target_venue_name" in included:
        lines += ["", "## 严格纳入 Top 来源", ""]
        lines += table_counts(included["target_venue_name"].value_counts().head(25), "来源", "数量")

    lines += ["", "## 重点论文回归检查", "", "| 论文 | 严格纳入命中数 |", "|---|---:|"]
    for title in regression_titles:
        count = int(included["title"].str.contains(title, case=False, regex=False).sum()) if "title" in included else 0
        lines.append(f"| {title} | {count} |")

    forbidden = {
        "Remote Sensing": int(included.get("venue_or_journal", pd.Series(dtype=str)).astype(str).str.fullmatch("Remote Sensing", case=False).sum()),
        "BMC Bioinformatics": int(included.get("venue_or_journal", pd.Series(dtype=str)).astype(str).str.fullmatch("BMC Bioinformatics", case=False).sum()),
        "Scientific Reports": int(included.get("venue_or_journal", pd.Series(dtype=str)).astype(str).str.fullmatch("Scientific Reports", case=False).sum()),
        "arXiv venue": int(included.get("venue_or_journal", pd.Series(dtype=str)).astype(str).str.contains("arxiv", case=False).sum()),
    }
    lines += ["", "## 禁止来源检查", "", "| 来源 | 严格纳入命中数 |", "|---|---:|"]
    for source, count in forbidden.items():
        lines.append(f"| {source} | {count} |")

    (final_dir / "最终分析摘要报告.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> None:
    output_dir = args.output_dir.resolve()
    raw_dir = output_dir / "过程审计" / "原始严格检索输出"
    log_path = output_dir / "过程审计" / "运行日志.jsonl"
    error_log = output_dir / "过程审计" / "错误日志.md"
    regression_titles = args.regression_title or DEFAULT_REGRESSION_TITLES
    date_from, date_to = resolve_dates(args)
    configure_engine(args, date_from, date_to, raw_dir)

    write_log(log_path, "start", date_from=date_from, date_to=date_to, venues=len(engine.TARGET_VENUES), output_dir=str(output_dir))

    if args.report_only or args.offline_from_cache or (args.resume and (raw_dir / "target_strict_master_all.csv").exists()):
        generate_chinese_release(output_dir, raw_dir, regression_titles)
        write_log(log_path, "report_only_complete")
        return

    try:
        all_records, rejected = engine.load_strict_seed()
        all_records = filter_records_by_year(all_records, date_from, date_to)
        coverage = [{
            "venue": "Current maxrecall seed",
            "venue_key": "seed",
            "venue_type": "seed",
            "year_range": f"{date_from}..{date_to}",
            "retrieval_round": "round_seed_current_maxrecall",
            "retrieval_source": "current maxrecall target-venue seed",
            "venue_filter": "strict target venue aliases",
            "query_text": "",
            "retrieval_status": "ok" if all_records else "missing",
            "records_collected": len(all_records),
            "missing_abstracts": sum(1 for r in all_records if not r.get("abstract")),
            "notes": f"rejected non-target seed records: {len(rejected)}",
        }]

        if not args.skip_official:
            official_records, official_coverage = engine.collect_official_list_only()
            all_records.extend(official_records)
            coverage.extend(official_coverage)
        else:
            coverage.append({
                "venue": "Official list enumeration",
                "venue_key": "official_skipped",
                "venue_type": "official/proceedings",
                "year_range": f"{date_from}..{date_to}",
                "retrieval_round": "round_0_official_enumeration",
                "retrieval_source": "official list",
                "venue_filter": "configured official pages",
                "query_text": "",
                "retrieval_status": "skipped",
                "records_collected": 0,
                "missing_abstracts": 0,
                "notes": "Skipped by command-line option.",
            })

        if not args.skip_crossref:
            crossref_records, crossref_coverage = engine.collect_crossref_target_venues(args.crossref_rows, args.max_queries_per_venue or None)
            all_records.extend(crossref_records)
            coverage.extend(crossref_coverage)

        all_records = filter_records_by_year(all_records, date_from, date_to)
        engine.write_outputs(all_records, rejected, coverage)
        generate_chinese_release(output_dir, raw_dir, regression_titles)
        write_log(log_path, "complete", raw_records=len(all_records), rejected=len(rejected))
    except Exception as exc:
        error_log.parent.mkdir(parents=True, exist_ok=True)
        error_log.write_text(f"# 错误日志\n\n{type(exc).__name__}: {exc}\n", encoding="utf-8")
        write_log(log_path, "error", error=f"{type(exc).__name__}: {exc}")
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run strict target-venue AI-for-science literature survey.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--date-from")
    parser.add_argument("--date-to")
    parser.add_argument("--year-from", type=int)
    parser.add_argument("--year-to", type=int)
    parser.add_argument("--tiers", default="core,tier1,tier2")
    parser.add_argument("--domains", default="")
    parser.add_argument("--venues", default="")
    parser.add_argument("--venue-matrix", type=Path, default=REFERENCES_DIR / "venue_matrix.yaml")
    parser.add_argument("--domain-keywords", type=Path, default=REFERENCES_DIR / "domain_keywords.yaml")
    parser.add_argument("--method-keywords", type=Path, default=REFERENCES_DIR / "method_keywords.yaml")
    parser.add_argument("--crossref-rows", type=int, default=40)
    parser.add_argument("--max-queries-per-venue", type=int, default=0)
    parser.add_argument("--skip-official", action="store_true")
    parser.add_argument("--skip-crossref", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--offline-from-cache", action="store_true")
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--regression-title", action="append")
    return parser


def main() -> None:
    run(build_parser().parse_args())


if __name__ == "__main__":
    main()
