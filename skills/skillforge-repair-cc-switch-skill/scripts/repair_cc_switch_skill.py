#!/usr/bin/env python3
"""Repair missing support files for a single cc-switch-installed skill."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CONFIG_LOCAL = ROOT / "config" / "skillforge.local.json"

SKIP_NAMES = {
    ".git",
    ".github",
    ".DS_Store",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
}
SKIP_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".log",
    ".tmp",
    ".env",
}

RELATIVE_PATH_RE = re.compile(
    r"""(?P<path>(?:\.\./)+(?:[A-Za-z0-9_. -]+/)*[A-Za-z0-9_. -]+(?:\.[A-Za-z0-9_-]+)?)"""
)
PRIVATE_PATH_RE = re.compile(r"/U" r"sers/")
SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|token|secret|credential)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}"
)


@dataclass(frozen=True)
class CopyPlan:
    source: Path
    target: Path
    relative_target: Path
    reason: str
    kind: str


def expand_home(value: str) -> str:
    return value.replace("$HOME", str(Path.home())).replace("~", str(Path.home()), 1)


def json_value(key: str, file: Path) -> str | None:
    if not file.exists():
        return None
    try:
        data = json.loads(file.read_text())
    except json.JSONDecodeError:
        return None
    value = data.get(key)
    return str(value) if value else None


def resolve_cc_switch_skills_dir(cli_value: str | None) -> Path:
    value = cli_value or os.environ.get("CC_SWITCH_SKILLS_DIR") or json_value("cc_switch_skills_dir", CONFIG_LOCAL)
    if not value:
        value = "$HOME/.cc-switch/skills"
    return Path(expand_home(value)).resolve()


def run(cmd: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def clone_repo(repo_url: str, branch: str | None, work_dir: Path) -> Path:
    clone_dir = work_dir / "repo"
    cmd = ["git", "clone", "--depth", "1"]
    if branch:
        cmd.extend(["--branch", branch])
    cmd.extend([repo_url, str(clone_dir)])
    subprocess.run(cmd, check=True)
    return clone_dir.resolve()


def resolve_repo(args: argparse.Namespace, work_dir: Path) -> Path:
    if args.repo_path:
        repo_root = Path(expand_home(args.repo_path)).resolve()
        if not repo_root.exists():
            raise SystemExit(f"repo path not found: {repo_root}")
        return repo_root
    if not args.repo_url:
        raise SystemExit("one of --repo-url or --repo-path is required")
    return clone_repo(args.repo_url, args.branch, work_dir)


def find_upstream_skill(repo_root: Path, skill_name: str) -> Path:
    candidates = [repo_root / "skills" / skill_name]
    candidates.extend((repo_root / "plugins").glob(f"*/skills/{skill_name}"))
    for candidate in candidates:
        if (candidate / "SKILL.md").exists():
            return candidate.resolve()
    raise SystemExit(f"upstream skill not found: {skill_name}")


def is_probably_text(path: Path) -> bool:
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip", ".gz", ".ttf"}:
        return False
    try:
        chunk = path.read_bytes()[:4096]
    except OSError:
        return False
    return b"\0" not in chunk


def iter_text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and is_probably_text(path):
            files.append(path)
    return files


def reanchor_escaped_ref(raw: str, support_root: Path) -> Path:
    parts = [part for part in Path(raw).parts if part != ".."]
    return (support_root.joinpath(*parts)).resolve()


def extract_relative_refs(scan_root: Path, install_skill: Path, upstream_scan_root: Path | None = None) -> set[Path]:
    refs: set[Path] = set()
    support_root = install_skill.parent.resolve()
    upstream_scan_root = upstream_scan_root.resolve() if upstream_scan_root else scan_root.resolve()
    scan_root = scan_root.resolve()
    for file in iter_text_files(scan_root):
        try:
            text = file.read_text(errors="ignore")
        except OSError:
            continue
        current_dir = install_skill / file.parent.relative_to(upstream_scan_root)
        for match in RELATIVE_PATH_RE.finditer(text):
            raw = match.group("path").strip().rstrip(".,;:)]}'\"")
            if not raw.startswith("../"):
                continue
            resolved = (current_dir / raw).resolve()
            try:
                resolved.relative_to(support_root)
            except ValueError:
                resolved = reanchor_escaped_ref(raw, support_root)
            refs.add(resolved)
    return refs


def iter_copyable_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and not should_skip_path(path):
            files.append(path)
    return files


def build_skill_file_plan(upstream_skill: Path, installed_skill: Path) -> list[CopyPlan]:
    plans: list[CopyPlan] = []
    for source in iter_copyable_files(upstream_skill):
        relative = source.relative_to(upstream_skill)
        target = installed_skill / relative
        if target.exists():
            continue
        plans.append(
            CopyPlan(
                source=source,
                target=target,
                relative_target=Path(installed_skill.name) / relative,
                reason=f"missing installed skill file {relative}",
                kind="skill_file",
            )
        )
    return plans


def nearest_existing_source(repo_root: Path, upstream_skill: Path, installed_skill: Path, missing_target: Path) -> Path | None:
    rel_to_installed = missing_target.relative_to(installed_skill.parent)
    source_roots = [repo_root, repo_root / "skills"]

    for source_root in source_roots:
        direct = source_root / rel_to_installed
        if direct.exists():
            return direct

    # If a referenced file is missing, copy the nearest existing parent support directory.
    parts = rel_to_installed.parts
    for source_root in source_roots:
        for idx in range(len(parts), 0, -1):
            candidate = source_root.joinpath(*parts[:idx])
            if candidate.exists():
                return candidate

    # Plugin packaging may keep support dirs beside plugins/<name>/skills.
    plugin_root = upstream_skill.parents[2] if "plugins" in upstream_skill.parts else None
    if plugin_root:
        direct = plugin_root / rel_to_installed
        if direct.exists():
            return direct
        for idx in range(len(parts), 0, -1):
            candidate = plugin_root.joinpath(*parts[:idx])
            if candidate.exists():
                return candidate
    return None


def should_skip_path(path: Path) -> bool:
    return any(part in SKIP_NAMES for part in path.parts) or path.suffix in SKIP_SUFFIXES


def scan_for_private_or_secret(path: Path) -> list[str]:
    findings: list[str] = []
    paths = [path] if path.is_file() else [p for p in path.rglob("*") if p.is_file()]
    for file in paths:
        if should_skip_path(file):
            continue
        if not is_probably_text(file):
            continue
        text = file.read_text(errors="ignore")
        if PRIVATE_PATH_RE.search(text):
            findings.append(f"private path found: {file}")
        if SECRET_RE.search(text):
            findings.append(f"possible secret found: {file}")
    return findings


def copy_support(source: Path, target: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, target, ignore=shutil.ignore_patterns(*SKIP_NAMES, "*.pyc", "*.pyo", "*.log", "*.tmp"))
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def build_support_plan(repo_root: Path, upstream_skill: Path, installed_skill: Path, refs: set[Path]) -> list[CopyPlan]:
    plans: dict[Path, CopyPlan] = {}
    for target in sorted(refs):
        if target.exists():
            continue
        source = nearest_existing_source(repo_root, upstream_skill, installed_skill, target)
        if not source:
            continue
        rel_to_installed = target.relative_to(installed_skill.parent)
        source_root = repo_root / "skills"
        if source == source_root / rel_to_installed or str(source).startswith(str((source_root / rel_to_installed.parts[0]).resolve())):
            relative_target = source.relative_to(source_root)
        else:
            try:
                relative_target = source.relative_to(repo_root)
            except ValueError:
                relative_target = source.relative_to(upstream_skill.parents[2])
        target_path = installed_skill.parent / relative_target
        if target_path.exists():
            continue
        plans[target_path] = CopyPlan(
            source=source,
            target=target_path,
            relative_target=relative_target,
            reason=str(target.relative_to(installed_skill.parent)),
            kind="support_file",
        )
    return list(plans.values())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-url", help="Upstream Git repository URL")
    parser.add_argument("--repo-path", help="Already-cloned upstream repository path")
    parser.add_argument("--skill-name", required=True, help="Installed skill name under cc-switch skills")
    parser.add_argument("--branch", help="Optional branch/tag to clone")
    parser.add_argument("--cc-switch-skills-dir", help="cc-switch skills directory")
    parser.add_argument("--apply", action="store_true", help="Copy missing support files")
    parser.add_argument("--update-existing-support", action="store_true", help="Replace existing support paths")
    parser.add_argument("--update-existing-skill-files", action="store_true", help="Replace existing installed skill files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cc_skills_dir = resolve_cc_switch_skills_dir(args.cc_switch_skills_dir)
    installed_skill = cc_skills_dir / args.skill_name
    if not installed_skill.exists():
        raise SystemExit(f"installed skill not found: {installed_skill}")

    with tempfile.TemporaryDirectory(prefix="skillforge-repair-") as tmp:
        repo_root = resolve_repo(args, Path(tmp))
        upstream_skill = find_upstream_skill(repo_root, args.skill_name)
        try:
            commit = run(["git", "rev-parse", "HEAD"], cwd=repo_root)
        except subprocess.CalledProcessError:
            commit = "unknown"

        installed_refs = extract_relative_refs(installed_skill, installed_skill)
        upstream_refs = extract_relative_refs(upstream_skill, installed_skill, upstream_skill)
        refs = installed_refs | upstream_refs
        skill_plan = build_skill_file_plan(upstream_skill, installed_skill)
        support_plan = build_support_plan(repo_root, upstream_skill, installed_skill, refs)
        plan = skill_plan + support_plan

        print(f"repo_url: {args.repo_url or '(local repo)'}")
        print(f"repo_path: {repo_root}")
        print(f"upstream_commit: {commit}")
        print(f"installed_skill: {installed_skill}")
        print(f"upstream_skill: {upstream_skill.relative_to(repo_root.resolve())}")
        print(f"relative_refs_found: {len(refs)}")
        print(f"missing_skill_files_count: {len(skill_plan)}")
        print(f"missing_support_files_count: {len(support_plan)}")

        if not plan:
            print("missing_skill_files: (none)")
            print("missing_support_files: (none)")
            return 0

        print("missing_skill_files:")
        if skill_plan:
            for item in skill_plan:
                print(f"- copy {item.relative_target} -> {item.target}")
                print(f"  reason: {item.reason}")
        else:
            print("- (none)")

        print("missing_support_files:")
        if support_plan:
            for item in support_plan:
                print(f"- copy {item.relative_target} -> {item.target}")
                print(f"  reason: missing reference {item.reason}")
        else:
            print("- (none)")

        if not args.apply:
            print("dry_run: true")
            print("run with --apply to copy missing files")
            return 0

        copied: list[Path] = []
        skipped: list[str] = []
        for item in plan:
            update_existing = args.update_existing_skill_files if item.kind == "skill_file" else args.update_existing_support
            if item.target.exists() and not update_existing:
                skipped.append(f"exists: {item.target}")
                continue
            if item.target.exists() and update_existing:
                if item.target.is_dir():
                    shutil.rmtree(item.target)
                else:
                    item.target.unlink()

            findings = scan_for_private_or_secret(item.source)
            if findings:
                skipped.extend(findings)
                continue

            if should_skip_path(item.source):
                skipped.append(f"skipped unsafe source: {item.source}")
                continue

            copy_support(item.source, item.target)
            copied.append(item.target)

        print("copied:")
        for path in copied:
            print(f"- {path}")
        if not copied:
            print("- (none)")

        print("skipped:")
        for reason in skipped:
            print(f"- {reason}")
        if not skipped:
            print("- (none)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
