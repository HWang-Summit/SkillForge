#!/usr/bin/env python3
"""Validate Chinese strict literature survey outputs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


DEFAULT_REGRESSION_TITLES = [
    "SpectralGPT: Spectral Remote Sensing Foundation Model",
    "Changen2: Multi-Temporal Remote Sensing Generative Change Foundation Model",
    "Closer to Biological Mechanism: Drug-Drug Interaction Prediction from the Perspective of Pharmacophore",
]

REQUIRED_COLUMNS = {
    "title",
    "abstract",
    "authors",
    "year",
    "venue_or_journal",
    "target_venue_key",
    "target_venue_name",
    "target_venue_type",
    "venue_match_status",
    "primary_domain",
    "screening_status",
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate strict literature survey outputs.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--regression-title", action="append")
    args = parser.parse_args()

    final_dir = args.output_dir / "最终交付版"
    master_path = final_dir / "最终主表.csv"
    included_path = final_dir / "严格纳入论文.csv"
    xlsx_path = final_dir / "最终分类表.xlsx"
    errors: list[str] = []

    if not master_path.exists():
        fail(errors, f"缺少最终主表: {master_path}")
    if not included_path.exists():
        fail(errors, f"缺少严格纳入论文表: {included_path}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(1)

    master = pd.read_csv(master_path).fillna("")
    included = pd.read_csv(included_path).fillna("")

    missing = sorted(REQUIRED_COLUMNS - set(master.columns))
    if missing:
        fail(errors, "最终主表缺少字段: " + ", ".join(missing))
    missing_inc = sorted(REQUIRED_COLUMNS - set(included.columns))
    if missing_inc:
        fail(errors, "严格纳入论文表缺少字段: " + ", ".join(missing_inc))

    if "venue_match_status" in included:
        bad = included[~included["venue_match_status"].isin(["exact", "alias", "manual_verified"])]
        if len(bad):
            fail(errors, f"存在非法 venue_match_status: {len(bad)} 条")

    if "venue_or_journal" in included:
        checks = {
            "Remote Sensing": included["venue_or_journal"].astype(str).str.fullmatch("Remote Sensing", case=False).sum(),
            "BMC Bioinformatics": included["venue_or_journal"].astype(str).str.fullmatch("BMC Bioinformatics", case=False).sum(),
            "Scientific Reports": included["venue_or_journal"].astype(str).str.fullmatch("Scientific Reports", case=False).sum(),
            "arXiv venue": included["venue_or_journal"].astype(str).str.contains("arxiv", case=False).sum(),
        }
        for source, count in checks.items():
            if int(count):
                fail(errors, f"禁止来源进入严格纳入集: {source} = {int(count)}")

    titles = args.regression_title or DEFAULT_REGRESSION_TITLES
    if "title" in included:
        for title in titles:
            if int(included["title"].astype(str).str.contains(title, case=False, regex=False).sum()) == 0:
                fail(errors, f"重点论文未进入严格纳入集: {title}")

    if xlsx_path.exists():
        try:
            pd.ExcelFile(xlsx_path)
        except Exception as exc:
            fail(errors, f"最终分类表不可读: {exc}")

    if errors:
        print("校验失败：", file=sys.stderr)
        print("\n".join(f"- {e}" for e in errors), file=sys.stderr)
        raise SystemExit(1)

    print(f"校验通过：主表 {len(master)} 条，严格纳入 {len(included)} 条。")


if __name__ == "__main__":
    main()
