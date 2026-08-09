# Hermes Travel Itinerary Plugin

A destination-neutral Hermes plugin for building realistic multi-day itineraries, maintaining existing private itinerary projects, optionally integrating a trip-expense view without mixing travel spending into an ordinary household ledger, emitting styled Google Sheets as an editable source of truth, routing Japan train trips with live times, and researching Japan restaurants on Tabelog at everyday budgets.

## What it covers

- realistic day-by-day planning with transfers, buffers, optional stops, and uncertainty;
- Google Maps short-link resolution and exact branch identification;
- relation-based schedule revisions, including same-station continuity and ordered map waypoints;
- restaurants, services, fittings, pickup cutoffs, and fallback plans;
- new projects using validated JSON and self-contained mobile HTML;
- existing projects with their own authoritative HTML, JavaScript, YAML, database, tests, runtime copy, and authenticated page;
- optional trip-expense integration with independent persistence, separate currency totals, safe rendering, and private live verification;
- Google Sheets sync — styled day tabs, food map, transport legs, reminders, real clickable hyperlinks, and a sync loop back to canonical JSON + mobile HTML;
- Japan transit routing with live departure times (Transit API / MCP) and operator-specific station codes;
- Tabelog food research — budget-tier ¥1k-5k search with rate-limiting discipline, plus the award-tier Silver list;
- complete-tree privacy sanitation before public publication.

The bundled generic renderer remains itinerary-only. The expense module is a workflow for integrating an independent trip ledger into an existing authenticated itinerary project, or for extending the renderer with an explicit private-data boundary and tests. It does not expose a real ledger in a public static page.

## Repository layout

```text
plugin.yaml
__init__.py
skills/
├── travel-itinerary-builder/
│   ├── SKILL.md
│   ├── references/
│   │   ├── existing-itinerary-project-workflow.md
│   │   ├── map-linked-itinerary-revisions.md
│   │   ├── renderer-verification.md
│   │   ├── reusable-travel-artifact-sanitization.md
│   │   ├── travel-expense-integration.md
│   │   └── gsheets-sync-workflow.md
│   ├── scripts/
│   │   └── render_itinerary.py
│   └── templates/
│       └── itinerary.example.json
├── tabelog-budget-food-research/
│   └── SKILL.md
├── japan-transit-routing/
│   ├── SKILL.md
│   └── references/
│       └── transit-api-notes.md
└── jp-restaurant-search/
    └── SKILL.md
tests/
└── test_plugin.py
```

The renderer uses only the Python standard library. It validates dates, required fields, item types and statuses, time ordering, duplicate days, trip-range boundaries, finite JSON, and HTTPS-only links before writing HTML atomically.

## Install as a Hermes plugin

```bash
hermes plugins install https://github.com/sehhong318/hermes-travel-itinerary-plugin.git
hermes plugins enable travel-itinerary
```

Start a fresh Hermes session, then load the bundled skill explicitly:

```text
/skill travel-itinerary:travel-itinerary-builder
```

Plugin-bundled skills are namespaced and read-only. This is the recommended installation because it keeps the skill and all references together.

## Install as an editable local skill

A single raw `SKILL.md` is no longer sufficient because this version uses linked references. Clone the repository and copy the complete skill directory:

```bash
git clone --depth 1 https://github.com/sehhong318/hermes-travel-itinerary-plugin.git
mkdir -p "${HERMES_HOME:-$HOME/.hermes}/skills"
cp -R hermes-travel-itinerary-plugin/skills/travel-itinerary-builder \
  "${HERMES_HOME:-$HOME/.hermes}/skills/"
```

Reload skills or start a new session:

```text
/reload-skills
/skill travel-itinerary-builder
```

## How to use it

### Build a new itinerary

Ask Hermes:

```text
Use travel-itinerary-builder to create a realistic five-day itinerary.
Keep uncertain times flexible, include transfer buffers, and generate a
phone-friendly HTML page after validating the plan.
```

To render the bundled neutral example manually:

```bash
cp skills/travel-itinerary-builder/templates/itinerary.example.json itinerary.json
python3 skills/travel-itinerary-builder/scripts/render_itinerary.py \
  itinerary.json itinerary.html
python3 -m http.server 8000
```

Open `http://localhost:8000/itinerary.html` and inspect desktop and phone widths.

### Revise an existing itinerary project

```text
Use travel-itinerary-builder in existing-project mode. First identify the
authoritative source, generated/runtime copies, current tests, authentication
boundary, and synchronization process. Resolve this map link, add a regression
for the requested stop order, update the source, synchronize runtime, and read
the real authenticated page back before reporting success.
```

This mode preserves an existing tested source format instead of introducing a competing `itinerary.json`.

### Add a private trip-expense view

```text
Use the optional travel-expense module. Keep trip expenses in an independent
ledger from ordinary spending, preserve currencies as separate totals, use a
unified group view, escape all record-derived text, test empty and non-empty
states with fixtures, synchronize the runtime snapshot, and verify the private
itinerary expense tab without exposing credentials.
```

Core expense rules:

- a filtered category in an ordinary ledger is not independent persistence;
- ordinary and trip records must not change each other's counts or totals;
- currencies remain separate unless an explicit conversion policy exists;
- examples and hypothetical records never enter production;
- unified trip presentation must not erase ownership from an unrelated ordinary ledger;
- authenticated content and unauthenticated denial both require verification.

### Emit the itinerary as a styled Google Sheet

```text
Use travel-itinerary-builder in Google Sheets sync mode. Set up the user-owned
OAuth desktop client, create the Day / Food Map / Transport / Reminders tabs,
write rows with real clickable map hyperlinks (textFormat.link), color-code
optional vs planned vs day headers, and provide a sync script that reads the
sheet back into itinerary.json and the mobile HTML.
```

The working hyperlink method is `textFormat.link` via `updateCells` —
`=HYPERLINK()` formulas are unreliable on mobile and the `hyperlink` field is
read-only in the Sheets API. See `references/gsheets-sync-workflow.md`.

### Research Japan restaurants at budget prices

```text
Use tabelog-budget-food-research to find ¥1,000-5,000 restaurants on Tabelog
for a Japan trip. Search the EN domain with curl, filter by dinner/lunch budget
client-side, add kanji names via the Google Places API, pace requests to avoid
rate limiting, and decide price tiers before searching (budget ¥1-3k / mid
¥3-5k / splurge ¥5k+).
```

### Route Japan trains with live times

```text
Use japan-transit-routing to get live Japan train departures. Query the Transit
API (api.transit.ls8h.com) directly or via the japan-transit MCP server, pass
endpoints verbatim, skip pure-walk journeys, and use Japanese station names in
suggest. Include operator-specific station codes (M/C/N for Osaka Metro, KH for
Keihan, A for Kintetsu, NK for Nankai) and typical headways in itinerary sheets.
```

## Development

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile \
  __init__.py \
  skills/travel-itinerary-builder/scripts/render_itinerary.py
```

The tests verify plugin registration, skill metadata and linked files, renderer behavior, fail-closed input validation, public-tree sanitation, and absence of credential-like material.

## Privacy and security

This public repository contains fictional, destination-neutral examples only. It must not contain:

- real traveler names or identity mappings;
- exact private trip routes, accommodation details, or reservation references;
- private repository, application, deployment, API, or filesystem identifiers;
- real expense records, account details, allowlists, cookies, or session material;
- API keys, tokens, passwords, private keys, or connection strings.

A public GitHub owner name in the installation URL is intentional repository metadata, not private trip data.

## License

MIT
