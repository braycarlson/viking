#!/bin/bash

# Viking respawn wrapper.

readonly ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PYTHON="$ROOT/.venv/bin/python"
readonly SCRIPT="$ROOT/run.py"
readonly STOP="$ROOT/.stop"
readonly WRAPPER_LOG="$ROOT/.logs/wrapper.log"

# run.py creates .logs, but the wrapper logs before it ever runs.
mkdir -p "$(dirname "$WRAPPER_LOG")"

# Without this, print() to a redirected stdout is block-buffered and only
# reaches the log when run.py exits.
export PYTHONUNBUFFERED=1

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$WRAPPER_LOG"
}

network_wait() {
    while true; do
        sleep 1 && nc -dzw1 google.com 443 &> /dev/null && break
    done
}

# A fresh start (cron @reboot or `just start`) is never a stop.
rm -f "$STOP"

network_wait
log "wrapper started (pid $$)"

while true; do
    "$PYTHON" "$SCRIPT"
    code=$?
    log "run.py exited $code"

    if [ -f "$STOP" ]; then
        rm -f "$STOP"
        log "stop requested; wrapper exiting"
        break
    fi

    network_wait
    sleep 2
    log "respawning run.py"
done
