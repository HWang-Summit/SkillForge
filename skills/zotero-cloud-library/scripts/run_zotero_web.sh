#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

load_skillforge_env() {
  local file="${SKILLFORGE_ENV_FILE:-$HOME/.skillforge/env}"
  local line key value

  [[ -f "$file" ]] || return 0

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="$(trim "$line")"
    [[ -z "$line" || "$line" == \#* ]] && continue

    if [[ "$line" == export[[:space:]]* ]]; then
      line="$(trim "${line#export}")"
    fi

    [[ "$line" == *=* ]] || continue
    key="$(trim "${line%%=*}")"
    value="$(trim "${line#*=}")"

    [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue

    if [[ ${#value} -ge 2 ]]; then
      if [[ "${value:0:1}" == "'" && "${value: -1}" == "'" ]]; then
        value="${value:1:${#value}-2}"
      elif [[ "${value:0:1}" == '"' && "${value: -1}" == '"' ]]; then
        value="${value:1:${#value}-2}"
      fi
    fi

    export "$key=$value"
  done < "$file"
}

expand_path() {
  local value="$1"
  if [[ "$value" == '$HOME/'* ]]; then
    value="$HOME/${value#'$HOME/'}"
  elif [[ "$value" == "~/"* ]]; then
    value="$HOME/${value#"~/"}"
  fi
  printf '%s\n' "$value"
}

select_python() {
  local candidate

  if [[ -n "${ZOTERO_PYTHON:-}" ]]; then
    candidate="$(expand_path "$ZOTERO_PYTHON")"
    if [[ -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
    echo "ZOTERO_PYTHON is set but not executable: $ZOTERO_PYTHON" >&2
    return 1
  fi

  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi

  if command -v python >/dev/null 2>&1; then
    command -v python
    return 0
  fi

  echo "No usable Python found. Set ZOTERO_PYTHON in \$HOME/.skillforge/env or install Python." >&2
  return 1
}

load_skillforge_env

PYTHON_CMD="$(select_python)"
exec "$PYTHON_CMD" "$SCRIPT_DIR/zotero_web.py" "$@"
