#!/usr/bin/env bash
set -euo pipefail
rm -f "$HOME/.local/bin/gps-line-studio"
rm -f "$HOME/.local/share/applications/io.github.gpslinestudio.GPSLineStudio.desktop"
cat <<'MESSAGE'
Desktop launcher removed. The source directory and saved lines were preserved.
Saved data is normally in ~/.local/share/gps-line-studio/lines.json
MESSAGE
