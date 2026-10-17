# Development guide

## Stack and conventions

- Python 3.11+ (Fedora system Python recommended)
- GTK4 with libadwaita for native GNOME styling
- libshumate 1.0 GObject introspection (`gi.repository.Shumate`) for OSM rendering and map-projection operations
- No third-party pip dependencies, JavaScript or REST backend
- Application state contained in `LineStore`, model dataclasses immutable where possible
- `unittest` suite for pure functions and filesystem operations

## Developer environment

```bash
sudo dnf install -y python3 python3-gobject gtk4 libadwaita libshumate
/usr/bin/python3 -m unittest discover -s tests -v
/usr/bin/python3 -m compileall -q gps_line_studio
/usr/bin/python3 -m gps_line_studio
```

For VS Code on Fedora, select `/usr/bin/python3` as interpreter to use Fedora's GI packages. The workspace should be run from the repository root. A separate venv is usually unnecessary.

## Manual GUI smoke-test checklist

- [ ] Application launches from terminal without GLib/GTK critical warnings
- [ ] Tiles appear over HTTPS, © OpenStreetMap contributors is visible
- [ ] Wheel zoom/pan works with Draw line off
- [ ] Header +/- zoom works while drawing, map remains responsive
- [ ] Pointer coordinate display updates in Draw mode
- [ ] Click two points, save labelled line, see list and coloured segment
- [ ] Drag a second line and save a different label
- [ ] Select either line, centre map and see S/E markers
- [ ] Edit start/end numerical values and label; restart app to confirm persistence
- [ ] Export CSV and JSON; verify two rows / records and negative west longitude
- [ ] Cancel drawing, cancel editor, and cancel export without errors
- [ ] Delete a line, restart app, verify removal
- [ ] Test no network connection: existing data remains and new lines still save; no offline tile downloads
- [ ] Test loading invalid JSON after backing up: original data is not overwritten

## Roadmap

**v0.2 candidates:** draggable endpoint adjustment; copy-to-clipboard buttons; filter/search, undo, JSON import, per-line colouring, GPX/GeoJSON output; geodesic accuracy improvements using geographiclib; configurable default camera via settings.

**v0.3 candidates:** OSM road snapping, route matching, GIS overlay import and optional GNSS sensor input. These require separate routing/GIS data providers and accurate attribution/licensing. Keep them distinct from simple straight-line capture.

## Publishing to GitHub

```bash
cd gps-line-studio
git init
git add .
git commit -m "Initial GPS Line Studio GTK4 release"
git branch -M main
git remote add origin git@github.com:YOUR-ACCOUNT/gps-line-studio.git
git push -u origin main
```

Create the empty GitHub repo first, using your own account name. No GitHub remote is preconfigured in this archive. Update the application's `USER_AGENT` with a genuine project/contact link before distributing publicly.

## Design choices to revisit before wider release

- Test on the targeted Fedora GNOME and libshumate versions; UI cannot be exercised by pure-Python unit tests.
- Add an integration test that drives actual GTK pointer events under a virtual display.
- Consider packaging via Flatpak or RPM with desktop/icon resources and desktop-app metainfo.
- Consider automated linting, stronger schema migration support, and atomic-directory fsync for durability.
