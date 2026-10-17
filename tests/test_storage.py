import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from gps_line_studio.models import GeoPoint, LineRecord
from gps_line_studio.storage import LineStore


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.file = Path(self.temp.name) / "data" / "lines.json"
        self.a = GeoPoint(54.17, -4.45)
        self.b = GeoPoint(54.171, -4.451)

    def test_creates_persists_reloads(self):
        store = LineStore(self.file)
        self.assertEqual(store.lines, [])
        line = LineRecord.create("First", self.a, self.b)
        store.upsert(line)
        self.assertEqual(LineStore(self.file).lines, [line])
        self.assertEqual(self.file.stat().st_mode & 0o777, 0o600)
        self.assertEqual(json.loads(self.file.read_text())["coordinate_reference_system"], "EPSG:4326")

    def test_update_without_duplicates(self):
        store = LineStore(self.file)
        line = LineRecord.create("First", self.a, self.b)
        store.upsert(line)
        store.upsert(LineRecord(line.id, "Changed", self.b, self.a, line.created_at))
        self.assertEqual(len(LineStore(self.file).lines), 1)
        self.assertEqual(LineStore(self.file).lines[0].label, "Changed")

    def test_remove(self):
        store = LineStore(self.file)
        line = LineRecord.create("First", self.a, self.b)
        store.upsert(line)
        store.remove(line.id)
        self.assertEqual(LineStore(self.file).lines, [])

    def test_bad_data_not_overwritten(self):
        self.file.parent.mkdir(parents=True)
        self.file.write_text('{"schema_version":999,"lines":[]}', encoding="utf-8")
        with self.assertRaises(ValueError):
            LineStore(self.file)
        self.assertIn('999', self.file.read_text())

    def test_duplicate_id_rejected(self):
        line = LineRecord.create("same", self.a, self.b)
        self.file.parent.mkdir(parents=True)
        self.file.write_text(json.dumps({"schema_version": 1, "lines": [line.to_dict(), line.to_dict()]}))
        with self.assertRaises(ValueError):
            LineStore(self.file)


if __name__ == "__main__":
    unittest.main()
