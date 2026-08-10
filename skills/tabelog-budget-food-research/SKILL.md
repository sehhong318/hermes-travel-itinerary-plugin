---
name: tabelog-budget-food-research
description: "Use when researching budget-aware Japan restaurants."
version: 1.1.0
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [japan, tabelog, restaurants, budget, itinerary, food-map]
    category: productivity
    requires_toolsets: [terminal]
---

# Budget-aware Japan Restaurant Research

Build a source-labelled restaurant shortlist that respects the user's current
meal budget, location, dates, dietary needs, and itinerary. Tabelog is one
best-effort source, not a guaranteed API and not the sole authority for whether
a restaurant is open or suitable.

## Define the brief first

Record before searching:

- exact area or route segment;
- meal date and approximate time;
- per-person budget and whether it includes drinks, tax, or service charges;
- party size, dietary constraints, reservation preference, and walking limit;
- desired number and mix of recommendations.

Do not substitute hard-coded rating cutoffs, price tiers, recommendation counts,
or cuisine quotas for the user's brief.

## Capability check

Tabelog access controls and markup vary by page, language, network, and time. Use
an available browser or a bounded HTTP request. Never bypass a CAPTCHA,
challenge, login requirement, or access control.

For every saved listing or detail page, run the packaged guard with the expected
canonical page title:

```bash
python3 scripts/tabelog_guard.py saved-page.html \
  --expected-title "EXPECTED CANONICAL TITLE"
```

The command exits zero only for `ok`. Treat `blocked`, `wrong_page`, `invalid`,
and `error` as failures; never parse those pages as restaurant data.

## Research workflow

1. Search the current Tabelog interface or a search engine for candidates near
   the requested area. Do not rely on undocumented query parameters.
2. Validate each page with the guard before extraction.
3. Read the current page semantics instead of assuming stable CSS selectors.
4. Capture only fields visibly present on the validated page:
   - restaurant name and detail URL;
   - displayed meal budget and its meal context;
   - displayed rating and review count;
   - cuisine, nearest station, and reservation indicator;
   - source URL and checked-at time.
5. Cross-check operational facts with an official restaurant, building,
   operator, or booking-provider page when available:
   - Japanese name and exact branch;
   - address and nearest exit;
   - opening hours, closure notices, and reservation policy.
6. Distinguish conflicting or missing fields instead of choosing the more
   convenient value. Record which source supplied each fact.
7. Rank candidates using the user's stated priorities. Ratings are comparative
   evidence, not universal quality thresholds or predictions.

## Rate limits and retries

Prefer one validated results page plus client-side filtering over many rapid
requests. Honor HTTP status and `Retry-After`. Use bounded exponential backoff
with a small retry cap for transient failures. Stop on challenges, repeated
mismatches, or persistent errors rather than increasing request pressure.

## Fallback

When Tabelog is blocked, stale, unavailable, or returns a mismatched page:

1. Do not report zero candidates unless a valid source actually proves that.
2. Preserve already verified fields and mark unavailable Tabelog-only fields as
   null.
3. Continue with official restaurant/building pages, official booking providers,
   and user-visible map listings.
4. Label the source and checked-at time for every retained operational fact.
5. Export the shortlist as Markdown, CSV, or JSON; do not fabricate missing
   ratings, budgets, hours, or reservation availability.

## Output contract

Return a compact table or structured data with:

| Field | Requirement |
|---|---|
| Name | Display name plus Japanese name when verified |
| Branch/location | Exact branch and area; never infer from a chain name |
| Meal budget | Current displayed range and meal context, or null |
| Evidence | Rating/reviews only when present on a validated page |
| Operational facts | Hours/status/reservation with source and checked-at time |
| Fit | Why it matches the user's current budget and itinerary |
| Risks | Source conflict, stale data, access failure, or missing field |
| Links | Direct source links and a user-visible map search link |

For a map search link, URL-encode the verified branch name and location:

```text
https://www.google.com/maps/search/?api=1&query=<urlencoded query>
```

## Verification

Before presenting results:

- every Tabelog-derived row came from a guard result of `ok`;
- restaurant name, branch, and area refer to the same place across sources;
- budget context is not confused between lunch, dinner, set, or course pricing;
- operational facts carry a source and checked-at time;
- missing or conflicting fields remain explicit;
- no CAPTCHA was bypassed and no unsupported external service was implied;
- output contains no credentials, cookies, private paths, or private itinerary
  details beyond what the user requested for the current task.
