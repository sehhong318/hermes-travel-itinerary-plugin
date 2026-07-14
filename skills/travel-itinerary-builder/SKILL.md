---
name: travel-itinerary-builder
description: "Use when turning travel requirements into a realistic multi-day plan and a self-contained, phone-friendly HTML itinerary. Establishes a canonical JSON plan, validates timing and uncertainty, generates accessible mobile HTML, and verifies the rendered artifact without adding hosting, expense, or destination-specific assumptions."
version: 1.0.0
author: Hermes Agent
license: MIT
created_by: agent
metadata:
  hermes:
    tags: [travel, itinerary, planning, mobile-html, static-site]
    related_skills: [maps]
---

# Travel Itinerary Builder

## Overview

Build a realistic travel plan first, then render it as a self-contained mobile HTML page. Keep itinerary facts in one structured file and treat HTML as a generated artifact. This prevents the schedule and the page from drifting apart.

This skill is deliberately limited to two outcomes:

1. a coherent, machine-readable trip plan; and
2. an accessible, phone-friendly HTML itinerary.

It does not prescribe hosting, authentication, expense tracking, booking, or destination-specific behavior.

## When to Use

Use this skill when the user asks to:

- create or reorganize a multi-day itinerary;
- turn notes, messages, spreadsheets, or research into a day-by-day plan;
- generate a mobile itinerary page;
- revise a plan while keeping the HTML synchronized;
- validate schedule realism, buffers, links, and mobile usability.

Do not use it as proof of current opening hours, live transport, availability, prices, or reservation status. Retrieve and cite current sources when those facts affect the plan.

## Artifact Contract

Keep these artifacts together:

```text
trip-project/
├── itinerary.json              # canonical plan
├── itinerary.html              # generated output
└── sources.md                  # optional citations and checked-at times
```

If a repository already has an authoritative format, preserve it instead of introducing a competing copy. Generate HTML from the existing structured source whenever practical.

## Phase 1 — Define the Planning Brief

Collect or retrieve only the inputs that materially affect the schedule:

- trip title, start date, end date, and local timezone;
- arrival/departure constraints;
- overnight base for each date;
- fixed reservations and their required arrival buffers;
- traveler priorities and must-do items;
- pace, walking tolerance, accessibility, luggage, and rest needs;
- transport preferences and budget boundaries;
- optional items that can be dropped when delayed;
- language or local-name requirements for labels.

Write unknowns as unknowns. Never turn “morning,” “about two hours,” or “maybe” into a fabricated exact time.

**Completion criterion:** every fixed constraint has a source or is explicitly labeled as a user assumption, and unresolved details are visible rather than silently guessed.

## Phase 2 — Create the Canonical Plan

Use `templates/itinerary.example.json` as the starting shape. The minimum model is:

```json
{
  "trip": {
    "title": "Sample Journey",
    "start": "2030-04-10",
    "end": "2030-04-12",
    "timezone": "Europe/Paris",
    "summary": "A relaxed three-day city break."
  },
  "days": [
    {
      "date": "2030-04-10",
      "base": "Central district",
      "title": "Arrival and orientation",
      "summary": "Keep the first day flexible after travel.",
      "items": [
        {
          "time": "14:00",
          "end_time": "15:00",
          "name": "Hotel check-in",
          "type": "hotel",
          "location": "Hotel area",
          "local_name": "",
          "notes": "Store luggage if the room is not ready.",
          "status": "planned",
          "map_url": "https://maps.example.com/"
        }
      ]
    }
  ]
}
```

### Required invariants

- `trip.start <= trip.end`.
- Every day date is unique, valid, and inside the trip range.
- Days are sorted chronologically.
- Each item has a non-empty `name`, `type`, and `status`.
- Exact `HH:MM` times are used only when justified; otherwise use labels such as `Morning`, `T-3h`, or `Flexible`.
- End times do not precede start times when both are exact times.
- All external links use `https://`.
- Reservations are distinct from merely planned items.
- Optional items are marked `optional`, not placed as silent commitments.

Recommended item types are `transport`, `hotel`, `activity`, `food`, `buffer`, and `note`. Recommended statuses are `planned`, `reserved`, `confirmed`, and `optional`.

**Completion criterion:** the canonical JSON parses successfully and every invariant above holds.

## Phase 3 — Make the Schedule Realistic

Evaluate each day as a sequence, not a list of attractions.

