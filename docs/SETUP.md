# Setup guide: Fedora Workstation + GNOME

## Requirements

- Fedora Workstation **43, 44, or newer**, with a graphical GNOME session (Wayland or X11)
- Python 3 from Fedora packages; use **`/usr/bin/python3`**
- GTK 4, libadwaita 1.x, libshumate 1.x and GObject Introspection
- Internet connectivity to load OSM tiles not already in libshumate's cache
- No API keys, Node.js, web server, Flatpak, pip, developer toolchain or database server needed

## 1. Install RPM dependencies

```bash
sudo dnf upgrade --refresh
sudo dnf install -y python3 python3-gobject gtk4 libadwaita libshumate
```

The Fedora `libshumate` RPM includes the `Shumate-1.0.typelib`; `libadwaita` includes `Adw-1.typelib`. There is no separate `python3-shumate` dependency for this application.

Verify introspection versions:

```bash
/usr/bin/python3 - <<'PY'
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Shumate', '1.0')
from gi.repository import Gtk, Adw, Shumate
print('GTK', Gtk.get_major_version(), Gtk.get_minor_version())
print('libadwaita', Adw.get_major_version(), Adw.get_minor_version())
print('Shumate loaded:', Shumate.SimpleMap)
PY
```

**Avoid** using a Python virtual environment that lacks access to Fedora's system GI bindings, unless you explicitly configure it to inherit system packages.

## 2. Run without installing a desktop launcher

```bash
unzip gps-line-studio.zip
cd gps-line-studio
/usr/bin/python3 run.py
```

Or run `/usr/bin/python3 -m gps_line_studio` from within the source directory.

## 3. Optional: install a GNOME application menu entry

```bash
bash scripts/install-fedora.sh
```

This script installs RPM dependencies if needed, creates a symlink in `~/.local/bin`, and writes a `.desktop` file into `~/.local/share/applications`. The files remain in your extracted source directory; do **not** delete or move the source directory without reinstalling the launcher.

To launch:

```bash
~/.local/bin/gps-line-studio
```

Find "GPS Line Studio" in Activities. If GNOME hasn't indexed the icon yet, log out/in or launch directly from terminal.

Uninstall launcher **without deleting saved data**:

```bash
bash scripts/uninstall-fedora.sh
```

## 4. Change the initial centre or tile source

In `gps_line_studio/constants.py`:

- `INITIAL_LAT`, `INITIAL_LON`, `INITIAL_ZOOM` control the first map location
- `TILE_URL` controls tiles (custom source must match libshumate `{z}/{x}/{y}` style)
- `USER_AGENT` must identify the app and preferably give a real operator contact for public distribution

In the GUI, the target icon changes the map centre without editing source code.

If substituting another tile provider, verify its permission for reuse, cache rules, attribution, zoom range and licence. The bundled settings use only the official OSM Standard tiles.

## 5. Test

```bash
/usr/bin/python3 -m unittest discover -s tests -v
/usr/bin/python3 -m compileall -q gps_line_studio
```

Then use the [User Guide](USER_GUIDE.md) for a manual map test with live tiles.
