# Google Sheets Output Workflow (itinerary → styled sheet)

Emit a trip itinerary to a styled Google Sheet that doubles as the **editable
source of truth** for the itinerary, with a sync loop back to the canonical JSON
and mobile HTML. Verified in production on a real 8-day Japan trip (Aug 2026).

## When to use

- User wants the itinerary "in a spreadsheet" or "in Google Sheets"
- User wants to edit the itinerary themselves and have the web page follow
- Any multi-day trip where a visual, link-rich, color-coded sheet helps

## Architecture: one source of truth, two outputs

```
Google Sheet (user edits)  ──sync script──▶  itinerary.json (canonical)
                                                   │
                                                   ▼
                                          itinerary.html (mobile web)
```

The Google Sheet is the human-editable copy; a small sync script reads it back
into canonical JSON, then the existing renderer produces the mobile HTML. Any
edit in the sheet propagates to the web by re-running the sync script.

## Setup (one-time, per machine)

### 1. Google OAuth (user-owned client — gcloud default client 403s)

The default `gcloud auth` OAuth client is blocked by Google (403
`client_id_mismatch`). The working path is a **user-created desktop OAuth
client**:

1. Google Cloud Console → project → APIs & Services → Credentials →
   **Create OAuth client ID** → Desktop app → download JSON.
2. Copy the JSON to `~/.hermes/google_client_secret.json`
   (iCloud/Downloads are TCC-blocked on macOS — the user must copy the file
   into `~/.hermes` manually).
3. Exchange for a token (scopes: `spreadsheets`, `drive`, plus whatever else the
   sheet needs) → `~/.hermes/google_token.json`.
4. Use with `google-auth` + `google-api-python-client` in a venv
   (`uv venv /tmp/gvenv && uv pip install google-auth google-api-python-client`).

Token refresh: `Credentials(token, refresh_token, client_id, client_secret,
scopes).refresh(Request())` — the refresh happens automatically on first API call.

### 2. Spreadsheet structure (verified layout)

| Tab | Purpose | Columns |
|---|---|---|
| `Day 1-4` / `Day 5-8` | Day-by-day timeline | Time | Activity | 🚇 Line/Station | ⏱ Frequency | Location 🗺️ | Details | Cost |
| `Food Map` | All restaurant picks | Day/Tier | Restaurant (日本語名) | Category | Location/Budget | Tabelog link |
| `Transport` | All verified legs | Leg | Line | Time | Fare |
| `Reminders` | Pre-trip checklist | Category | Item | Details | Cost/Action |

Day-sheet row conventions (user-verified, do not skip):
- **Day header** row: `📅 DAY 1 · Mon 24 Aug — Title` (blue bg, white bold).
- **Column header** row: `Time | Activity | ...` (light blue).
- **Planned** items: white bg. **Optional** items: gray bg
  `rgb(0.95, 0.95, 0.95)` and the activity starts with `(optional)`.
- **Transport rows** get the two extra columns (line/station codes + frequency);
  other rows leave them blank.
- **Location** cells: kanji name + real Google Maps hyperlink (see below).
- No gaps: every time slot must have a fixed or optional activity.

### 3. Real clickable hyperlinks (the ONLY working method)

- ❌ `=HYPERLINK(url,label)` formulas — evaluate on desktop, unreliable on
  mobile, and the user complained links "don't work".
- ❌ `CellData.hyperlink` field in `updateCells` — read-only in the Sheets API
  (reads back NONE even when the link works — that's expected, not a failure).
- ✅ Set a plain string value + attach the link in the cell's text format via
  `updateCells`:
  ```json
  {
    "userEnteredValue": {"stringValue": "関西国際空港"},
    "textFormatRuns": [{
      "startIndex": 0,
      "format": {
        "link": {"uri": "https://www.google.com/maps/search/?api=1&query=Kansai+International+Airport"},
        "foregroundColor": {"red": 0.05, "green": 0.3, "blue": 0.85},
        "underline": true
      }
    }]
  }
  ```
- Link URL: `https://www.google.com/maps/search/?api=1?query=<urlencoded>` (no
  API key needed).
- Verify by reading back
  `sheets().get(... fields="sheets.data.rowData.values(userEnteredFormat.textFormat.link)")`.

### 4. Formatting rules that survived user review

- Apply `repeatCell` formatting by **content**, never by assumed row indices —
  day blocks vary in height (`Day 1-4` headers at rows 1, 16, 31, 46; not a
  fixed stride). Detect `row[0].startswith("📅")` for day headers.
- After any rewrite: first reset the used range to white, THEN re-apply
  headers/optional coloring. Order matters — stale colors from a previous layout
  are a user-visible bug ("glitch with the price category / formatting color").
- Batch API calls: `batchUpdate` in chunks of ~90 requests; one `updateCells`
  with `fields: "*"` per sheet clears that sheet's formatting.
- Column widths via `updateDimensionProperties` (pixelSize): Time 105,
  Activity 200, Line 240, Frequency 110, Location 150, Details 280, Cost 70.

### 5. Rebuild cleanly instead of patching

Incremental row edits over an old layout are the #1 source of sheet glitches
(misaligned links, stale colors, orphan rows). The reliable pattern is:

1. `updateCells` with `fields:"*"` on the whole sheet (wipe everything).
2. Write all rows fresh (`values().update`, `valueInputOption="RAW"`).
3. One pass: repeatCell formatting + updateCells links + dimension widths.

## Food Map specifics (see tabelog-budget-food-research skill)

- Sections per day → price tier: `DAY 2 GION — ¥3-5k`, uniform header format.
- Every day needs 3+ ⭐ must-eats (gold highlight) + 2-5 regular picks.
- **Never append new rows at the bottom** — insert under the day's section;
  orphan rows are a user-visible failure.
- Restaurant names: `English Name (日本語名)` + kanji location.

## Sync script skeleton

```python
# sync_itinerary.py — reads the sheet, writes itinerary.json + itinerary.html
def main():
    sheets = get_sheets()                     # OAuth creds (step 1)
    days = parse_days(sheets)                 # read Day 1-4 + Day 5-8 tabs
    it = build_json(days)                     # canonical itinerary.json
    html = build_html(it, photos)             # reuse travel-itinerary-builder renderer
```

Keep this script next to the canonical JSON (`~/.hermes/travel/`). The user
edits the sheet → re-runs the script → the web page updates. For non-Japan
trips, the same pattern applies with any sheet layout.

## Pitfalls

- **gcloud default OAuth client 403s** — always use the user-created desktop
  client JSON; keep the client secret + token out of the public repo.
- **TCC sandbox** — on macOS, `~/Downloads` and iCloud are unreadable from a
  terminal; have the user copy credential files into `~/.hermes`.
- **`LstCos=` on Tabelog is a course-price filter, not a dinner-budget filter.**
- **`updateCells` with `fields:"*"` clears formatting on every sheet in the
  request** — scope to the intended sheetId only, or you'll wipe sibling tabs.
- **Inserting filler rows anchored to other filler rows** in a single pass
  silently skips them — use a multi-pass "insert until no change" loop.
- **`api.transit.ls8h.com`** provides station codes for transport columns
  (Osaka Metro M/C/N, Keihan KH, Kintetsu A, Nankai NK); see the
  `japan-transit-routing` skill.
