#!/usr/bin/env bash
set -euo pipefail

# Project root
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

# Defaults
MODE="auto"           # auto | term | tmux | bg
ACTION="start"        # start | stop
WITH_ORCH="yes"       # yes | no
LOG_DIR="$ROOT_DIR/logs"
PID_FILE="$ROOT_DIR/.agent_pids"

# Parse args
for arg in "$@"; do
  case "$arg" in
    --mode=*) MODE="${arg#*=}" ;;
    --no-orchestrator) WITH_ORCH="no" ;;
    start) ACTION="start" ;;
    stop) ACTION="stop" ;;
    *) echo "Unknown arg: $arg" >&2; exit 1 ;;
  esac
done

# Auto-activate a local virtualenv if present (./.venv, ./venv, ./Attager)
if [ -z "${VIRTUAL_ENV:-}" ]; then
  for VENV_DIR in ".venv" "venv" "Attager"; do
    if [ -f "$ROOT_DIR/$VENV_DIR/bin/activate" ]; then
      set +u
      . "$ROOT_DIR/$VENV_DIR/bin/activate"
      set -u
      break
    fi
  done
fi

# Resolve Python interpreter robustly (supports virtualenv)
if [ -n "${PYTHON:-}" ]; then
  PYTHON_COMMAND="$PYTHON"
elif [ -n "${VIRTUAL_ENV:-}" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
  PYTHON_COMMAND="$VIRTUAL_ENV/bin/python"
else
  PYTHON_COMMAND="$(command -v python3 || true)"
  if [ -z "$PYTHON_COMMAND" ]; then
    PYTHON_COMMAND="$(command -v python || true)"
  fi
fi
if [ -z "$PYTHON_COMMAND" ]; then
  echo "Python interpreter not found. Set PYTHON=/path/to/python and re-run." >&2
  exit 1
fi

MODULES=(
  "agents.delivery_agent:Delivery Agent"
  "agents.item_agent:Item Agent"
  "agents.vehicle_agent:Vehicle Agent"
  "agents.qulity_agent:Quality Agent"
)
if [ "$WITH_ORCH" = "yes" ]; then
  MODULES=( "Orchestrator_new:Orchestrator" "${MODULES[@]}" )
fi

start_bg() {
  mkdir -p "$LOG_DIR"
  rm -f "$PID_FILE"
  for entry in "${MODULES[@]}"; do
    module_name="${entry%%:*}"
    title="${entry#*:}"
    echo "Starting $module_name (bg)..."
    nohup "$PYTHON_COMMAND" -m "$module_name" >"$LOG_DIR/${module_name//./_}.log" 2>&1 &
    echo "$! $module_name" >> "$PID_FILE"
  done
  echo "Started in background. PIDs in $PID_FILE; logs in $LOG_DIR"
}

stop_bg() {
  if [ -f "$PID_FILE" ]; then
    while read -r pid _; do kill "$pid" 2>/dev/null || true; done < "$PID_FILE"
    rm -f "$PID_FILE"
    echo "Stopped background processes."
  else
    # Fallback by pattern
    pkill -f Orchestrator_new 2>/dev/null || true
    pkill -f agents.delivery_agent 2>/dev/null || true
    pkill -f agents.item_agent 2>/dev/null || true
    pkill -f agents.vehicle_agent 2>/dev/null || true
    pkill -f agents.qulity_agent 2>/dev/null || true
  fi
}

start_tmux() {
  if ! command -v tmux >/dev/null 2>&1; then
    echo "tmux not found; use --mode=bg or install tmux." >&2
    exit 1
  fi
  if tmux has-session -t agents 2>/dev/null; then
    echo "Using existing tmux session 'agents'"
  else
    tmux new-session -d -s agents -n "${MODULES[0]#*:}" "$PYTHON_COMMAND -m ${MODULES[0]%%:*}"
  fi
  for entry in "${MODULES[@]:1}"; do
    module_name="${entry%%:*}"
    title="${entry#*:}"
    tmux new-window -t agents: -n "$title" "$PYTHON_COMMAND -m $module_name"
  done
  echo "tmux session 'agents' ready. Attach: tmux attach -t agents"
}

start_term() {
  if [ -z "${DISPLAY:-}" ]; then
    echo "DISPLAY not set; GUI terminals unavailable. Use --mode=tmux or --mode=bg." >&2
    exit 1
  fi
  open_term() {
    local title="$1"; shift
    local cmd="$*"
    if command -v gnome-terminal >/dev/null 2>&1; then
      gnome-terminal --title="$title" -- bash -lc "$cmd; exec bash" &
      return 0
    elif command -v konsole >/dev/null 2>&1; then
      konsole --new-window -p tabtitle="$title" -e bash -lc "$cmd; exec bash" &
      return 0
    elif command -v xterm >/dev/null 2>&1; then
      xterm -T "$title" -e bash -lc "$cmd; exec bash" &
      return 0
    fi
    return 1
  }
  for entry in "${MODULES[@]}"; do
    module_name="${entry%%:*}"
    title="${entry#*:}"
    echo "Starting $module_name in new terminal..."
    open_term "$title" "$PYTHON_COMMAND -m $module_name" || {
      echo "No GUI terminal found; falling back to --mode=tmux" >&2
      start_tmux
      return
    }
  done
}

case "$ACTION" in
  start)
    case "$MODE" in
      auto)
        if [ -n "${DISPLAY:-}" ] && { command -v gnome-terminal >/dev/null 2>&1 || command -v konsole >/dev/null 2>&1 || command -v xterm >/dev/null 2>&1; }; then
          start_term
        elif command -v tmux >/dev/null 2>&1; then
          start_tmux
        else
          start_bg
        fi
        ;;
      term) start_term ;;
      tmux) start_tmux ;;
      bg) start_bg ;;
      *) echo "Unknown mode: $MODE" >&2; exit 1 ;;
    esac
    ;;
  stop)
    if tmux has-session -t agents 2>/dev/null; then
      tmux kill-session -t agents || true
      echo "Killed tmux session 'agents'"
    fi
    stop_bg
    ;;
  *) echo "Unknown action: $ACTION" >&2; exit 1 ;;
esac

