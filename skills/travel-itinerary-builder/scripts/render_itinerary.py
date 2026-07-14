#!/usr/bin/env python3
"""Render a validated itinerary JSON file as self-contained mobile HTML."""

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
ITEM_TYPES = {"transport", "hotel", "activity", "food", "buffer", "note"}
STATUSES = {"planned", "reserved", "confirmed", "optional"}


def fail(message: str) -> None:
    raise ValueError(message)


def require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{field} must be a non-empty string")
    return value.strip()


def optional_text(value: object, field: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        fail(f"{field} must be a string")
    return value.strip()


def parse_date(value: object, field: str) -> date:
    text = require_text(value, field)
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field} must use YYYY-MM-DD") from exc


def validate_https_url(value: object, field: str) -> str:
    text = optional_text(value, field)
    if not text:
        return ""
    parsed = urlparse(text)
    if parsed.scheme != "https" or not parsed.netloc:
        fail(f"{field} must be an absolute HTTPS URL")
    return text


def load_and_validate(path: Path) -> dict:
    def reject_constant(value: str) -> None:
        fail(f"non-finite JSON value is not allowed: {value}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        fail("root must be an object")

    trip = data.get("trip")
    days = data.get("days")
    if not isinstance(trip, dict):
        fail("trip must be an object")
    if not isinstance(days, list) or not days:
        fail("days must be a non-empty array")

    clean_trip = {
        "title": require_text(trip.get("title"), "trip.title"),
        "start": parse_date(trip.get("start"), "trip.start"),
        "end": parse_date(trip.get("end"), "trip.end"),
        "timezone": require_text(trip.get("timezone"), "trip.timezone"),
        "summary": optional_text(trip.get("summary"), "trip.summary"),
    }
    if clean_trip["end"] < clean_trip["start"]:
        fail("trip.end must not precede trip.start")

    clean_days = []
    seen_dates: set[date] = set()
    for day_index, raw_day in enumerate(days):
        prefix = f"days[{day_index}]"
        if not isinstance(raw_day, dict):
            fail(f"{prefix} must be an object")
        day_date = parse_date(raw_day.get("date"), f"{prefix}.date")
        if not clean_trip["start"] <= day_date <= clean_trip["end"]:
            fail(f"{prefix}.date is outside the trip range")
        if day_date in seen_dates:
            fail(f"duplicate day date: {day_date.isoformat()}")
        seen_dates.add(day_date)
        items = raw_day.get("items")
        if not isinstance(items, list):
            fail(f"{prefix}.items must be an array")

        clean_items = []
        for item_index, raw_item in enumerate(items):
            item_prefix = f"{prefix}.items[{item_index}]"
            if not isinstance(raw_item, dict):
                fail(f"{item_prefix} must be an object")
            item_type = require_text(raw_item.get("type"), f"{item_prefix}.type")
            status = require_text(raw_item.get("status"), f"{item_prefix}.status")
            if item_type not in ITEM_TYPES:
                fail(f"{item_prefix}.type must be one of {sorted(ITEM_TYPES)}")
            if status not in STATUSES:
                fail(f"{item_prefix}.status must be one of {sorted(STATUSES)}")
            start_time = require_text(raw_item.get("time"), f"{item_prefix}.time")
            end_time = optional_text(raw_item.get("end_time"), f"{item_prefix}.end_time")
            if TIME_RE.fullmatch(start_time) and end_time and TIME_RE.fullmatch(end_time):
                if end_time < start_time:
                    fail(f"{item_prefix}.end_time precedes time")
            clean_items.append(
                {
                    "time": start_time,
                    "end_time": end_time,
                    "name": require_text(raw_item.get("name"), f"{item_prefix}.name"),
                    "type": item_type,
                    "location": optional_text(raw_item.get("location"), f"{item_prefix}.location"),
                    "local_name": optional_text(raw_item.get("local_name"), f"{item_prefix}.local_name"),
                    "notes": optional_text(raw_item.get("notes"), f"{item_prefix}.notes"),
                    "status": status,
                    "map_url": validate_https_url(raw_item.get("map_url"), f"{item_prefix}.map_url"),
                }
            )
        clean_days.append(
            {
                "date": day_date,
                "base": require_text(raw_day.get("base"), f"{prefix}.base"),
                "title": require_text(raw_day.get("title"), f"{prefix}.title"),
                "summary": optional_text(raw_day.get("summary"), f"{prefix}.summary"),
                "items": clean_items,
            }
        )

    clean_days.sort(key=lambda entry: entry["date"])
    return {"trip": clean_trip, "days": clean_days}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def render(data: dict) -> str:
    trip = data["trip"]
    day_nav = []
    day_sections = []
    for index, day in enumerate(data["days"], start=1):
        anchor = f"day-{day['date'].isoformat()}"
        label = day["date"].strftime("%a %d %b")
        day_nav.append(f'<a href="#{anchor}"><span>Day {index}</span>{esc(label)}</a>')
        items = []
        for item in day["items"]:
            time_label = item["time"]
            if item["end_time"]:
                time_label += f"–{item['end_time']}"
            location_parts = [part for part in (item["location"], item["local_name"]) if part]
            location = " · ".join(location_parts)
            map_link = (
                f'<a class="map" href="{esc(item["map_url"])}" target="_blank" rel="noopener noreferrer">Open map</a>'
                if item["map_url"]
                else ""
            )
            detail = "".join(
                (
                    f'<p class="location">{esc(location)}</p>' if location else "",
                    f'<p class="notes">{esc(item["notes"])}</p>' if item["notes"] else "",
                    map_link,
                )
            )
            items.append(
                f'''<li class="event {esc(item['status'])}">
<div class="time">{esc(time_label)}</div>
<div class="event-body"><div class="event-head"><h3>{esc(item['name'])}</h3><span class="pill">{esc(item['status'])}</span></div>
<p class="kind">{esc(item['type'])}</p>{detail}</div></li>'''
            )
        empty = '<li class="empty">No scheduled items. Keep this day flexible.</li>' if not items else ""
        day_sections.append(
            f'''<section class="day" id="{anchor}">
<header><div><p class="day-label">Day {index} · {esc(label)}</p><h2>{esc(day['title'])}</h2></div><span class="base">Base: {esc(day['base'])}</span></header>
{f'<p class="day-summary">{esc(day["summary"])}</p>' if day['summary'] else ''}
<ol class="timeline">{''.join(items)}{empty}</ol></section>'''
        )

    date_range = f"{trip['start'].strftime('%d %b %Y')} – {trip['end'].strftime('%d %b %Y')}"
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<title>{esc(trip['title'])}</title>
<style>
:root{{--bg:#f5f3ef;--card:#fff;--ink:#1c2530;--muted:#66717f;--line:#d9dde2;--accent:#126b63;--accent-soft:#dff2ef;--optional:#8b5b13;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;color-scheme:light}}*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--bg);color:var(--ink)}}a{{color:var(--accent)}}a:focus-visible{{outline:3px solid #f4a261;outline-offset:3px}}.shell{{width:min(880px,100%);margin:auto;padding:20px 16px 72px}}.hero{{padding:28px;border-radius:24px;background:linear-gradient(135deg,#103f3a,#126b63);color:#fff;box-shadow:0 12px 38px #163c3828}}.eyebrow,.day-label,.kind{{margin:0;text-transform:uppercase;letter-spacing:.1em;font-size:.72rem;font-weight:800}}h1{{margin:.35rem 0;font-size:clamp(2rem,8vw,3.8rem);line-height:1}}.meta{{margin:.75rem 0 0;color:#d4eeea}}.summary{{max-width:62ch;line-height:1.55}}nav{{display:flex;gap:8px;overflow:auto;padding:16px 2px 6px;scrollbar-width:thin}}nav a{{min-width:112px;min-height:52px;padding:9px 12px;border:1px solid var(--line);border-radius:14px;background:var(--card);text-decoration:none;font-weight:800}}nav span{{display:block;color:var(--muted);font-size:.7rem;text-transform:uppercase}}.day{{margin-top:20px;padding:20px;border:1px solid var(--line);border-radius:20px;background:var(--card);box-shadow:0 6px 24px #26333d0d;scroll-margin-top:12px}}.day>header{{display:flex;justify-content:space-between;gap:16px;align-items:start}}h2{{margin:.25rem 0 0;font-size:1.45rem}}.day-label,.kind{{color:var(--accent)}}.base{{padding:7px 10px;border-radius:999px;background:var(--accent-soft);color:#174e48;font-size:.78rem;font-weight:800}}.day-summary,.notes,.location{{color:var(--muted);line-height:1.5}}.timeline{{list-style:none;padding:0;margin:20px 0 0}}.event{{display:grid;grid-template-columns:92px 1fr;gap:14px;padding:16px 0;border-top:1px solid var(--line)}}.time{{font-weight:850;font-variant-numeric:tabular-nums}}.event-head{{display:flex;justify-content:space-between;gap:12px}}h3{{margin:0;font-size:1.02rem}}.pill{{align-self:start;padding:4px 7px;border-radius:999px;background:#edf0f2;color:#4e5965;font-size:.68rem;font-weight:900;text-transform:uppercase}}.confirmed .pill,.reserved .pill{{background:var(--accent-soft);color:#174e48}}.optional .pill{{background:#fff1d9;color:var(--optional)}}.kind{{margin:.35rem 0}}.location,.notes{{margin:.35rem 0}}.map{{display:inline-flex;align-items:center;min-height:44px;margin-top:4px;font-weight:800}}.empty{{padding:20px;color:var(--muted)}}@media(max-width:560px){{.shell{{padding:12px 10px 56px}}.hero,.day{{padding:17px;border-radius:16px}}.day>header{{display:block}}.base{{display:inline-block;margin-top:10px}}.event{{grid-template-columns:1fr;gap:7px}}.time{{color:var(--accent)}}}}@media print{{body{{background:#fff}}.shell{{width:100%;padding:0}}.hero{{background:#fff;color:#000;box-shadow:none;border:1px solid #bbb}}.meta{{color:#333}}nav{{display:none}}.day{{break-inside:avoid;box-shadow:none}}.map{{display:none}}}}
</style>
</head>
<body><main class="shell"><header class="hero"><p class="eyebrow">Travel itinerary</p><h1>{esc(trip['title'])}</h1><p class="meta">{esc(date_range)} · {esc(trip['timezone'])}</p>{f'<p class="summary">{esc(trip["summary"])}</p>' if trip['summary'] else ''}</header>
<nav aria-label="Trip days">{''.join(day_nav)}</nav>{''.join(day_sections)}</main></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Canonical itinerary JSON")
    parser.add_argument("output", type=Path, help="Generated HTML path")
    args = parser.parse_args()
    try:
        data = load_and_validate(args.source)
        output = render(data)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(output, encoding="utf-8")
        temporary.replace(args.output)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Rendered {len(data['days'])} day(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
