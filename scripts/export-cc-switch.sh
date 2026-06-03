#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST="$ROOT/dist"
rm -rf "$DIST"
mkdir -p "$DIST"

while IFS= read -r -d '' skill; do
  cp -R "$skill" "$DIST/$(basename "$skill")"
done < <(find "$ROOT/skills" -mindepth 1 -maxdepth 1 -type d -print0)

"$ROOT/scripts/validate-skills.sh"
echo "Exported cc-switch compatible skills to $DIST"
