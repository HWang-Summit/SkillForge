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

select_python() {
  local conda_env="${MINERU_CONDA_ENV:-base}"
  local candidate conda_bin forced_python

  if [[ -n "${MINERU_PYTHON:-}" ]]; then
    forced_python="$MINERU_PYTHON"
    if [[ "$forced_python" == '$HOME/'* ]]; then
      forced_python="$HOME/${forced_python#'$HOME/'}"
    elif [[ "$forced_python" == "~/"* ]]; then
      forced_python="$HOME/${forced_python#"~/"}"
    fi

    if [[ -x "$forced_python" ]]; then
      printf '%s\n' "$forced_python"
      return 0
    fi
    echo "MINERU_PYTHON is set but not executable: $MINERU_PYTHON" >&2
    return 1
  fi

  for candidate in \
    "$HOME/miniconda3/bin/python" \
    "$HOME/mambaforge/bin/python" \
    "$HOME/miniforge3/bin/python"; do
    if [[ -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  if [[ -n "${CONDA_EXE:-}" && -x "$CONDA_EXE" ]]; then
    printf '%q run -n %q python\n' "$CONDA_EXE" "$conda_env"
    return 0
  fi

  conda_bin="$(command -v conda 2>/dev/null || true)"
  if [[ -n "$conda_bin" && -x "$conda_bin" ]]; then
    printf '%q run -n %q python\n' "$conda_bin" "$conda_env"
    return 0
  fi

  if command -v python >/dev/null 2>&1; then
    command -v python
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi

  echo "No usable Python found. Set MINERU_PYTHON in \$HOME/.skillforge/env or install conda/Python." >&2
  return 1
}

load_skillforge_env

PYTHON_CMD="$(select_python)"
echo "Selected Python command: $PYTHON_CMD" >&2

if [[ "$PYTHON_CMD" == conda\ run\ * ]]; then
  eval "exec $PYTHON_CMD \"\$SCRIPT_DIR/mineru_parse.py\" \"\$@\""
fi

exec "$PYTHON_CMD" "$SCRIPT_DIR/mineru_parse.py" "$@"
