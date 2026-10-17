import csv
import io
import json
import unittest

from gps_line_studio.exporters import CSV_FIELDS, to_csv, to_json
from gps_line_studio.models import GeoPoint, LineRecord


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.lines = [
            LineRecord.create("north-east", GeoPoint(54.1699821, -4.4468667), GeoPoint(54.1699239, -4.4470213)),
            LineRecord.create("=2+2", GeoPoint(54.170352, -4.4473125), GeoPoint(54.170298, -4.4474715)),
        ]

    def test_csv_fields(self):
        rows = list(csv.DictReader(io.StringIO(to_csv(self.lines))))
        self.assertEqual(len(rows), 2)
        self.assertEqual(list(rows[0]), CSV_FIELDS)
        self.assertEqual(rows[0]["start_latitude"], "54.169982100")
        self.assertEqual(rows[0]["crs"], "EPSG:4326")

    def test_csv_formula_sanitized(self):
        rows = list(csv.DictReader(io.StringIO(to_csv(self.lines))))
        self.assertEqual(rows[1]["label"], "'=2+2")

    def test_json_preserves_labels(self):
        result = json.loads(to_json(self.lines))
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["lines"][1]["label"], "=2+2")
        self.assertEqual(result["lines"][0]["start"]["latitude"], 54.1699821)


if __name__ == "__main__":
    unittest.main()
