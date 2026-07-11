#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

select_python() {
  local conda_env="${PDF_RENDER_CONDA_ENV:-base}"
  local candidate conda_bin forced_python

  if [[ -n "${PDF_RENDER_PYTHON:-}" ]]; then
    forced_python="$PDF_RENDER_PYTHON"
    if [[ "$forced_python" == '$HOME/'* ]]; then
      forced_python="$HOME/${forced_python#'$HOME/'}"
    elif [[ "$forced_python" == "~/"* ]]; then
      forced_python="$HOME/${forced_python#"~/"}"
    fi

    if [[ -x "$forced_python" ]]; then
      printf '%s\n' "$forced_python"
      return 0
    fi
    echo "PDF_RENDER_PYTHON is set but not executable: $PDF_RENDER_PYTHON" >&2
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

  echo "No usable Python found. Set PDF_RENDER_PYTHON or install conda/Python." >&2
  return 1
}

PYTHON_CMD="$(select_python)"
echo "Selected Python command: $PYTHON_CMD" >&2

if [[ "$PYTHON_CMD" == *\ run\ -n\ *\ python ]]; then
  eval "exec $PYTHON_CMD \"\$SCRIPT_DIR/render_pdf_contact_sheet.py\" \"\$@\""
fi

exec "$PYTHON_CMD" "$SCRIPT_DIR/render_pdf_contact_sheet.py" "$@"
