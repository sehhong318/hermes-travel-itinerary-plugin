---
name: travel-itinerary-builder
description: "Use when creating or revising a realistic multi-day plan, an existing phone-friendly itinerary project, or its optional trip-expense view. Establishes one authoritative source, validates timing and uncertainty, resolves map-linked revisions, keeps trip spending isolated from ordinary ledgers, generates or synchronizes accessible mobile HTML, and verifies the real protected artifact."
version: 2.0.1
author: Hermes Agent
license: MIT
created_by: agent
metadata:
  hermes:
    tags: [travel, itinerary, planning, mobile-html, static-site, trip-expenses]
    related_skills: [maps]
---

# Travel Itinerary Builder

## Overview

Build a realistic travel plan first, then render or synchronize it as a self-contained mobile HTML page. Keep itinerary facts in one authoritative source: use structured JSON for new projects, but preserve an existing project's tested source format. This prevents the schedule, source, runtime, and visible page from drifting apart.

This skill has two core outcomes and one optional integration:

1. a coherent, machine-readable trip plan;
2. an accessible, phone-friendly HTML itinerary; and
3. when requested, a private trip-expense view backed by a ledger that is isolated from ordinary spending.

It does not prescribe a hosting provider, booking system, destination-specific behavior, or full accounting product. Authentication and expense handling are integrated only by preserving the existing project's boundaries and explicit user requirements.

## When to Use

Use this skill when the user asks to:

- create or reorganize a multi-day itinerary;
- turn notes, messages, spreadsheets, or research into a day-by-day plan;
- generate a mobile itinerary page;
- revise a plan while keeping the HTML synchronized;
- validate schedule realism, buffers, links, and mobile usability;
- place a trip-specific expense tab or section inside an itinerary;
- keep travel spending separate from ordinary or household expenses;
- verify trip-expense currencies, totals, privacy, and source/runtime synchronization.

Do not use it as proof of current opening hours, live transport, availability, prices, or reservation status. Retrieve and cite current sources when those facts affect the plan.

## Artifact Contract

Keep these artifacts together:

```text
trip-project/
├── itinerary.json              # canonical plan
├── itinerary.html              # generated output
├── trip-expenses.csv           # optional independent trip ledger
├── trip-expenses.json          # optional generated expense snapshot
└── sources.md                  # optional citations and checked-at times
```

If a repository already has an authoritative format, preserve it instead of introducing a competing copy. Generate HTML from the existing structured source whenever practical.

### Existing-project mode

When the itinerary already lives inside an application or authenticated companion page, do not force the new-project JSON layout onto it. First identify the project's actual source of truth, generated/runtime copies, regression tests, authentication boundary, and synchronization mechanism. Preserve adjacent tabs, APIs, manifests, and independent data stores while changing the itinerary.

Follow `references/existing-itinerary-project-workflow.md` for the full discover → regress → edit → synchronize → authenticated-live-verify workflow. That branch takes precedence over the generic file layout above.

**Completion criterion:** the existing authority is preserved, no competing itinerary source is introduced, and every derived/runtime artifact is accounted for.

### Optional trip-expense mode

When the user wants spending inside the itinerary, keep trip expenses in an independent ledger or persistence namespace rather than filtering the ordinary ledger. Preserve original currencies as separate totals, follow the requested unified or per-traveler presentation, escape every record-derived value, and keep examples out of production data.

The bundled generic renderer remains itinerary-only. Add expense rendering through the existing authenticated project view, or extend the renderer only with an explicit private-data boundary and regression coverage; never expose a real ledger merely because the static itinerary is shareable.

Follow `references/travel-expense-integration.md` for ledger boundaries, safe message routing, currency rules, itinerary-tab rendering, snapshot synchronization, regression tests, and authenticated live verification.

**Completion criterion:** trip records and ordinary records cannot alter each other's counts or totals, each currency is independently reproducible, and the private itinerary expense view is verified in its requested location.

### Local export mode

When the user wants a portable table or machine-readable copy, run
`scripts/export_itinerary.py` to emit CSV, Markdown, or normalized JSON. The
standard-library exporter reads the canonical source, writes atomically, and
refuses to overwrite that source.

**Completion criterion:** the requested local artifact is opened or parsed and
the canonical input remains byte-for-byte unchanged.

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

### Map-linked venue revisions

When a traveler sends a map short link, resolve the exact branch before changing the schedule. Compare it with the current day sequence, preserve same-station or connected-building continuity, replace any competing meal in that slot, and shift the next activity if dining or travel time changes. Never add a redundant train leg merely because a station exit appears after a station-connected venue.

Follow `references/map-linked-itinerary-revisions.md` for the full resolve → cluster → substitute → verify workflow, including ambiguous day/time wording and live-page ordering checks.

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

### Reusable-package sanitation

When the plan, renderer, or template will be shared publicly, scan the **entire publishable tree**—skill text, templates, scripts, tests, README, manifests, and examples—not only the main `SKILL.md`. Replace real traveler names, destinations, repository names, deployment identifiers, dates, accommodation details, and account-specific URLs with fictional neutral examples. Keep required public namespace strings only when they are intentional installation URLs, and distinguish those from leaked trip data rather than weakening the scan globally.

See `references/reusable-travel-artifact-sanitization.md` for a compact release gate.

