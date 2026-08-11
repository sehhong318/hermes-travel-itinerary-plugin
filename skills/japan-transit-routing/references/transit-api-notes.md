# Transit API (api.transit.ls8h.com) — reference notes

Free, unauthenticated, read-only Japan transit API (GTFS/ODPT-derived).
Unofficial; check https://transit.ls8h.com/terms before heavy use.
Wrapper: https://github.com/Anchovy-s3/japan-transit-mcp

## Endpoints (all GET, JSON)

| Endpoint | Purpose |
|---|---|
| `/api/v1/places/suggest?q=<jp>&limit=N` | Search stations/places → `endpoint` field |
| `/api/v1/locations/suggest?q=<jp>&limit=N` | Station/stop IDs only (feed-qualified) |
| `/api/v1/places/reverse?lat=&lon=&radiusMeters=` | Nearby endpoints from coordinates |
| `/api/v1/plan?from=&to=&date=&time=&type=` | Route plan (departure/arrival/first/last) |
| `/api/v1/guidance/plan?...` | Ranked guidance options |
| `/api/v1/stations/<id>` | Station detail + platforms |
| `/api/v1/stations/<id>/departures` | Departure board (license permitting) |
| `/api/v1/feeds` | Ingested GTFS/ODPT feeds + attribution |
| `/api/v1/operators` | Operator branding/license metadata |

## plan params

- `from` / `to`: endpoint string — `geo:lat,lon` or feed-qualified `feedId:stopId`
- `date`: YYYYMMDD (e.g. 20260825) — service date
- `time`: HH:MM or HH:MM:SS
- `type`: `departure` (default) | `arrival` | `first` | `last`
- `allowModes` / `avoidModes`: comma list e.g. `rail,bus`
- `avoidWalk`: bool; `maxTransfers`: 0-8 (default 3); `numItineraries`: 1-6 (default 3)
- `via`: up to 3 waypoints (departure/arrival only)

## Response shape

```json
{
  "date": "20260825", "type": "departure", "timezone": "Asia/Tokyo",
  "from": {...}, "to": {...},
  "journeys": [
    {
      "departureSecs": 34260, "arrivalSecs": 36600, "durationSecs": 2340,
      "transferCount": 0, "accessWalkSecs": 9062, "egressWalkSecs": 211,
      "legs": [
        {"mode": "rail", "from": {"name": "大阪"}, "to": {"name": "京都"}, "line": {...}}
      ]
    }
  ]
}
```

**Times = seconds from service-date midnight in `timezone`.** May exceed 86400
(after-midnight service). Convert: `h = secs//3600; m = (secs%3600)//60`.

## Verified example routes (24-30 Aug 2026, Asia/Tokyo)

| Route | Date/Time | Result |
|---|---|---|
| 心斎橋 → 難波 (subway) | 27 Aug 15:00 | dep 15:03/15:07, 4 min, 0 transfers |
| 梅田 → 京都 (JR) | 25 Aug 09:30 | dep 09:33/09:36/09:39, arr 10:15, ~40 min |
| 梅田 → 七条 (Onyado Nono) | 25 Aug 09:30 | dep 09:33, arr 10:29, ~52 min (大阪→京都→walk) |
| 七条 → 嵐山 | 26 Aug 08:30 | dep 08:43, arr 09:26, ~43 min (京都→嵯峨嵐山) |
| 七条 → 心斎橋 (Keihan→subway) | 27 Aug 13:00 | dep 13:08, arr 14:03, 55 min, 1 transfer |
| なんば → 近鉄奈良 (Kintetsu) | 28 Aug 09:30 | dep 09:41, arr 10:22, ~41 min direct |
| 心斎橋 → ユニバーサルシティ | 29 Aug 08:30 | dep 08:32, arr 09:28, ~56 min, 2 transfers (ドーム前→西九条) |
| 梅田 → 三ノ宮 (Kobe, JR) | 30 Aug 10:00 | dep 10:03, arr 10:34, ~31 min direct |

## Gotchas hit in practice

- `scrape-nankai` (Nankai Railway, Kansai Airport) is suggest-only, NOT routable —
  `plan` returns `stationNotFound` for its feed IDs. Use `geo:` coordinates for KIX.
- First journey in the list may be a pure-walk route (mode null, hours long) — skip it.
- Japanese query terms give better suggest hits than romanized names.
- Google Directions API transit mode returns ZERO_RESULTS for Japan — do not
  retry it; the Transit API is the replacement.
- Station codes for itinerary sheets: Osaka Metro letter+number (M/C/N), Keihan
  KH, Kintetsu A, Nankai NK; JR lines use line name only.

## MCP server setup (recreate if needed)

```bash
# 1. Clone + build the wrapper
cd /tmp && git clone --depth 1 https://github.com/Anchovy-s3/japan-transit-mcp.git
cd japan-transit-mcp && npm install && npm run build   # → dist/index.js

# 2. Register with Hermes (answer "Y" to enable all 10 tools)
echo "Y" | hermes mcp add japan-transit --command node --args /tmp/japan-transit-mcp/dist/index.js

# 3. Verify in config: ~/.hermes/config.yaml → mcp_servers.japan-transit
# 4. MCP tools load ONLY in NEW sessions (mcp_japan_transit_*)
#    Until then, call the REST API directly (endpoints above).
```

Registered state: `mcp_servers.japan-transit` in `~/.hermes/config.yaml`
(enabled, 10/10 tools). If the config entry is missing, re-run step 2.
