---
name: tabelog-budget-food-research
description: "Use when finding ¥1-5k Japan restaurants on Tabelog."
version: 1.0.0
platforms: [macos, linux]
metadata:
  hermes:
    tags: [japan, tabelog, restaurants, budget, google-sheets, hyperlinks, itinerary, food-map]
    category: productivity
    requires_toolsets: [terminal]
---

# Tabelog Budget Food Research + Sheets Output

Two coupled workflows for Japan trip food planning at everyday budgets (¥1k-5k),
plus the Google Sheets output patterns that survived user review. The Tabelog
Award Silver list is the WRONG tool for budget meals (Silver ≈ ¥15k-80k) — use
the main-search flow here instead. For the award-tier list see the
`jp-restaurant-search` skill.

## 1. Budget-tier Tabelog search (¥1k-5k, EN domain, curl-only)

The EN domain `tabelog.com/en/...` is NOT Akamai-gated; the `/ja/` domain IS
(returns a "Just a moment..." challenge). No browser/proxy needed for the
listing pages.

```bash
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
ENC=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$QUERY")
curl -s -L -A "$UA" "https://tabelog.com/en/${AREA}/rstLst/?vs=1&sa=${ENC}&sk=&lid=hd_search1&vac_net=1&sw=${ENC}&srt=rt&svd=20260824&svt=1900&svps=2" -o /tmp/tb.html
```

Parse result cards (`<div class="list-rst js-bookmark">`), all fields inline:
- name: `list-rst__rst-name-target`
- rating: `c-rating__val` (e.g. `3.50`)
- **dinner/lunch budget (the key field):** `aria-label="Average dinner price"` /
  `aria-label="Average lunch price"` followed by `<span class="c-rating-v3__val">JPY 3,000 - JPY 3,999</span>`
- detail URL: `data-detail-url="..."`
- genre + station: `list-rst__area-genre`

Filter client-side on parsed ranges. `LstCos=` in the URL is a COURSE-price
filter, not a dinner-budget filter — it does not pin results to ¥1-5k.

## 2. Kanji names + closure check (Google Places API)

EN Tabelog pages show romaji only. Get the 日本語名 via Places API with a
Japanese textQuery + `languageCode:"ja"`; check `businessStatus` for closures.
User preference: restaurant entries are `English Name (日本語名)` + kanji
location — never romaji-only.

## 3. Rate limiting (learned the hard way)

- Rapid sequential detail-page fetches → Tabelog serves a cached "Dining Hida"
  placeholder page for EVERY URL. Check `<title>` after each batch.
- **Pace `sleep 4-5` between requests.** Retry once after a longer sleep (10-20s)
  on the failed page before giving up.
- Prefer ONE search page fetch + client-side filtering over many small fetches.
- Google Places API: batch with ~0.3s sleeps; the free tier rate-limits fast.
- Wikipedia REST API for photos: ~0.4s+ sleeps, retry 429s (rate limit is
  aggressive — do 3 attempts with 8-10s backoff).

## 4. How pricing ranges are decided (user-verified decision logic)

Tiers are set BEFORE searching (user brief), then applied as filters:

| Tier | Range | Use when | Examples |
|---|---|---|---|
| Budget | ¥1,000-3,000 | casual eats, street food, lunch | ramen, takoyaki, gyoza, kaiten sushi, curry, obanzai |
| Mid | ¥3,000-5,000 | most dinner picks, wagyu yakiniku | yakiniku, sushi kappo, izakaya, Italian |
| Splurge | ¥5,000+ | special meals only, flagged not filtered | Kobe beef, kaiseki, Tendan |

Decision rules (state these to the user):
- Pick `D¥3-5k` (dinner) OR `L¥1-3k` (lunch) ranges per the day's meal slot.
- Weigh ⭐ rating (≥3.4 decent, ≥3.5 good, ≥3.6+ excellent), review count
  (higher = more reliable), and per-meal ¥ value.
- Budget tier ≠ low quality: 中谷堂 mochi ¥300-800, 蛸之徹 takoyaki ¥1-2k are
  must-eats at budget prices.
- Each day needs 3+ ⭐ must-eats (web_search famous dishes → verify on Tabelog
  detail → Places closure check) plus 2-5 regular picks.

## 5. Food categories (standard taxonomy for the Food Map)

Classify every pick into a category so days have variety (never two same-category
dinners in a row):

```
Yakiniku/BBQ, Sushi, Yakitori, Izakaya, Italian, French, Seafood,
Tempura, Unagi, Soba/Udon, Ramen, Okonomiyaki/Takoyaki, Kushikatsu,
Curry, Sweets/Matcha, Oden, Obanzai, Gyoza, Beer Bar
```

