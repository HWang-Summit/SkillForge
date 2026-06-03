#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail=0

while IFS= read -r -d '' skill; do
  skill_name="$(basename "$skill")"
  skill_md="$skill/SKILL.md"
  if [[ ! -f "$skill_md" ]]; then
    echo "missing SKILL.md: $skill" >&2
    fail=1
    continue
  fi
  if ! sed -n '1,20p' "$skill_md" | grep -q '^name:'; then
    echo "missing frontmatter name: $skill_md" >&2
    fail=1
  fi
  if ! sed -n '1,20p' "$skill_md" | grep -q '^description:'; then
    echo "missing frontmatter description: $skill_md" >&2
    fail=1
  fi
  declared_name="$(awk '/^name:/ {print $2; exit}' "$skill_md" | tr -d '"')"
  if [[ "$declared_name" != "$skill_name" ]]; then
    echo "name mismatch: directory=$skill_name frontmatter=$declared_name" >&2
    fail=1
  fi
done < <(find "$ROOT/skills" -mindepth 1 -maxdepth 1 -type d -print0)

suite="$ROOT/suites/galaxypedia-suite.yaml"
if [[ -f "$suite" ]]; then
  while IFS= read -r ref; do
    [[ -z "$ref" ]] && continue
    if [[ ! -f "$ROOT/skills/galaxypedia-suite/references/$ref.md" ]]; then
      echo "suite reference missing: $ref" >&2
      fail=1
    fi
  done < <(awk '/included_modules:/ {flag=1; next} /shared_references:/ {flag=0} flag && /^  - / {print $2}' "$suite")

  if find "$ROOT/skills/galaxypedia-suite" -type f | grep -q 'mineru-import'; then
    echo "mineru-import should not be bundled in galaxypedia-suite" >&2
    fail=1
  fi
fi

if [[ "$fail" -ne 0 ]]; then
  exit 1
fi

echo "SkillForge validation passed."
