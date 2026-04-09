#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export HK_TRACKER_API_PORT="${HK_TRACKER_API_PORT:-5050}"

if [ -x ".venv/bin/python" ]; then
	exec .venv/bin/python api_server.py "$@"
fi

exec python3 api_server.py "$@"