**Completion criterion:** a case-insensitive tree scan finds no private or destination-specific trip material, and every remaining personal/account identifier is explicitly required for public installation or attribution.

## Phase 5 — Verify the Artifact

Use `references/renderer-verification.md` for the full fail-closed input boundary, adversarial fixture matrix, deterministic output contract, and browser-review checklist.

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

1. Read the latest authoritative source and project guidance.
2. Identify affected days, transfers, fixed constraints, adjacent features, and derived/runtime copies.
3. Add or update a relation-based regression for the requested ordering or substitution.
4. Edit the authoritative source only; use JSON for new projects, or preserve the existing tested format.
5. Re-run project validation and generation/synchronization.
6. Inspect the changed day, adjacent transfers, and unaffected private tabs/APIs.
7. Read the actual authenticated page back when the project is deployed and private.
8. Report only the commit, push, synchronization, or deployment actions actually evidenced.

Do not claim the page is updated if only the source changed, if a runtime copy can overwrite it, or if the live page was checked only for HTTP status.

## Common Pitfalls

1. **Duplicated truth:** editing JSON and HTML separately. Fix by regenerating HTML.
2. **False precision:** inventing exact times. Preserve ranges and flexible labels.
3. **List-shaped days:** attractions appear without travel or buffers. Add sequence constraints.
4. **Hidden overload:** every item looks mandatory. Mark lower-priority items optional.
5. **Desktop-first output:** cards become tiny or overflow on phones. Inspect at 360px.
6. **Unsafe rendering:** itinerary text is inserted without escaping. Escape all text and allow HTTPS links only.
7. **Map dependency:** essential instructions exist only in an embedded map. Keep them in text.
8. **Stale HTML:** the page was not regenerated after a plan edit. Compare timestamps or rebuild deterministically.
9. **Brand-only mapping:** a short link is treated as any branch of a chain. Resolve the exact branch, address, and local name before editing.
10. **Redundant station transfer:** a station-connected venue is followed by a fictional second train leg. Model concourse/building/exit continuity explicitly.
11. **Duplicate meal slot:** a named restaurant is added while the generic lunch or dinner remains. Replace the old meal and retime the next activity.
12. **Store hours mistaken for service completion:** an optician, salon, clinic, repair, or fitting stop is scheduled from opening hours alone. Check last acceptance, duration, inventory, pickup cutoff, and same-day completion; put flexible shopping after it and define what gets dropped if it runs long.
13. **Stale waypoint sequence:** text shows a new stop but the walking link still skips it. Update and test both the textual order and map waypoint order.
14. **Competing source migration:** a mature project receives a new `itinerary.json` even though another format is authoritative. Preserve the tested format or perform an explicit migration with the user's approval.
15. **Runtime-only edit:** the deployed copy is changed while a source-sync job will overwrite it. Modify the authority, rebuild/synchronize, and verify source/runtime equivalence.
16. **Status-only production check:** a private page returns 200 but the changed day is stale or ordered incorrectly. Read authenticated content and assert exact markers and absence of replaced content.
17. **Adjacent feature regression:** an itinerary change breaks authentication, navigation, expense views, or another tab. Run the existing project tests and verify unaffected protected routes before completion.
18. **Filtered ledger masquerading as separation:** trip expenses are only a category in the ordinary ledger. Use independent persistence when the user requires separation.
19. **Mixed-currency total:** unlike currencies are added without an explicit conversion policy. Keep totals separate and label every currency.
20. **Example record pollution:** hypothetical expenses are written to the real ledger to demonstrate the UI. Use fixtures or temporary preview data.
21. **Unified trip view erases ordinary ownership:** hiding travelers in the itinerary also removes person attribution from the household ledger. Limit unification to the requested trip view.

## Verification Checklist

- [ ] One canonical or otherwise authoritative itinerary source exists.
- [ ] Existing projects preserve their tested source format instead of gaining a competing plan file.
- [ ] Dates, timezone, bases, and fixed constraints are explicit.
- [ ] Transfers, buffers, optional items, and uncertainty are represented.
- [ ] JSON validation passes when JSON is the authority; otherwise the project's native validation passes.
- [ ] HTML is regenerated or synchronized from the current authoritative source.
- [ ] Source, build output, and runtime copies are identified and equivalent.
- [ ] Dynamic text is escaped and links are HTTPS-only.
- [ ] All days and items appear exactly once.
- [ ] Relation-based tests protect changed order, substitutions, and map waypoints.
- [ ] Adjacent authenticated tabs, APIs, manifests, and independent data stores remain intact.
- [ ] Trip and ordinary expense ledgers have distinct persistence boundaries when separation is required.
- [ ] Trip expenses cannot change ordinary record counts or totals, and ordinary expenses cannot change trip totals.
- [ ] Each currency is totaled separately unless a documented conversion policy exists.
- [ ] Unified trip views hide traveler fields only where requested and do not erase ordinary-ledger ownership.
- [ ] Expense notes and other record-derived values are safely escaped; empty and fixture-backed non-empty states are tested.
- [ ] Source and runtime expense snapshots match after excluding only approved variable metadata.
- [ ] Desktop, 360px mobile, keyboard, and print checks pass when rendering changed.
- [ ] The real authenticated page contains the requested content; private unauthenticated access remains denied.
- [ ] No destination-specific or private trip data is embedded in reusable templates.
- [ ] Commit, push, synchronization, and deployment claims are backed by actual evidence.
