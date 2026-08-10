# Transit API reference notes

`https://api.transit.ls8h.com` is an unofficial, unauthenticated third-party
service that has exposed GTFS/ODPT-derived Japan transit data. Availability,
terms, feeds, paths, and response fields may change without notice. Check the
service terms and probe the exact endpoint needed before relying on it.

The plugin's supported interface is `../scripts/transit_client.py`, which applies
bounded timeouts, input validation, response-shape checks, and walk-only route
filtering. These notes describe observed protocol shapes, not a service-level
guarantee.

## Observed endpoints

| Endpoint | Observed purpose |
|---|---|
| `/api/v1/places/suggest?q=<jp>&limit=N` | Station/place suggestions with an `endpoint` field |
| `/api/v1/locations/suggest?q=<jp>&limit=N` | Feed-qualified station/stop suggestions |
| `/api/v1/places/reverse?lat=&lon=&radiusMeters=` | Nearby endpoints from coordinates |
| `/api/v1/plan?from=&to=&date=&time=&type=` | Schedule-based route candidates |
| `/api/v1/feeds` | Feed and attribution metadata |
| `/api/v1/operators` | Operator metadata |

Other paths exposed at one time—guidance, station detail, or departures—must be
capability-tested before use. A missing generic `/health` route says nothing
about an individual data endpoint.

## Observed plan parameters

- `from` / `to`: API-returned endpoint strings; do not invent them.
- `date`: service date in `YYYYMMDD`.
- `time`: local time in `HH:MM`.
- `type`: `departure`, `arrival`, `first`, or `last`.
- `numItineraries`: number of candidates requested.

The packaged client intentionally supports a conservative subset. If the API
adds or removes parameters, update tests before changing the client.

## Observed response shape

```json
{
  "date": "20300410",
  "type": "departure",
  "timezone": "Asia/Tokyo",
  "from": {},
  "to": {},
  "journeys": [
    {
      "departureSecs": 34260,
      "arrivalSecs": 36600,
      "durationSecs": 2340,
      "transferCount": 0,
      "legs": [
        {
          "mode": "rail",
          "from": {"name": "Origin"},
          "to": {"name": "Destination"},
          "line": {}
        }
      ]
    }
  ]
}
```

Times have been observed as seconds from service-date midnight in the returned
timezone and may exceed 86400 for after-midnight service. Validate this against
the current payload before conversion.

## Historical observations

The following are troubleshooting observations from earlier runs, not permanent
facts:

- Some suggestions used `geo:lat,lon`; some used feed-qualified IDs.
- Certain feed-qualified IDs were suggestible but not routable.
- The first journey could be pure walking with no transit mode.
- Japanese station queries often produced better matches than romanized names.
- Feed coverage differed by operator and changed independently of API uptime.

Do not publish historical departure minutes as current schedules. Do not infer
that another mapping API always succeeds or always fails from one test run.

## Verification

- Probe the exact suggestion/plan endpoint with a bounded timeout.
- Validate `places` and `journeys` types before reading nested fields.
- Reject malformed journeys and those without a public-transit leg.
- Compare candidate routes with an official operator planner or user-visible map.
- Label the checked-at time and schedule-vs-real-time status.
- Recheck official alerts and the final route near departure.
