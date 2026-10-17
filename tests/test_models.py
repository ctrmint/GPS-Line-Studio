import math
import unittest

from gps_line_studio.models import GeoPoint, LineRecord, straight_line_distance_m


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.a = GeoPoint(54.1699821, -4.4468667)
        self.b = GeoPoint(54.1699239, -4.4470213)

    def test_distance_identical_zero(self):
        self.assertEqual(straight_line_distance_m(self.a, self.a), 0)

    def test_short_distance(self):
        self.assertGreater(straight_line_distance_m(self.a, self.b), 10)
        self.assertLess(straight_line_distance_m(self.a, self.b), 14)

    def test_distance_symmetry(self):
        self.assertAlmostEqual(straight_line_distance_m(self.a, self.b), straight_line_distance_m(self.b, self.a))

    def test_create_validates_label(self):
        with self.assertRaises(ValueError):
            LineRecord.create("  ", self.a, self.b)

    def test_create_validates_endpoints(self):
        with self.assertRaises(ValueError):
            LineRecord.create("same", self.a, self.a)

    def test_lat_lon_outside_map(self):
        for lat, lon in [(90, 0), (-90, 0), (20, 181), (20, -181), (math.nan, 0), (0, math.inf)]:
            with self.subTest(lat=lat, lon=lon), self.assertRaises(ValueError):
                GeoPoint(lat, lon)

    def test_boolean_rejected(self):
        with self.assertRaises(ValueError):
            GeoPoint.from_dict({"latitude": True, "longitude": 0})

    def test_round_trip(self):
        line = LineRecord.create("Road east", self.a, self.b)
        self.assertEqual(line, LineRecord.from_dict(line.to_dict()))


if __name__ == "__main__":
    unittest.main()
