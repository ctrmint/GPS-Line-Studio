# Troubleshooting

## `ModuleNotFoundError: No module named 'gi'`

Use `/usr/bin/python3` (system Python) and install `python3-gobject`:

```bash
sudo dnf install -y python3-gobject
/usr/bin/python3 run.py
```

Virtual environments and alternative Python distributions often cannot see the Fedora PyGObject packages.

## `Namespace Shumate not available` / `Namespace Adw not available`

```bash
sudo dnf install -y libshumate libadwaita
```

Fedora runtime packages provide the GI typelib files; no separate Python PyPI install is needed.

## App opens but no map tiles display

- Confirm working HTTPS network access and DNS.
- Verify system time and CA trust for TLS certificate validation.
- Check the terminal for tile-loading or TLS warnings.
- Check VPN/firewall/network policy if OSM's tile host is blocked.
- Do not disable TLS certificate checks.
- Check [OSM tile policy](https://operations.osmfoundation.org/policies/tiles/); improperly identified traffic may be rate-limited.
- No blanket offline map is bundled and public OSM servers do not permit bulk offline prefetch.

## Cannot pan map

Turn **Draw line** off. The transparent canvas intentionally captures pointer events while drawing; navigate with normal pan when drawing is off. Zoom +/- works in both modes.

## Wrong coordinates / line doesn't align

- Confirm latitude, then longitude. Check western longitudes are negative.
- Zoom in and retry, or use Edit to input exact numbers.
- Screen capture resolution and tile features can be less accurate than numeric precision.
- No road snapping is implemented.

## Missing/corrupted `lines.json`

The application refuses to overwrite incompatible or malformed saved data. Check the terminal output. Restore a backup or move the corrupted file to a safe name before starting with a blank database:

```bash
mv ~/.local/share/gps-line-studio/lines.json \
   ~/.local/share/gps-line-studio/lines.json.broken
```

If `$XDG_DATA_HOME` is set, the data directory may be different. Do not delete the broken file before examining/recovering it.

## Export fails

- Ensure write permission at the selected path.
- Export uses a **local file** destination; remote URI providers may be unsupported in v0.1.
- Disk full and permissions errors are shown in a toast.

## Opening from GNOME Activities fails

Run `~/.local/bin/gps-line-studio` from a terminal to see errors. Check the repository directory hasn't been moved after installing the desktop launcher; rerun `scripts/install-fedora.sh` to update it. The installer creates an absolute Exec path in the `.desktop` file.

## Reporting a bug

Include Fedora release, GTK/libadwaita/libshumate versions, reproducible actions and sanitized stderr output. **Remove private coordinates/labels** from logs before sharing them.
