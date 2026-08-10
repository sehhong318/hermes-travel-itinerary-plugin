#!/usr/bin/env python3
"""Export canonical itinerary JSON to local JSON, CSV, or Markdown."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import tempfile
from pathlib import Path
from typing import Any

_COLUMNS: tuple[str, ...] = (
    "date",
    "time",
    "end_time",
    "name",
    "type",
    "status",
    "location",
    "notes",
    "map_url",
)


def _load_itinerary(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("trip"), dict):
        raise ValueError("source must contain a trip object")
    days = data.get("days")
    if not isinstance(days, list):
        raise ValueError("source must contain a days list")
    for day in days:
        if not isinstance(day, dict) or not isinstance(day.get("items"), list):
            raise ValueError("each day must contain an items list")
        if not isinstance(day.get("date"), str):
            raise ValueError("each day must contain a date")
        if any(not isinstance(item, dict) for item in day["items"]):
            raise ValueError("each itinerary item must be an object")
    return data


def _rows(data: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    for day in data["days"]:
        for item in day["items"]:
            row = {column: str(item.get(column, "")) for column in _COLUMNS}
            row["date"] = day["date"]
            rows.append(row)
    return rows


def _render(data: dict[str, Any], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    rows = _rows(data)
    buffer = io.StringIO()
    if output_format == "csv":
        writer = csv.DictWriter(buffer, fieldnames=_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        return buffer.getvalue()
    if output_format == "markdown":
        buffer.write("| " + " | ".join(_COLUMNS) + " |\n")
        buffer.write("| " + " | ".join("---" for _ in _COLUMNS) + " |\n")
        for row in rows:
            values = [
                row[column].replace("|", "\\|").replace("\r", " ").replace("\n", " ")
                for column in _COLUMNS
            ]
            buffer.write("| " + " | ".join(values) + " |\n")
        return buffer.getvalue()
    raise ValueError(f"unsupported format: {output_format}")


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_name = temporary.name
        os.replace(temporary_name, path)
    finally:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export itinerary JSON without modifying the canonical source."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--format", choices=("json", "csv", "markdown"), required=True
    )
    args = parser.parse_args()

    if args.source.resolve() == args.output.resolve():
        parser.error("output must differ from the canonical source")
    try:
        data = _load_itinerary(args.source)
        content = _render(data, args.format)
        _write_atomic(args.output, content)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(f"wrote {args.format}: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
