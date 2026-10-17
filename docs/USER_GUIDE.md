# User guide

## Screen layout

- **Top bar:** Draw line / cancel, Go to coordinates (target), Zoom out, Zoom in
- **Map:** OpenStreetMap raster tiles, roads, existing coloured straight segments; red denotes the selected line and blue indicates other saved lines
- **Left panel:** saved line list, edit and delete actions, selected line detail, CSV/JSON export
- **Lower map bar:** attribution, coordinate reference system and live pointer latitude/longitude (when drawing)

## Navigate

With **Draw line OFF**, pan the map with the primary mouse button and zoom with the wheel or the header +/- controls. Use the target icon to centre on known decimal latitude/longitude. Map source tile zoom is limited to level 19. The initial centre is on the Isle of Man; you can navigate anywhere supported by the map service.

## Draw a line (two options)

**Option 1: two clicks**

1. Zoom as far as useful to locate the start position precisely.
2. Click **Draw line**.
3. Click the start location. A blue start dot appears, with a provisional orange line to the pointer.
4. Click the end location. The Save line dialog opens.
5. Enter a **label**; adjust start/end coordinates if necessary. Click **Save line**.

**Option 2: drag**

1. Click **Draw line**.
2. Press on the start location, drag at least five screen pixels to the endpoint, then release.
3. Label, optionally edit coordinates, and save.

During drawing, pointer events go to a transparent overlay, so ordinary dragging does **not** pan the map. Use the header +/- to zoom while drawing. Press **Esc** or click **Cancel drawing** to abandon the unfinished line.

## High-precision selection

- Zoom to level 18–19 to minimise the ground distance represented by each screen pixel.
- The pointer location display during drawing is decimal **latitude, longitude**.
- Coordinate values in the Save/Edit dialog have nine decimal places; edit them directly for exact numeric placement.
- Coordinates may be entered with a leading minus sign. **West longitude is negative**. Isle of Man longitude is approximately `-4.x`.
- Latitude must be within ±85.05112878° because this map uses Web Mercator, and longitude is within ±180°.
- An error message will prevent blank labels, identical endpoints, malformed/non-finite coordinates, and out-of-bounds values.

**Important:** The app does not use a GNSS receiver, cadastral dataset or surveying hardware. Numeric precision should not be mistaken for actual physical/survey accuracy. Line length is an approximate spherical straight-line distance, not route distance.

## Manage and inspect lines

Click any saved line to highlight it in orange/red, centre the map on it, and reveal **S** (start) and **E** (end) markers. The panel shows start and end latitude/longitude and straight-line length. The coordinate text is selectable for copying.

Click **Edit** to rename the line or correct either coordinate. Click **Delete** and confirm to remove a line. A unique ID is retained across edits. Changes automatically update local persistent storage.

## Export all lines

Click **Export CSV** or **Export JSON**. Enter a filename in the GNOME Save dialog. The exported file contains **all currently saved lines**, not only the selected line. The export filename is your choice; sensible defaults are `gps-lines.csv` and `gps-lines.json`.

See [Data Format](DATA_FORMAT.md) for CSV column names, WGS84 reference system and JSON structure.

## Persistence and backup

The application automatically saves in:

```text
~/.local/share/gps-line-studio/lines.json
```

Or under `$XDG_DATA_HOME/gps-line-studio/lines.json` if the variable is set. It does **not** share this information with OSM: only tile requests are sent over the network. Before replacing your computer or reinstalling Fedora, copy the file or export to JSON/CSV.

## Limitations

- Lines are direct two-point segments, not OSM road-following routes.
- No import, snapping, waypoint routing, measurement certification or live GPS receiver support in v0.1.
- The map needs online access for noncached tiles; do not use the public OSM server as an offline-tile download service.
- For very long international lines crossing the antimeridian, midpoint/visual line behaviour is optimised for short, local segments.
