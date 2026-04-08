#!/usr/bin/env bash
set -euo pipefail

export HK_TRACKER_API_PORT="${HK_TRACKER_API_PORT:-5050}"
python3 api_server.py
