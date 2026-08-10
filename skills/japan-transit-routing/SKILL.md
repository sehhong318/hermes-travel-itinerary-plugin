---
name: japan-transit-routing
description: "Use when planning Japan transit with verified fallbacks."
version: 1.1.0
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [japan, transit, trains, metro, routes, travel]
---

# Japan Transit Routing

Plan Japan rail, metro, bus, and ferry legs without treating any single third-party
service as authoritative. Timetables, platforms, fares, disruptions, and even API
availability change. Always name the source, record when it was checked, and ask
the traveler to recheck close to departure.

## When to use

- The user asks how to travel between Japanese places.
- An itinerary needs route order, transfer buffers, fares, or station codes.
- A saved route must be rechecked before travel.

## Source order

1. **Official operator source** for service notices, planned engineering work,
   airport access, ticket rules, and timetable confirmation.
2. **A user-visible map or journey-planning app** for practical route comparison.
3. **Optional Transit API** for structured suggestions and schedule-based
   route candidates. Treat these as supporting data, not live operational truth.

Do not call a scheduled result “live” unless its source explicitly supplies
real-time status and the response contains a freshness timestamp.

## Capability check

Before using an optional integration:

- For the direct API, make one bounded suggestion request with a 10-second
  timeout and validate the JSON shape.
- Do not install or configure unrelated external integrations as a prerequisite.

This plugin packages a Python-standard-library client at
`scripts/transit_client.py`. It validates suggestions and route response shapes,
uses bounded timeouts, filters walk-only journeys, and raises an actionable
`TransitServiceError` instead of returning plausible-looking data.

```python
from transit_client import TransitServiceError, plan_route, suggest_places

try:
    places = suggest_places("梅田", limit=3)
    origin = places["places"][0]["endpoint"]
    routes = plan_route(
        origin,
        "geo:34.9858,135.7588",
        date="20260825",
        time="09:30",
    )
except TransitServiceError:
    routes = None  # continue with the Fallback workflow below
```

Pass API-returned endpoint strings verbatim. Do not invent feed-qualified IDs.

## Optional direct API

Base URL: `https://api.transit.ls8h.com`

- Suggestions: `/api/v1/places/suggest?q=<name>&limit=<1-10>`
- Route planning: `/api/v1/plan?from=<endpoint>&to=<endpoint>&date=YYYYMMDD&time=HH:MM&type=departure&numItineraries=3`

Service availability and feed coverage are mutable. A missing `/health` endpoint
is not proof that route endpoints work or fail; probe the exact endpoint needed.
Validate that `places`/`journeys` are lists and that each retained journey has a
real transit leg.

## Fallback

When the optional API is unavailable, malformed, stale, or geographically
wrong:

1. Open an official operator planner or the user's map app.
2. Record route, line, transfer station, approximate duration, fare, and source.
3. Mark uncertain departure/platform details as `recheck-required`.
4. Add transfer and station-navigation buffers instead of inventing exact times.
5. Recheck official disruptions and the final route 1–3 days before travel and
   again on departure day.

A fallback route is useful only when its uncertainty is visible. Never fabricate
an API response or silently substitute typical headways for a timetable.

## Station codes and headways

Station codes are line-specific. Verify them with an operator source before
publication. Common patterns include Osaka Metro M/C/N, Keihan KH, Kintetsu A,
and Nankai NK; JR stations may not use the same public code convention.

Typical headways can help size buffers, but must be labeled estimates—not quoted
as a particular departure. Peak/off-peak, weekends, holidays, and disruptions
change them.

## Validation checklist

- Exact origin and destination branches/stations resolved.
- Date, local time, weekday, and arrival/departure intent recorded.
- Every journey has at least one rail/metro/bus/tram/ferry leg.
- Duration and transfers pass a common-sense check.
- Official alerts checked for important or same-day travel.
- Source URL and checked-at time shown.
- User is told what must be reconfirmed.

Protocol notes and response examples are in `references/transit-api-notes.md`.
