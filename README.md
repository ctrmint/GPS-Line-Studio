# GPS Line Studio

**Native Fedora GNOME GPS endpoint annotation tool** built with **Python 3, GTK 4, libadwaita and libshumate**, displaying live OpenStreetMap (OSM) tiles.

Click twice or drag across the map to create a straight line. The application captures and labels the start and end GPS coordinates, displays the line on the map, saves multiple lines locally, and exports every saved line as CSV or JSON.

> **Important accuracy distinction:** Captured coordinates are exact floating-point results of the map viewport's pointer-to-WGS84 conversion, **not** surveyed ground-truth GPS measurements. Zoom to street level and use the manual coordinate editor for finer placement. This draws straight segments; it does not follow roads, snap to OSM ways, or calculate a road route.

## Features

- Native GNOME/GTK4 application with libadwaita header and toast messages
- Interactive OpenStreetMap raster map, pan, scroll-wheel zoom, dedicated +/- zoom controls
- Zoom to OSM standard tile level 19 for fine endpoint placement
- Create lines by click-start/click-end **or** click-and-drag
- Real-time pointer coordinates during drawing
- Automatic start/end extraction using `Shumate.Viewport.widget_coords_to_location()`
- Line labels; each record has a unique UUID and creation time
- Select saved lines; start/end markers (S and E), coordinates and approximate line length
- Edit labels **and** exact decimal latitude/longitude values after drawing
- Persistent, atomic, local JSON storage with restrictive file permissions
- CSV or JSON export; CSV labels protected against spreadsheet formula execution
- Explicit OSM attribution and identifiable User-Agent, libshumate on-disk tile caching
- No API keys, paid map services, web browser or JavaScript required

## Quick start (Fedora GNOME)

```bash
unzip gps-line-studio.zip
cd gps-line-studio
sudo dnf install -y python3 python3-gobject gtk4 libadwaita libshumate
/usr/bin/python3 run.py
```

Optional desktop launcher:

```bash
bash scripts/install-fedora.sh
```

Then launch **GPS Line Studio** from GNOME Activities or run `~/.local/bin/gps-line-studio`. Installer leaves your data intact. `python3 -m gps_line_studio` also works from the repository root.

**Supported target:** Fedora Workstation 43 or later; GTK/libshumate APIs and RPM names were checked against current documentation, but runtime GUI testing on Fedora is still required. GUI start-up needs a running graphical GNOME/GTK session and network access for uncached map tiles.

## Use it

1. Pan and zoom to your area, or press the target icon to enter centre coordinates.
2. Select **Draw line**, then click the start and finish, or drag between them.
3. Enter a descriptive **label**, optionally refine coordinate numbers, and select **Save line**.
4. Repeat to build your collection. Select a line to see S/E endpoints and straight-line distance.
5. Choose **Export CSV** or **Export JSON** in the left panel to export **all** saved lines.

**Coordinate order:** `latitude, longitude`, decimal degrees (WGS84 / EPSG:4326). The CSV stores nine digits after the decimal for consistency. This is numeric representation precision, not a guarantee of geographical accuracy.

## Saved data

`~/.local/share/gps-line-studio/lines.json` (or `$XDG_DATA_HOME/gps-line-studio/lines.json`). Saved automatically on each create, edit or delete. Back up this file to preserve your collection. Map tiles live in libshumate's separate cache.

## Repository structure

```text
gps-line-studio/
├── README.md
├── LICENSE
├── run.py
├── gps_line_studio/
│   ├── __main__.py
│   ├── constants.py       # Tile source and application identity
│   ├── models.py          # WGS84 validation and line model
│   ├── storage.py         # XDG data and atomic persistence
│   ├── exporters.py       # CSV / JSON formats
│   └── ui.py              # GTK/libadwaita and libshumate map
├── docs/
│   ├── SETUP.md
│   ├── USER_GUIDE.md
│   ├── ARCHITECTURE.md
│   ├── DATA_FORMAT.md
│   ├── DEVELOPMENT.md
│   └── TROUBLESHOOTING.md
├── data/
│   └── io.github.gpslinestudio.GPSLineStudio.desktop
├── scripts/
│   ├── install-fedora.sh
│   ├── launch.sh
│   └── uninstall-fedora.sh
├── examples/             # Two example exports (not auto-loaded)
├── .github/workflows/     # Fedora CI for imports and unit tests
└── tests/
    ├── test_models.py
    ├── test_storage.py
    └── test_exporters.py
```

## Documentation

- [Install and configure on Fedora](docs/SETUP.md)
- [User guide and line drawing](docs/USER_GUIDE.md)
- [Architecture and coordinate transformation](docs/ARCHITECTURE.md)
- [Export structure and example schema](docs/DATA_FORMAT.md)
- [Development, testing and roadmap](docs/DEVELOPMENT.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## Tests

```bash
/usr/bin/python3 -m unittest discover -s tests -v
/usr/bin/python3 -m compileall -q gps_line_studio
```

Non-GUI test suite uses the Python standard library only. A graphical smoke test must be performed on Fedora Workstation; no GNOME display session was available in the build environment.

## OpenStreetMap usage and accuracy

Tiles: `https://tile.openstreetmap.org/{z}/{x}/{y}.png` rendered with libshumate (HTTPS). **© OpenStreetMap contributors**, see [copyright](https://www.openstreetmap.org/copyright). OSMF public tile servers have [usage rules](https://operations.osmfoundation.org/policies/tiles/); do not bulk-download, prefetch or distribute cached tiles. Set a genuine contact URL in `USER_AGENT` if publicly distributing a fork. The default app-specific user agent is `GPSLineStudio/0.1.0`.

Coordinates are taken from the map projection, which may be less accurate than the underlying road geometry or ground survey. No accuracy guarantee is implied by displaying nine decimal digits.

## Licence

Application source: **MIT** (see [LICENSE](LICENSE)). OpenStreetMap data and imagery are provided separately under their respective licensing terms.
