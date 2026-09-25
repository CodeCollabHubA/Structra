#!/usr/bin/env sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PORT="${PORT:-5000}"
export PORT

if [ ! -x .venv/bin/python ]; then
    python3 -m venv .venv
fi

if ! .venv/bin/python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    printf '%s\n' 'Structra needs Python 3.10 or newer. Install Python, then recreate .venv.' >&2
    exit 1
fi

if ! .venv/bin/python -c 'import flask' >/dev/null 2>&1; then
    .venv/bin/python -m pip install -r requirements.txt
fi

printf '\n%s\n%s\n\n' \
    "Structra is starting. Open http://127.0.0.1:$PORT in your browser." \
    'Keep this terminal open during your demo. Press Ctrl+C to stop.'
exec .venv/bin/python app.py
