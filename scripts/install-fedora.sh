#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Installing GTK/libadwaita/libshumate dependencies (Fedora)..."
sudo dnf install -y python3 python3-gobject gtk4 libadwaita libshumate

BIN_DIR="${HOME}/.local/bin"
APP_DIR="${HOME}/.local/share/applications"
mkdir -p "$BIN_DIR" "$APP_DIR"

# Symbolic symlink: source can remain in the user's project directory.
ln -sfn "$HERE/scripts/launch.sh" "$BIN_DIR/gps-line-studio"
sed "s|^Exec=.*$|Exec=$BIN_DIR/gps-line-studio|" \
  "$HERE/data/io.github.gpslinestudio.GPSLineStudio.desktop" \
  > "$APP_DIR/io.github.gpslinestudio.GPSLineStudio.desktop"
# Desktop launch always calls the wrapper under ~/.local/bin.
chmod +x "$HERE/scripts/launch.sh"
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APP_DIR" || true
fi
printf '\nInstalled desktop launcher. Run: %s/gps-line-studio\n' "$BIN_DIR"
printf 'Or from repo: python3 run.py\n'
