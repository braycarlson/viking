set windows-shell := ["cmd.exe", "/c"]

log := '.logs\viking.log'


# List every recipe
default:
    @just --list

# Lint, then run the test suite
check: lint test

# Delete the caches and compiled files
[script('uv', 'run', 'python')]
clean:
    import pathlib
    import shutil

    removed = 0

    for path in pathlib.Path('.').rglob('__pycache__'):
        if '.venv' in path.parts:
            continue

        shutil.rmtree(path, ignore_errors=True)
        removed = removed + 1

    for name in ('.pytest_cache', '.ruff_cache'):
        shutil.rmtree(name, ignore_errors=True)

    print(f'Removed {removed} __pycache__ director(ies).')

# Create config.ini from config.example.ini
config:
    @if exist config.ini (echo config.ini already exists.) else (copy /y config.example.ini config.ini)

# Lint every file, and apply the safe fixes
fix:
    uv run ruff check --fix .

# Lint every file
lint:
    uv run ruff check .

# Display the bot log
logs:
    @if exist {{log}} (type {{log}}) else (echo No log file yet.)

# Start the bot
run:
    uv run run.py

# Start the bot on the Pi, detached, under the respawn wrapper
[unix]
start:
    #!/usr/bin/env bash
    set -euo pipefail
    if pgrep -f 'viking/run[.]' > /dev/null; then
        echo 'Viking is already running.'
        pgrep -af 'viking/run[.]'

        exit 1
    fi
    mkdir -p {{justfile_directory()}}/.logs
    setsid {{justfile_directory()}}/run.sh >> {{justfile_directory()}}/.logs/crontab.txt 2>&1 < /dev/null &
    echo 'Viking started.'

# Report whether the bot is running on the Pi
[unix]
status:
    #!/usr/bin/env bash
    if pgrep -f 'viking/run[.]' > /dev/null; then
        echo 'RUNNING'
        pgrep -af 'viking/run[.]'
    else
        echo 'STOPPED'
    fi

# Stop the bot on the Pi, and keep the wrapper from respawning it
[unix]
stop:
    #!/usr/bin/env bash
    set -uo pipefail
    touch {{justfile_directory()}}/.stop
    pkill -f 'viking/run[.]py' && echo 'Viking is stopping.' || echo 'Viking is not running.'

# Install the dependencies from uv.lock
sync:
    uv sync

# Run the test suite
test *arguments:
    uv run pytest {{arguments}}

# Upgrade the locked dependencies
upgrade:
    uv lock --upgrade

# Empty the bot log
wipe:
    @if exist {{log}} (type nul > {{log}})
