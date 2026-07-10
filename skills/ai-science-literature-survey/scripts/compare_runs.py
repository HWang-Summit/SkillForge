#!/usr/bin/env python3
"""Compare two strict literature survey output directories."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def read_table(run_dir: Path, name: str) -> pd.DataFrame:
    path = run_dir / "最终交付版" / name
    if not path.exists():
        raise SystemExit(f"Missing {path}")
    return pd.read_csv(path).fillna("")


def record_key(row: pd.Series) -> str:
    doi = str(row.get("doi", "")).strip().lower()
    if doi:
        return "doi:" + doi
    return "title:" + str(row.get("title", "")).strip().lower()


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two strict literature survey runs.")
    parser.add_argument("--old", type=Path, required=True)
    parser.add_argument("--new", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    old_master = read_table(args.old, "最终主表.csv")
    new_master = read_table(args.new, "最终主表.csv")
    old_included = read_table(args.old, "严格纳入论文.csv")
    new_included = read_table(args.new, "严格纳入论文.csv")

    old_master_keys = {record_key(row) for _, row in old_master.iterrows()}
    old_included_keys = {record_key(row) for _, row in old_included.iterrows()}
    added_master = new_master[[record_key(row) not in old_master_keys for _, row in new_master.iterrows()]]
    added_included = new_included[[record_key(row) not in old_included_keys for _, row in new_included.iterrows()]]

    args.out.mkdir(parents=True, exist_ok=True)
    added_master.to_csv(args.out / "新增主表记录.csv", index=False, encoding="utf-8-sig")
    added_included.to_csv(args.out / "新增严格纳入论文.csv", index=False, encoding="utf-8-sig")

    lines = [
        "# 两次检索运行对比",
        "",
        f"- 旧运行：{args.old}",
        f"- 新运行：{args.new}",
        f"- 旧运行主表：{len(old_master)} 条",
        f"- 新运行主表：{len(new_master)} 条",
        f"- 旧运行严格纳入：{len(old_included)} 条",
        f"- 新运行严格纳入：{len(new_included)} 条",
        f"- 新增主表记录：{len(added_master)} 条",
        f"- 新增严格纳入论文：{len(added_included)} 条",
        "",
        "## 新增严格纳入领域分布",
        "",
        "| 领域 | 数量 |",
        "|---|---:|",
    ]
    for domain, count in added_included.get("primary_domain", pd.Series(dtype=str)).value_counts().items():
        lines.append(f"| {domain} | {int(count)} |")
    lines += ["", "## 新增严格纳入 Top 来源", "", "| 来源 | 数量 |", "|---|---:|"]
    for venue, count in added_included.get("target_venue_name", pd.Series(dtype=str)).value_counts().head(30).items():
        lines.append(f"| {venue} | {int(count)} |")
    (args.out / "对比报告.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote comparison outputs to {args.out}")


if __name__ == "__main__":
    main()
