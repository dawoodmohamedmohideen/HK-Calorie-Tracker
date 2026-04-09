#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -x ".venv/bin/streamlit" ]; then
	exec .venv/bin/streamlit run streamlit_app.py "$@"
fi

if [ -x ".venv/bin/python" ]; then
	exec .venv/bin/python -m streamlit run streamlit_app.py "$@"
fi

exec streamlit run streamlit_app.py "$@"
