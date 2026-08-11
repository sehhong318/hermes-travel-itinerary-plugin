---
name: japan-transit-routing
description: "Use when planning Japan train routes — get live times."
version: 1.0.0
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [japan, transit, trains, metro, routes, mcp, travel]
---

# Japan Transit Routing (live train times)

Get REAL Japan train/metro departure times for trip planning. Google's
Directions API does NOT serve Japan transit data (transit mode returns
ZERO_RESULTS for Japan even when it works for other countries) — so use the
**Transit API** (`api.transit.ls8h.com`) instead, directly or via the registered
**japan-transit MCP server**.

## When to use

- User asks for Japan train/metro routes, times, fares, or "how do I get from A to B in Japan"
- Verifying/refining a Japan itinerary's transport legs with live scheduled departures
- Any Japan transit query where Google Maps API or Jorudan fails/blocked

## Quick path: registered MCP (preferred)

`japan-transit` MCP server is registered in `~/.hermes/config.yaml`
(`mcp_servers.japan-transit`), built from
https://github.com/Anchovy-s3/japan-transit-mcp — a wrapper around the free,
unauthenticated Transit API. Tools appear as `mcp_japan_transit_*` (they load at
session start; if missing, the server may need a new session).

Tools: `suggest_places`, `suggest_stations`, `reverse_places`, `plan_route`,
`guidance_plan`, `get_station`, `station_departures`, `list_feeds`,
`list_operators`, `health`.

Workflow: `suggest_places` (e.g. "梅田") → take the returned `endpoint` →
`plan_route` with `from`/`to` endpoints + `date` (YYYYMMDD) + `time` (HH:MM) +
`type=departure`.

### MCP tool-call examples (exact names)

Once loaded (new session), call the tools directly — they take the same params
as the API:

```
mcp_japan_transit_suggest_places(q="梅田", limit=3)
   → returns places[] with "endpoint": "geo:34.703180,135.497801" (or feed-qualified id)

mcp_japan_transit_plan_route(
    from="geo:34.703180,135.497801",     # origin endpoint from suggest_places
    to="geo:34.989607,135.767768",       # destination endpoint (七条)
    date="20260825", time="09:30", type="departure",
    numItineraries=3
)
   → journeys[] with departureSecs/arrivalSecs/durationSecs/transferCount/legs[]

mcp_japan_transit_reverse_places(lat=34.4358, lon=135.2432, radiusMeters=100)
   → nearby routable stations when you only have coordinates

mcp_japan_transit_station_departures(id="osakametro-rail:大阪市高速電気鉄道-御堂筋線-梅田")
   → live departure board for a station (license permitting)
```

Key: always pass the `endpoint` string verbatim from
`suggest_places`/`reverse_places` into `plan_route` — never retype or guess it.
`geo:lat,lon` endpoints route; `scrape-*` feed IDs don't (see Pitfalls).

## Direct API path (no MCP needed)

Base: `https://api.transit.ls8h.com` — free, no auth, read-only.

```bash
# 1. Find endpoints (returns `endpoint` field, e.g. "geo:34.703180,135.497801")
curl -s "https://api.transit.ls8h.com/api/v1/places/suggest?q=%E6%A2%85%E7%94%B0&limit=3"

# 2. Plan a route (date=YYYYMMDD, time=HH:MM, type=departure|arrival|first|last)
curl -s "https://api.transit.ls8h.com/api/v1/plan?from=<endpoint>&to=<endpoint>&date=20260825&time=09:30&type=departure&numItineraries=3"
```

Response shape: top-level keys `date`, `type`, `timezone`, `from`, `to`,
`journeys`. Each journey: `departureSecs`, `arrivalSecs`, `durationSecs`,
`transferCount`, `accessWalkSecs`, `egressWalkSecs`, `legs[]` (each with `mode`,
`from.name`, `to.name`, `line`). **Times are seconds from service-date midnight
in `timezone`** — values may exceed 86400 for after-midnight service. Convert:
`h = secs//3600, m = (secs%3600)//60`.

## Station codes for itinerary sheets (learned from real use)

When writing transport rows to an itinerary, use the operator-specific station
code format (verified via the API's feed-qualified IDs):

| Operator / Line | Code format | Example |
|---|---|---|
| Osaka Metro Midosuji (M) | M + number | 梅田 M16, 淀屋橋 M17, 心斎橋 M19, 難波 M20 |
| Osaka Metro Chuo (C) | C + number | — |
| Osaka Metro Nagahori (N) | N + number | 心斎橋 N15, ドーム前千代崎 N12 |
| Keihan Main Line | KH + number | 七条 KH38, 伏見稲荷 KH36, 祇園四条 KH39, 淀屋橋 KH01 |
| Kintetsu Nara Line | A + number | 大阪難波 A01, 近鉄奈良 A28 |
| Nankai Airport Line | NK + number | 難波 NK01, 関西空港 NK31 |
| JR lines | no station codes | use line name: JR京都線 新快速 |

Typical headways for the frequency column: Osaka Metro 3-5 min, Keihan 5-10,
JR Kyoto/Kobe/Sagano 15-30, Kintetsu Nara 20-30, Nankai Rapi:t 30, city bus
10-20. Always note these are schedule-based; confirm on the ground.

## Blocked alternatives (don't re-chase these)

- **Jorudan (`jorudan.co.jp`) is not curl-able.** Its search flow redirects
  through `jid.jorudan.co.jp/jrd_uuid/` — a JS-driven UUID session assignment —
  and `redirect2.cgi` rejects requests without that session cookie. curl gets an
  infinite redirect loop / empty page. No query-string workaround found.
- **MLIT 国土数値情報 railway data (`nlftp.mlit.go.jp/ksj/.../KsjTmplt-N02...`)
  is GIS geometry, not a timetable.** It ships railway line shapes + station
  coordinates as shapefiles (reference years 2015-2022) — no schedules, fares,
  or routing.
- **Google Directions API `mode=transit` returns ZERO_RESULTS for Japan** even
  when the Directions API is enabled (verified: same key returns OK for NYC
  transit, ZERO_RESULTS for Tokyo/Osaka).

## Pitfalls

- **`geo:<lat>,<lon>` endpoints work for routing; `scrape-*` feed IDs do NOT.**
  Kansai Airport's Nankai feed is `scrape-nankai` (suggest-only, not routable) —
  a `geo:` point at the airport routes via a nearby JR station instead (e.g.
  新家). For airports/stations on scrape feeds, use the `geo:` endpoint from
  suggest rather than the feed ID.
- **Routable feeds are the GTFS/ODPT ones**: `osakametro-rail`, `jrwest-*`,
  `kintetsu-*`, `keihan-*`, `hanshin-rail-*`, etc. Check `list_feeds` when a
  station won't route.
- **Walking routes pollute results**: `journeys[0]` can be a pure-walk itinerary
  with `mode` null and huge `durationSecs`. Skip journeys with no rail/subway
  legs when the user wants transit.
- **Station name matching is fuzzy**: use Japanese station names in suggest (梅田
  not "Umeda") for the best hits; the API returns `nameEn` when available.
- **Don't claim exact minutes as gospel**: departures are schedule-based; always
  tell the user to confirm on the ground (Google Maps app has Japan data the API
  lacks).

## Verification

After planning, sanity-check: journey durations and transfer counts should match
common sense (e.g. Osaka→Kyoto ~30-50 min, Namba→Nara ~40 min). If the API
returns `stationNotFound` for a `scrape-*` endpoint, switch to `geo:` coordinates
from suggest.

Full endpoint/param reference and example verified routes:
`references/transit-api-notes.md`
