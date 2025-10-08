#!/usr/bin/env bash

set -euo pipefail

# Resolve repo root (directory of this script) and cd there
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Pick Python interpreter: prefer venv, else python3, else python
PY="$ROOT_DIR/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PY="python3"
  elif command -v python >/dev/null 2>&1; then
    PY="python"
  else
    echo "Error: Python interpreter not found. Install python3 or create .venv first." >&2
    exit 1
  fi
fi

echo "Using Python: $PY"

# Helper to open a new terminal window and run a command
open_in_terminal() {
  local title="$1"
  shift
  local cmd="$*"

  if command -v gnome-terminal >/dev/null 2>&1; then
    gnome-terminal --title="$title" -- bash -lc "$cmd"
    return 0
  elif command -v xfce4-terminal >/dev/null 2>&1; then
    xfce4-terminal --title="$title" --hold -e "bash -lc '$cmd'"
    return 0
  elif command -v konsole >/dev/null 2>&1; then
    konsole --caption "$title" -e bash -lc "$cmd"
    return 0
  elif command -v mate-terminal >/dev/null 2>&1; then
    mate-terminal --title="$title" -- bash -lc "$cmd"
    return 0
  elif command -v tilix >/dev/null 2>&1; then
    tilix -t "$title" -e bash -lc "$cmd"
    return 0
  elif command -v xterm >/dev/null 2>&1; then
    xterm -T "$title" -hold -e bash -lc "$cmd"
    return 0
  fi

  return 1
}

# Build execution commands (activate venv if present)
ACTIVATE=""
if [[ -f "$ROOT_DIR/.venv/bin/activate" ]]; then
  ACTIVATE="source '$ROOT_DIR/.venv/bin/activate' && "
fi

CMD_AGENT="cd '$ROOT_DIR' && ${ACTIVATE}$PY -m customer_agent --host 0.0.0.0 --port 10006; exec bash"
CMD_ORCH="cd '$ROOT_DIR' && ${ACTIVATE}$PY '$ROOT_DIR/customer_orchestrator/__main__.py' --host 0.0.0.0 --port 10005; exec bash"

if open_in_terminal "customer-agent (10006)" "$CMD_AGENT"; then
  echo "Opened customer-agent in a new terminal."
else
  echo "No GUI terminal found. Running customer-agent in background (nohup)."
  nohup bash -lc "${CMD_AGENT%'; exec bash'}" > "$ROOT_DIR/customer_agent.out" 2>&1 &
fi

if open_in_terminal "orchestrator (10005)" "$CMD_ORCH"; then
  echo "Opened orchestrator in a new terminal."
else
  echo "No GUI terminal found. Running orchestrator in background (nohup)."
  nohup bash -lc "${CMD_ORCH%'; exec bash'}" > "$ROOT_DIR/orchestrator.out" 2>&1 &
fi

echo "Both services launched."
exit 0


