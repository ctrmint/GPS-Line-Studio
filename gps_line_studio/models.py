"""GUI-independent models; coordinates are latitude then longitude (EPSG:4326)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import asin, cos, isfinite, radians, sin, sqrt
from uuid import uuid4

MAX_WEB_MERCATOR_LAT = 85.05112878
EARTH_RADIUS_M = 6371008.8  # mean spherical Earth radius; length is an estimate


@dataclass(frozen=True)
class GeoPoint:
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not (isfinite(self.latitude) and isfinite(self.longitude)):
            raise ValueError("Coordinates must be finite numbers")
        if not (-MAX_WEB_MERCATOR_LAT <= self.latitude <= MAX_WEB_MERCATOR_LAT):
            raise ValueError("Latitude must be inside the Web Mercator map bounds (±85.05112878°)")
        if not (-180 <= self.longitude <= 180):
            raise ValueError("Longitude must be between -180° and 180°")

    def to_dict(self) -> dict:
        return {"latitude": self.latitude, "longitude": self.longitude}

    @classmethod
    def from_dict(cls, value: dict) -> "GeoPoint":
        if not isinstance(value, dict):
            raise ValueError("Invalid coordinate object")
        # Reject booleans, which Python considers numbers.
        for key in ("latitude", "longitude"):
            if isinstance(value.get(key), bool) or not isinstance(value.get(key), (int, float)):
                raise ValueError(f"{key} must be numeric")
        return cls(float(value["latitude"]), float(value["longitude"]))


def straight_line_distance_m(start: GeoPoint, end: GeoPoint) -> float:
    """Spherical haversine distance, not a snapped road distance."""
    dlat = radians(end.latitude - start.latitude)
    dlon = radians(end.longitude - start.longitude)
    a = sin(dlat / 2) ** 2 + cos(radians(start.latitude)) * cos(radians(end.latitude)) * sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_M * asin(min(1.0, sqrt(a)))


@dataclass(frozen=True)
class LineRecord:
    id: str
    label: str
    start: GeoPoint
    end: GeoPoint
    created_at: str

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ValueError("Each line requires a label")
        if len(self.label) > 120:
            raise ValueError("Label must contain at most 120 characters")
        if self.start == self.end:
            raise ValueError("Start and end must be different locations")
        if not self.id or not self.created_at:
            raise ValueError("Line must have an ID and creation timestamp")

    @property
    def distance_m(self) -> float:
        return straight_line_distance_m(self.start, self.end)

    @classmethod
    def create(cls, label: str, start: GeoPoint, end: GeoPoint) -> "LineRecord":
        return cls(
            id=str(uuid4()),
            label=label.strip(),
            start=start,
            end=end,
            created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id, "label": self.label, "created_at": self.created_at,
            "start": self.start.to_dict(), "end": self.end.to_dict(),
            "straight_line_distance_m": round(self.distance_m, 3),
        }

    @classmethod
    def from_dict(cls, value: dict) -> "LineRecord":
        if not isinstance(value, dict):
            raise ValueError("Invalid line record")
        return cls(
            id=str(value["id"]),
            label=value["label"],
            created_at=str(value["created_at"]),
            start=GeoPoint.from_dict(value["start"]),
            end=GeoPoint.from_dict(value["end"]),
        )
