"""Export labelled endpoint pairs to CSV or JSON."""

import csv
import io
import json

from .models import LineRecord

CSV_FIELDS = [
    "id", "label", "created_at", "start_latitude", "start_longitude",
    "end_latitude", "end_longitude", "straight_line_distance_m", "crs",
]


def _safe_csv_cell(value: str) -> str:
    """Stop untrusted labels being executed as formulas in spreadsheet software."""
    if value and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def to_csv(lines: list[LineRecord]) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(CSV_FIELDS)
    for line in lines:
        writer.writerow([
            line.id, _safe_csv_cell(line.label), line.created_at,
            format(line.start.latitude, ".9f"), format(line.start.longitude, ".9f"),
            format(line.end.latitude, ".9f"), format(line.end.longitude, ".9f"),
            format(line.distance_m, ".3f"), "EPSG:4326",
        ])
    return output.getvalue()


def to_json(lines: list[LineRecord]) -> str:
    return json.dumps({
        "schema_version": 1,
        "coordinate_reference_system": "EPSG:4326",
        "line_geometry": "straight segment between start and end; not road snapped",
        "lines": [line.to_dict() for line in lines],
    }, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
