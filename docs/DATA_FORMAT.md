# Data structures and interoperability

## CRS and ordering

Coordinate reference system: **EPSG:4326 (WGS84)**. Values are decimal degrees and always appear as **latitude first, longitude second** in both UI and exported named fields.

Longitude is negative for locations west of Greenwich; latitude is negative south of the Equator. Coordinates are finite and range-limited to latitude ±85.05112878° (the Web Mercator map extent) and longitude ±180°.

## Internal JSON

`lines.json` contains an object with `schema_version`, `coordinate_reference_system`, and `lines`. Example:

```json
{
  "schema_version": 1,
  "coordinate_reference_system": "EPSG:4326",
  "lines": [
    {
      "id": "626f6084-01fb-4a5a-bd8d-99536c2b6590",
      "label": "North driveway boundary",
      "created_at": "2026-10-17T15:00:00+00:00",
      "start": {"latitude": 54.1699821, "longitude": -4.4468667},
      "end": {"latitude": 54.1699239, "longitude": -4.4470213},
      "straight_line_distance_m": 11.964
    }
  ]
}
```

The distance in this example is illustrative. Line distance is recalculated from the stored endpoints; the exported distance field should not be treated as surveyed length.

## CSV

The single header row is:

```csv
id,label,created_at,start_latitude,start_longitude,end_latitude,end_longitude,straight_line_distance_m,crs
```

One row per line. Coordinates are formatted with nine decimal places; distance with three decimal places, in metres. `crs` is always `EPSG:4326`.

CSV labels that begin with spreadsheet formula metacharacters `=`, `+`, `-`, or `@` are prefixed with `'` for safer use in spreadsheet software. The original label is unchanged in JSON, the app and local storage.

## JSON export

JSON export has the same `lines` records as internal storage and additionally documents the line geometry. Numeric WGS84 values are preserved as JSON numbers (not strings). It is a bespoke line-record format, **not** GeoJSON. For GeoJSON, transform a segment to a `LineString` with `[longitude, latitude]` coordinate arrays as required by that standard.

## Import

Importing previously exported files is *not yet implemented* in v0.1. Copy/restore the internal `lines.json` file after quitting the application for backup/restore.