1. Anchor fixed events first: flights, trains, check-ins, tickets, and reservations.
2. Add transfer time between different locations.
3. Add explicit buffers for airports, unfamiliar stations, queues, and luggage.
4. Group nearby activities to reduce backtracking.
5. Put high-priority activities before optional ones.
6. Avoid filling every open minute; include meal and recovery space.
7. Check base changes for checkout, luggage storage, and check-in timing.
8. Flag assumptions that require current verification, such as hours or seasonal service.

A day is overloaded when one delay makes every later item fail. Move or mark items optional until the day remains usable after a modest delay.

**Completion criterion:** every location change has travel time or an explicit unresolved route, and each dense day has at least one removable item or recovery buffer.

## Phase 4 — Generate the Mobile HTML

Run the bundled renderer:

```bash
python3 scripts/render_itinerary.py itinerary.json itinerary.html
```

The renderer must keep the output:

- self-contained: inline CSS and JavaScript, no required CDN;
- responsive: single-column layout at phone widths;
- accessible: semantic landmarks, visible focus, sufficient contrast, and 44px tap targets;
- resilient: essential plan content remains readable if JavaScript is unavailable;
- safe: all itinerary text is HTML-escaped and external URLs are restricted to HTTPS;
- printable: a clean print layout expands all days;
- honest: statuses and uncertainty are visible in the page.

The top of the page should show the title, date range, timezone, and summary. Each day should show its date, base, summary, and ordered timeline. Each item should show time, name, type/status, location, notes, and an optional map link.

Never hand-edit generated HTML to change itinerary facts. Update the canonical JSON and regenerate.

**Completion criterion:** the output file is produced from the current JSON and contains every day and item exactly once.

## Phase 5 — Verify the Artifact

### Structural checks

```bash
python3 -m json.tool itinerary.json >/dev/null
python3 scripts/render_itinerary.py itinerary.json itinerary.html
python3 - <<'PY'
from pathlib import Path
html = Path("itinerary.html").read_text(encoding="utf-8")
assert "<!doctype html>" in html.lower()
assert "<meta name=\"viewport\"" in html
assert "javascript:" not in html.lower()
print("basic HTML checks passed")
PY
```

### Content checks

- Compare the page with the canonical plan.
- Confirm date range, timezone, day count, and item count.
- Confirm uncertainty and optional statuses remain visible.
- Open every map link and ensure it targets the intended location.
- Check that special characters render correctly.

### Visual checks

Serve locally and inspect at desktop and phone widths:

```bash
python3 -m http.server 8000
```

At minimum verify:

- no horizontal overflow at 360px width;
- readable type without zoom;
- day controls and links meet the 44px tap-target goal;
- long names and notes wrap without clipping;
- keyboard focus is visible;
- printing does not hide itinerary content.

**Completion criterion:** structural, content, and visual checks pass against the generated file—not merely against source code.

## Revision Workflow

For every requested change:

1. Read the latest canonical source.
2. Identify affected days, transfers, and fixed constraints.
3. Edit the canonical plan only.
4. Re-run validation and generation.
5. Inspect the changed day and adjacent transfers.
6. Report the concrete files changed and checks executed.

Do not claim the page is updated if only the JSON changed or if the generated HTML was not verified.

## Common Pitfalls

1. **Duplicated truth:** editing JSON and HTML separately. Fix by regenerating HTML.
2. **False precision:** inventing exact times. Preserve ranges and flexible labels.
3. **List-shaped days:** attractions appear without travel or buffers. Add sequence constraints.
4. **Hidden overload:** every item looks mandatory. Mark lower-priority items optional.
5. **Desktop-first output:** cards become tiny or overflow on phones. Inspect at 360px.
6. **Unsafe rendering:** itinerary text is inserted without escaping. Escape all text and allow HTTPS links only.
7. **Map dependency:** essential instructions exist only in an embedded map. Keep them in text.
8. **Stale HTML:** the page was not regenerated after a plan edit. Compare timestamps or rebuild deterministically.

## Verification Checklist

- [ ] One canonical structured itinerary exists.
- [ ] Dates, timezone, bases, and fixed constraints are explicit.
- [ ] Transfers, buffers, optional items, and uncertainty are represented.
- [ ] JSON validation passes.
- [ ] HTML is regenerated from the current plan.
- [ ] Dynamic text is escaped and links are HTTPS-only.
- [ ] All days and items appear exactly once.
- [ ] Desktop, 360px mobile, keyboard, and print checks pass.
- [ ] No destination-specific or private trip data is embedded in reusable templates.
