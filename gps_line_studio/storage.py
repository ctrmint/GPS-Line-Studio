"""Atomic, private JSON persistence in XDG_DATA_HOME."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from .models import LineRecord

SCHEMA_VERSION = 1


def default_data_file() -> Path:
    base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "gps-line-studio" / "lines.json"


class LineStore:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path is not None else default_data_file()
        self.lines: list[LineRecord] = self.load()

    def load(self) -> list[LineRecord]:
        if not self.path.exists():
            return []
        content = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(content, dict) or content.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("Unsupported or invalid stored data format")
        if not isinstance(content.get("lines"), list):
            raise ValueError("Stored lines are invalid")
        lines = [LineRecord.from_dict(item) for item in content["lines"]]
        if len({x.id for x in lines}) != len(lines):
            raise ValueError("Stored line IDs are duplicated")
        return lines

    def _save(self, new_lines: list[LineRecord]) -> None:
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "coordinate_reference_system": "EPSG:4326",
            "lines": [line.to_dict() for line in new_lines],
        }
        temporary_name = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.path.parent,
                prefix=".lines-", suffix=".tmp", delete=False,
            ) as fh:
                temporary_name = fh.name
                os.chmod(temporary_name, 0o600)
                json.dump(payload, fh, ensure_ascii=False, indent=2, allow_nan=False)
                fh.write("\n")
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(temporary_name, self.path)
        finally:
            if temporary_name and os.path.exists(temporary_name):
                os.unlink(temporary_name)

    def upsert(self, line: LineRecord) -> None:
        updated = [line if item.id == line.id else item for item in self.lines]
        if not any(item.id == line.id for item in self.lines):
            updated.append(line)
        self._save(updated)
        self.lines = updated

    def remove(self, line_id: str) -> None:
        updated = [line for line in self.lines if line.id != line_id]
        if len(updated) == len(self.lines):
            raise KeyError(f"Line not found: {line_id}")
        self._save(updated)
        self.lines = updated