## 6. Google Sheets output patterns (user-verified)

### Food map layout
- Organize by day → price tier sections (`DAY 2 GION — ¥3-5k`), uniform header
  format, every day needs 3+ ⭐ must-eats.
- Columns: Day/Tier | Restaurant (日本語名) | Category | Location/Budget | Tabelog link.
- **Never append new rows at the bottom** — put them under their day's section;
  orphan rows at the end are a user-visible failure ("Bro don't append at the end").
- After any rewrite, reset the used range to white, re-apply headers by CONTENT
  (row starts with `📅`/`DAY`), never by assumed row indices — day blocks vary in height.

### Real clickable hyperlinks (the working method)
- ❌ `=HYPERLINK(url,label)` formulas — evaluate on desktop, unreliable on mobile.
- ❌ `CellData.hyperlink` field in updateCells — read-only in the Sheets API.
- ✅ Plain string value + link in the cell's text format via `updateCells`:
  `userEnteredFormat.textFormat.link.uri` + blue `foregroundColor` + `underline:true`.
- Link URL: `https://www.google.com/maps/search/?api=1?query=<urlencoded>` (no key).
- Verify by reading back
  `sheets().get(... fields="sheets.data.rowData.values(userEnteredFormat.textFormat.link)")`.
  Note: the top-level `hyperlink` key reads back NONE even when the link works —
  that is expected, not a failure.

### Itinerary rows: transport columns (user-verified Aug 2026)
Transport rows in the day itinerary get TWO extra columns beyond the base
layout — `🚇 Line/Station (code)` and `⏱ Frequency`:
- Line/station with codes: `御堂筋線 M20→M16`, `京阪本線 KH38→KH36`,
  `近鉄奈良線 A01→A28`, `南海空港線 NK01→NK31`, `長堀鶴見緑地線 N15→N12`.
- Codes are LINE-SPECIFIC: Osaka Metro letter+number (M/C/N), Keihan KH,
  Kintetsu A, Nankai NK; JR lines have no station codes — just the line name
  (JR京都線 新快速). Verify via the Transit API suggest when unsure (it returns
  feed-qualified ids like `osakametro-rail:大阪市高速電気鉄道-御堂筋線-梅田`).
- Frequency from typical headway: Midosuji every 3-5 min, Keihan 5-10, JR
  Kyoto/Kobe/Sagano 15-30, Kintetsu Nara 20-30, Nankai Rapi:t 30, city bus 10-20.
- Non-transport rows leave these columns blank. Color coding: optional=gray,
  planned=white, day header=blue.

## Pitfalls

- **Verifying a NAMED restaurant:** `sa=` fuzzy search often returns unrelated
  cached results for multi-word names. Use `web_search` for the exact Tabelog
  URL (e.g. `"Kushi no Bo" Umeda tabelog 串の坊`), then fetch the detail page
  directly — EN detail pages also load with plain curl. Budget parse on detail:
  `JPY ([0-9,]+) ?- ?(?:JPY )?([0-9,]*)` (first ~6 unique ranges = dinner/lunch).
- **`sa=` anchoring fails for multi-word/non-place queries** ("Universal City",
  "Kyoto Station" → empty/stale). Plain area names (Umeda, Gion, Namba,
  Sannomiya) work.
- **Genre-code URL paths** (`rstLst/RC0901/` = ramen) ignore the `sa=` anchor and
  return prefecture-wide top-rated — don't trust for area+genre combos.
- **`Pg=` page param is ignored** — the listing returns page 1 again.
- **Kitashinchi/Umeda Sky high-end districts** are mostly ¥15k+; skip when the
  brief is ¥1-5k.
- **Shared dict keys across days** (e.g. "Recovery buffer" on Day 1 AND Day 3)
  silently overwrite each other in a location lookup map — key on day+activity,
  then verify.
- **Chained row insertion**: inserting fillers anchored to OTHER filler rows in a
  single pass silently skips them — use multi-pass "insert until no change" loops.
- **Sheets API `updateCells` with `fields:"*"` on a range clears formatting on
  every sheet in the request** — scope clears to the intended sheetId only.

## Verification

- Spot-check 2-3 parsed rows: name + rating + price range all present, URL resolves.
- After writing a sheet, read back the Location column formatted values to confirm
  labels rendered and links attached.
- Run a gap check (`>`30 min between consecutive item end times) after any
  itinerary rewrite — every slot should have a fixed or optional activity.
