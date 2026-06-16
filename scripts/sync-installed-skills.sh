#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$ROOT/skills"
CONFIG_LOCAL="$ROOT/config/skillforge.local.json"

apply=0
update_existing=0
write_inventory=0
cc_switch_skills_dir="${CC_SWITCH_SKILLS_DIR:-}"
galaxypedia_skills_dir="${GALAXYPEDIA_SKILLS_DIR:-}"
skip_names=(
  _shared
  galaxypedia-suite
  skillforge-sync-installed-skills
)

usage() {
  cat <<'USAGE'
Usage: bash scripts/sync-installed-skills.sh [options]

Options:
  --apply                         Copy missing installed skills into skills/
  --update-existing               With --apply, replace existing non-self-managed skills when hashes differ
  --inventory                     Write skill-inventory.json
  --cc-switch-skills-dir <path>   Installed cc-switch skills directory
  --galaxypedia-skills-dir <path> Galaxypedia source skills directory for inventory only
  --skip <name>                   Skip a skill name
  -h, --help                      Show this help
USAGE
}

json_value() {
  local key="$1"
  local file="$2"
  [[ -f "$file" ]] || return 1
  sed -nE 's/^[[:space:]]*"'"$key"'"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/p' "$file" | head -n 1
}

expand_home() {
  local value="$1"
  value="${value/#\~/$HOME}"
  value="${value//\$HOME/$HOME}"
  printf '%s\n' "$value"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply)
      apply=1
      shift
      ;;
    --update-existing)
      update_existing=1
      shift
      ;;
    --inventory)
      write_inventory=1
      shift
      ;;
    --cc-switch-skills-dir)
      cc_switch_skills_dir="$2"
      shift 2
      ;;
    --galaxypedia-skills-dir)
      galaxypedia_skills_dir="$2"
      shift 2
      ;;
    --skip)
      skip_names+=("$2")
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$cc_switch_skills_dir" ]]; then
  cc_switch_skills_dir="$(json_value cc_switch_skills_dir "$CONFIG_LOCAL" || true)"
fi
if [[ -z "$galaxypedia_skills_dir" ]]; then
  galaxypedia_skills_dir="$(json_value galaxypedia_skills_dir "$CONFIG_LOCAL" || true)"
fi
if [[ -z "$cc_switch_skills_dir" ]]; then
  cc_switch_skills_dir="$HOME/.cc-switch/skills"
fi

cc_switch_skills_dir="$(expand_home "$cc_switch_skills_dir")"
galaxypedia_skills_dir="$(expand_home "$galaxypedia_skills_dir")"

is_skipped() {
  local name="$1"
  local skip
  [[ "$name" == galaxypedia-* ]] && return 0
  for skip in "${skip_names[@]}"; do
    [[ "$name" == "$skip" ]] && return 0
  done
  return 1
}

dir_hash() {
  local dir="$1"
  (
    cd "$dir"
    find . -type d -name '__pycache__' -prune -o -type f ! -name '.DS_Store' ! -name '*.pyc' -print \
      | LC_ALL=C sort \
      | while IFS= read -r file; do shasum -a 256 "$file"; done \
      | shasum -a 256 \
      | awk '{print $1}'
  )
}

cleanup_generated_files() {
  local dir="$1"
  find "$dir" -type d -name '__pycache__' -prune -exec rm -rf {} +
  find "$dir" -type f \( -name '.DS_Store' -o -name '*.pyc' \) -delete
}

copy_skill() {
  local src="$1"
  local dst="$2"
  local name
  local tmp
  local private_path_pattern

  name="$(basename "$src")"
  tmp="$(mktemp -d)"
  private_path_pattern='/U''sers/'

  cp -R "$src" "$tmp/$name"
  cleanup_generated_files "$tmp/$name"
  if rg -n "$private_path_pattern" "$tmp/$name" >/tmp/skillforge-sync-private-paths.$$ 2>/dev/null; then
    cat /tmp/skillforge-sync-private-paths.$$ >&2
    rm -f /tmp/skillforge-sync-private-paths.$$
    rm -rf "$tmp"
    echo "refusing to sync $name because it contains private absolute paths" >&2
    return 1
  fi
  rm -f /tmp/skillforge-sync-private-paths.$$

  rm -rf "$dst"
  mkdir -p "$(dirname "$dst")"
  mv "$tmp/$name" "$dst"
  rm -rf "$tmp"
}

if [[ ! -d "$cc_switch_skills_dir" ]]; then
  cat >&2 <<EOF
Installed skills directory not found: $cc_switch_skills_dir

Configure it with one of:
- --cc-switch-skills-dir <path>
- CC_SWITCH_SKILLS_DIR=<path>
- config/skillforge.local.json copied from config/skillforge.example.json
EOF
  exit 1
fi

missing=()
changed=()
present=()
skipped=()
synced=()
updated=()

while IFS= read -r -d '' src; do
  name="$(basename "$src")"
  dst="$SKILLS_DIR/$name"

  if is_skipped "$name"; then
    skipped+=("$name")
    continue
  fi

  if [[ ! -f "$src/SKILL.md" ]]; then
    skipped+=("$name:no-SKILL.md")
    continue
  fi

  if [[ ! -d "$dst" ]]; then
    missing+=("$name")
    if [[ "$apply" -eq 1 ]]; then
      copy_skill "$src" "$dst"
      synced+=("$name")
    fi
    continue
  fi

  src_hash="$(dir_hash "$src")"
  dst_hash="$(dir_hash "$dst")"
  if [[ "$src_hash" != "$dst_hash" ]]; then
    changed+=("$name")
    if [[ "$apply" -eq 1 && "$update_existing" -eq 1 ]]; then
      copy_skill "$src" "$dst"
      updated+=("$name")
    fi
  else
    present+=("$name")
  fi
done < <(find "$cc_switch_skills_dir" -mindepth 1 -maxdepth 1 -type d -print0)

if [[ "$write_inventory" -eq 1 ]]; then
  inventory="$ROOT/skill-inventory.json"
  {
    printf '{\n'
    printf '  "version": 1,\n'
    printf '  "generated_by": "scripts/sync-installed-skills.sh",\n'
    printf '  "sources": {\n'
    printf '    "cc_switch_skills_dir": "$HOME/.cc-switch/skills"'
    if [[ -n "$galaxypedia_skills_dir" ]]; then
      printf ',\n    "galaxypedia_skills_dir": "configured-locally"'
    fi
    printf '\n  },\n'
    printf '  "skills": [\n'
    first=1
    while IFS= read -r skill; do
      [[ -f "$skill/SKILL.md" ]] || continue
      name="$(basename "$skill")"
      hash="$(dir_hash "$skill")"
      if [[ "$first" -eq 0 ]]; then
        printf ',\n'
      fi
      first=0
      printf '    {"name": "%s", "content_hash": "%s"}' "$name" "$hash"
    done < <(find "$SKILLS_DIR" -mindepth 1 -maxdepth 1 -type d -print | LC_ALL=C sort)
    printf '\n  ]\n'
    printf '}\n'
  } > "$inventory"
fi

echo "Installed skills directory: $cc_switch_skills_dir"
echo "Missing: ${missing[*]:-(none)}"
echo "Changed: ${changed[*]:-(none)}"
echo "Present: ${present[*]:-(none)}"
echo "Skipped: ${skipped[*]:-(none)}"
echo "Synced: ${synced[*]:-(none)}"
echo "Updated: ${updated[*]:-(none)}"
if [[ "$write_inventory" -eq 1 ]]; then
  echo "Inventory: skill-inventory.json"
fi
