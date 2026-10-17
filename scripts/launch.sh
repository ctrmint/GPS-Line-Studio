#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
cd "$APP_ROOT"
exec /usr/bin/python3 -m gps_line_studio "$@"
