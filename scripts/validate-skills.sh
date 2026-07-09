#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail=0

err() {
  echo "$*" >&2
  fail=1
}

warn() {
  echo "warning: $*" >&2
}

while IFS= read -r -d '' skill; do
  skill_name="$(basename "$skill")"
  skill_md="$skill/SKILL.md"

  if [[ "$skill_name" == "_shared" ]]; then
    continue
  fi

  if [[ ! -f "$skill_md" ]]; then
    err "missing SKILL.md: $skill"
    continue
  fi

  if ! sed -n '1p' "$skill_md" | grep -qx -- '---'; then
    err "missing opening frontmatter marker: $skill_md"
  fi

  if ! sed -n '1,40p' "$skill_md" | grep -q '^name:'; then
    err "missing frontmatter name: $skill_md"
  fi

  if ! sed -n '1,80p' "$skill_md" | grep -q '^description:'; then
    err "missing frontmatter description: $skill_md"
  fi

  declared_name="$(awk '/^name:/ {print $2; exit}' "$skill_md" | tr -d '"')"
  if [[ "$declared_name" != "$skill_name" ]]; then
    err "name mismatch: directory=$skill_name frontmatter=$declared_name"
  fi

  if [[ -d "$skill/scripts" ]]; then
    if rg -n '(API[_-]?KEY|TOKEN|SECRET|CREDENTIAL)' "$skill/SKILL.md" "$skill/scripts" >/dev/null 2>/dev/null; then
      if ! rg -n '(\$HOME/\.skillforge/env|SKILLFORGE_ENV_FILE|load-skillforge-env|run_[A-Za-z0-9_-]+\.sh)' "$skill/SKILL.md" "$skill/scripts" >/dev/null 2>/dev/null; then
        warn "scripted skill mentions secrets but does not document SkillForge env/launcher: $skill_name"
      fi
    fi
  fi
done < <(find "$ROOT/skills" -mindepth 1 -maxdepth 1 -type d -print0)

required_galaxypedia=(
  galaxypedia-wiki
  galaxypedia-wiki-ingest
  galaxypedia-wiki-query
  galaxypedia-notion-literature-notes
  galaxypedia-wiki-lint
  galaxypedia-defuddle
  galaxypedia-zotero-ingest
  galaxypedia-mineru-import
  galaxypedia-json-canvas
  galaxypedia-karpathy-guidelines
  galaxypedia-suite
)

for skill in "${required_galaxypedia[@]}"; do
  [[ -f "$ROOT/skills/$skill/SKILL.md" ]] || err "missing Galaxypedia skill: $skill"
done

for ref in frontmatter templates obsidian-markdown; do
  [[ -f "$ROOT/skills/galaxypedia-wiki/references/$ref.md" ]] || err "missing Galaxypedia shared reference: $ref"
done

if [[ -d "$ROOT/skills/galaxypedia-suite/references" ]]; then
  err "galaxypedia-suite should not carry workflow references; use independent skills"
fi

[[ -f "$ROOT/skills/skillforge-sync-installed-skills/SKILL.md" ]] || err "missing skillforge-sync-installed-skills"
[[ -x "$ROOT/scripts/sync-installed-skills.sh" ]] || err "sync-installed-skills.sh is missing or not executable"

if [[ -f "$ROOT/skills/nature-writing/SKILL.md" ]]; then
  for ref in \
    core/reader-workflow.md \
    core/paper-type-taxonomy.md \
    core/ethics.md \
    core/terminology-ledger.md \
    journal-formats/nat-comms.md; do
    [[ -f "$ROOT/skills/_shared/$ref" ]] || err "missing nature-skills shared reference: skills/_shared/$ref"
  done
fi

private_path_pattern='/U''sers/'
if rg -n "$private_path_pattern" "$ROOT/skills" "$ROOT/README.md" "$ROOT/scripts" "$ROOT/suites" "$ROOT/config/skillforge.example.json" >/tmp/skillforge-private-paths.$$ 2>/dev/null; then
  cat /tmp/skillforge-private-paths.$$ >&2
  rm -f /tmp/skillforge-private-paths.$$
  err "private absolute paths found in tracked content"
else
  rm -f /tmp/skillforge-private-paths.$$
fi

if rg -n 'skills/(wiki-ingest|wiki-query|wiki-lint|defuddle|zotero-ingest|mineru-import|json-canvas|karpathy-guidelines)/SKILL\.md' "$ROOT/skills/galaxypedia-" >/tmp/skillforge-old-paths.$$ 2>/dev/null; then
  cat /tmp/skillforge-old-paths.$$ >&2
  rm -f /tmp/skillforge-old-paths.$$
  err "old Galaxypedia skill paths found"
else
  rm -f /tmp/skillforge-old-paths.$$
fi

if [[ "$fail" -ne 0 ]]; then
  exit 1
fi

echo "SkillForge validation passed."
