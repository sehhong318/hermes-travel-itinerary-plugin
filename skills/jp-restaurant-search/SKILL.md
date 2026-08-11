---
name: jp-restaurant-search
title: Tabelog Award Silver Restaurant Search
description: >-
  Enumerate Tabelog Award Silver winners (curated top-100), filter by
  prefecture/city + cuisine + lunch availability + lunch price ceiling + rating
  threshold, and report whether each survivor accepts online reservations
  directly on tabelog.com (vs. phone/email only). Read-only.
website: tabelog.com
category: restaurants
tags:
  - restaurants
  - reservations
  - japan
  - tabelog-award
  - read-only
  - akamai
recommended_method: browser
verified: true
proxies: true
---

# Tabelog Award Silver Restaurant Search

## Purpose

Enumerate Tabelog Award Silver winners, filter by user-supplied criteria
(prefecture/city, cuisine genre, rating threshold, lunch availability, lunch
price ceiling), and for each survivor report whether the restaurant accepts
**online reservations directly on tabelog.com** (vs. phone/email only). Returns
a structured list with rating, lunch budget, dinner budget, business hours, and
`bookable_online_via_tabelog` boolean. Read-only — never submits a reservation.

The Silver tier is a fixed 100-restaurant curated list published annually at
`award.tabelog.com/en/restaurants/silver` (Bronze, Gold, etc. live at sibling
paths). Because the Silver list is *already* the curated top-N, "top 100 in
Silver" is satisfied automatically — the rating ≥ 3.8 check is still applied as
a per-restaurant filter (every Silver winner observed in 2026 had rating ≥ 4.0,
but the data is read from the detail page so the user's threshold is
enforceable).

## When to Use

- "Find me the best French restaurants in Tokyo open for lunch under ¥50,000
  that I can book on Tabelog directly."
- Concierge / trip-planning agents narrowing a Tabelog Award shortlist to a city
  + cuisine + lunch budget.
- Any query of the form "Silver/Gold/Bronze + prefecture + genre +
  lunch-or-dinner + price ceiling + bookability."

For non-award restaurants (i.e. any Tokyo Sushi, not just Silver winners), use
the main Tabelog search at
`tabelog.com/en/{prefecture}/rstLst/{cuisineCode}/?vac_net=1&srt=rt` instead —
but that surface is paginated 20-per-page across hundreds of thousands of
results and is a different skill (`tabelog-budget-food-research` covers the
¥1k-5k budget tier via the EN main-search flow).

## Workflow

### 1. Stealth + residential-proxy Browserbase session

```bash
sid=$(browse cloud sessions create --keep-alive --proxies --verified \
  | node -e "let s='';process.stdin.on('data',c=>s+=c).on('end',()=>process.stdout.write(JSON.parse(s).id))")
export BROWSE_SESSION="$sid"
```

Tabelog will serve a CAPTCHA / soft-block from cloud IPs without
`--proxies --verified`. Verified Akamai-friendly residential is the only
configuration that works consistently. A bare session typically loads the home
page but stalls on restaurant detail pages with a "checking your browser"
interstitial.

### 2. Enumerate the Silver award list

There are exactly **100 Silver winners** per cycle (the page is not paginated —
all 100 cards are present in the initial HTML, but a few are below the fold and
only become `is-visible` after a short scroll-into-view animation):

```bash
browse open "https://award.tabelog.com/en/restaurants/silver" --remote --session "$sid"
browse wait load --remote --session "$sid"
browse wait timeout 2500 --remote --session "$sid"     # let lazy-load images settle
browse press End --remote --session "$sid"             # nudges any virtualized items
browse wait timeout 1500 --remote --session "$sid"
browse get html body --remote --session "$sid" > /tmp/silver.html
```

To target other award tiers, swap the path segment: `gold` (~30 winners),
`bronze` (~250), `new` (Best New Entry), `regional`, `chefsgold`. Same HTML
schema across all six pages.

Parse each card with this regex (one match per restaurant):

```javascript
const cardRe = /<li class="award-rstlst__item[^"]*"[^>]*>([\s\S]*?)<\/li>/g;
// inside each card:
const url       = match[1].match(/href="(https:\/\/tabelog\.com\/en\/[^"]+)"/)[1];
const name      = match[1].match(/<div class="award-rstlst__rst-name">\s*([^<]+?)\s*<\/div>/)[1];
const areaGenre = match[1].match(/<div class="award-rstlst__area-genre">\s*([^<]+?)\s*<\/div>/)[1];
// areaGenre is always "{Genre} / {Prefecture}", e.g. "French / Tokyo"
const badges    = [...match[1].matchAll(/award-rstlst__award-label is-([a-z\-]+)"><span>([^<]+)</g)].map(m=>m[2]);
// badges may be ["SILVER"], ["SILVER","BEST NEW ENTRY"], or include "Club10-4"
```

### 3. Client-side filter by prefecture + genre

`area_genre` is a single string `"{Genre} / {Prefecture}"`. Tokenize on ` / `.
Both fields are English-canonical regardless of locale — Tabelog normalizes
them on this page. Genre strings observed in 2026 Silver:

```
Japanese Cuisine, Sushi, Seafood, Tempura, French, Italian, Spanish,
Innovative, Creative cuisine, Chinese Cuisine, Steak/Teppanyaki,
Yakiniku/Meat dishes (shown as "Yakiniku" on cards), Yakitori/Poultry
(shown as "Yakitori"), Tonkatsu/Fried foods, Unagi, Soba, Udon, Izakaya,
Asian/Ethnic/Curry, Ramen, Other
```

Match the user's "cuisine type" against these with a case-insensitive substring
rule (Tabelog's "Italian" vs. user's "italian"/"Italian food"/"Italian cuisine"
all match). For prefecture, accept either prefecture name (`Tokyo`) or a nested
city/ward (`Shibuya`, `Ebisu`) — the latter requires checking the URL slug
instead, since the card only shows prefecture-level granularity. See gotcha on
"city vs prefecture" below.

Distribution in 2026 Silver (sanity-check expectations):

| Prefecture | Silvers | | Genre | Silvers |
|---|---|---|---|---|
| Tokyo | 49 | | Japanese Cuisine | 21 |
| Kyoto | 7 | | Sushi | 15 |
| Osaka, Fukuoka | 3 each | | French | 9 |
| Saitama, Kanagawa, Saga, Ehime, Gunma | 2 each | | Chinese Cuisine | 7 |
| 15 others | 1 each | | Innovative | 6 |
| | | | Italian | 5 |

If the user asks for `Tokyo + Italian` you'll get **exactly 1 restaurant**
(Megriva). Don't panic — that's the dataset.

### 4. For each surviving restaurant, fetch the detail page and extract metadata

```bash
browse open "$url" --remote --session "$sid"
browse wait load --remote --session "$sid"
browse wait timeout 2500 --remote --session "$sid"
browse get markdown body --remote --session "$sid" > /tmp/detail.md
TITLE=$(browse get title --remote --session "$sid")
```

Extract the four fields from the markdown:

- **Rating** — regex
  `/\*\*([0-9]\.[0-9]+)\*\*\s*\n[\s\S]{0,30}(Excellent|Very good|Good|Average|Below average)/`.
  The first group is the 0.00–5.00 score (e.g. `4.43`); the second is Tabelog's
  qualitative label. Every Silver winner observed scored ≥ 4.00, so a `>= 3.8`
  filter passes them all — but **enforce it anyway** because users may pass
  higher thresholds (e.g. ≥ 4.3).

- **Budget block** — locate the literal `Budget` heading, then take the next two
  `[JPY ... ](url#price-range)` links. **The first is Dinner, the second is
  Lunch.** (Order is fixed — there are also `<img alt="Dinner">` and
  `<img alt="Lunch">` icons in the snapshot tree for verification.) Either may
  be absent — Lunch is missing for dinner-only restaurants.
  - Parse the JPY string into a `max_lunch_price` integer for the `<50,000`
    check. `"JPY 30,000 - JPY 39,999"` → 39999. `"JPY 100,000 -"` (open-ended
    upper) → treat as ≥ 100000 (does NOT pass `<50k`).

- **Business hours** — in the snapshot tree, the row labeled `Business hours`
  contains a list with `StaticText: Lunch` and `StaticText: Dinner` subheadings,
  followed by hour ranges. Lunch presence here is more authoritative than the
  budget-block lunch field for the "open for lunch?" filter. Some restaurants
  have lunch budget listed but are weekend-only-lunch (e.g. Joël Robuchon:
  "Lunch · Last entry at 12:30 (Open only on weekends and public holidays)").
  Decide whether weekend-only-lunch satisfies the user's intent — default to
  "yes, this counts as open for lunch."

- **Bookable online via Tabelog** — the single most reliable signal is the
  **page `<title>`**:
  - If the title contains ` Reservation - ` (note the leading/trailing spaces),
    the restaurant is bookable directly on Tabelog. Examples: `"Bia Reservation
    - Nogizaka/Innovative | Tabelog"`, `"Bon.nu Reservation -
    Sangubashi/French | Tabelog"`.
  - If the title is just `"{Name} - {Location}/{Cuisine} | Tabelog"`, the
    restaurant is **not** bookable through Tabelog. Examples: `"Gastronomy Joel
    Robuchon - Ebisu/French | Tabelog"`, `"Sushi Akira - Hiro o/Sushi |
    Tabelog"`.
  - Cross-verify against page content: bookable pages contain a
    `<h2>Online reservation</h2>` heading with the literal text `"Instant
    reservations, no phone calls."` directly below. Non-bookable pages have a
    `Reservation availability: Reservations available` row in the Details table
    (= "they accept phone reservations") but no `Online reservation` heading.
    **The `Reservation availability` row is a trap — it says "Reservations
    available" even for phone-only restaurants and is NOT a
    Tabelog-online-booking signal.**

### 5. Apply final filters and emit

For each restaurant, apply:
- `rating >= user.rating_threshold` (default 3.8)
- `area_genre` matches `user.cuisine` (case-insensitive substring)
- `prefecture` (or city, see gotcha) matches `user.city`
- `lunch_budget present AND max_lunch_price <= user.lunch_price_ceiling`
  (50000 by default)
- `bookable_online_via_tabelog` is **reported, not filtered** — the user asks
  whether each survivor is bookable, so include both bookable and non-bookable
  restaurants with the flag set.

Hard-cap the survivor count at 100 (the Silver list is 100; you'll never exceed
it).

### 6. Release the session

```bash
browse cloud sessions update "$sid" --status REQUEST_RELEASE
```

## Site-Specific Gotchas

- **READ-ONLY.** Never click `Reserve` buttons or course-menu booking links on
  detail pages — they begin a real reservation flow. Stop at the "is this
  bookable?" determination.
- **Stealth + residential-proxy is mandatory.** Without `--proxies --verified`,
  restaurant detail pages stall on an Akamai-style "checking your browser"
  interstitial. The award listing page itself loads on a bare session, so a
  partial run with no `--proxies` may *look* like it works for 3 turns and then
  fail on the first detail fetch.
- **"Reservation availability: Reservations available" is NOT an online-booking
  signal.** It only means the restaurant takes reservations by phone or email.
  The discriminator for *Tabelog-direct online booking* is the page title
  containing ` Reservation - ` AND a `<h2>Online reservation</h2>` heading on
  the page.
- **Budget block order is `[Dinner, Lunch]`, never the other way.** If you see
  only one JPY link in the Budget section, check the adjacent
  `<img alt="...">` tag to know which meal it represents.
- **Lunch may be listed in Budget but only served on weekends.** Surface that
  string in the output rather than treating it as a fully-open lunch service.
- **"City" vs. "prefecture" mismatch.** The Silver listing's `area_genre` only
  reports prefecture-level location. If the user passes a city or ward (e.g.
  "Shibuya"), filter further by parsing the URL slug: a restaurant URL like
  `https://tabelog.com/en/tokyo/A1303/A130302/13009310/` encodes Tokyo → A1303
  (Shibuya-Ebisu-Daikanyama area) → A130302 (Ebisu).
- **Genre normalization.** Cards show truncated labels: `Yakiniku/Meat dishes`
  is displayed as `Yakiniku`, `Yakitori/Poultry` as `Yakitori`. User-supplied
  "Wagyu" or "BBQ" should map to `Yakiniku`; "ramen" stays `Ramen`.
- **Award badges can stack.** A restaurant card may carry multiple
  `award-rstlst__award-label is-*` spans, e.g. `is-silver` + `is-new-entry` or
  `is-silver` + a "Club10-4" badge. Collect them all into `badges: string[]`.
- **Award page in-page filter is client-side only.** Adding
  `?genre=sushi&pref=tokyo` to the URL does NOT filter — skip the form entirely
  and filter client-side after parsing.
- **The main Tabelog search is not a viable alternative for "Silver only."**
  There is no Silver-only filter on the main search; the only path to "is this
  restaurant a Silver winner?" is to scrape the award page first and join by
  restaurant URL.
- **Tabelog detail page Japanese-language fallback.** Some fields render as
  Japanese text on the EN page (e.g. address). Keep them as-is; agents
  downstream can translate. The rating, budget, business hours, and
  online-booking signals are all English-rendered.
- **Genre code → cuisine taxonomy mapping (for completeness)** — Tabelog's
  cuisine subcategory codes appear in URL slugs: `RC0201` Japanese cuisine,
  `RC0202` Italian, `RC021101` French, `RC0203` Teppanyaki, `RC0204` Steak,
  `RC130101` Yakiniku, `RC0301` Sushi, `RC0303` Tempura, `RC0305` Unagi,
  `RC0801` Chinese cuisine, `RC0901` Ramen, `RC1101` Cafe/Sweets.

## Expected Output

```json
{
  "query": {
    "city": "Tokyo",
    "cuisine": "French",
    "meal": "lunch",
    "max_price_jpy": 50000,
    "award_tier": "silver",
    "rating_min": 3.8
  },
  "total_silvers_in_tier": 100,
  "candidates_after_filter": 6,
  "restaurants": [
    {
      "name": "Chez Inno",
      "tabelog_url": "https://tabelog.com/en/tokyo/A1302/A130202/13000510/",
      "area_genre": "French / Tokyo",
      "ward_or_neighborhood": "Kyobashi",
      "rating": 4.41,
      "rating_label": "Excellent",
      "lunch_budget": "JPY 15,000 - JPY 19,999",
      "lunch_budget_max_jpy": 19999,
      "dinner_budget": "JPY 30,000 - JPY 39,999",
      "bookable_online_via_tabelog": false
    },
    {
      "name": "Bon.nu",
      "tabelog_url": "https://tabelog.com/en/tokyo/A1304/A130401/13184186/",
      "area_genre": "French / Tokyo",
      "rating": 4.24,
      "lunch_budget": "JPY 50,000 - JPY 59,999",
      "lunch_budget_max_jpy": 59999,
      "lunch_budget_passes_50k_ceiling": false,
      "dinner_budget": "JPY 50,000 - JPY 59,999",
      "bookable_online_via_tabelog": true
    }
  ]
}
```

Edge-case shapes the workflow must emit honestly:

```json
// No restaurants match the filter (e.g. Tokyo + Spanish + Silver = 0)
{ "query": { ... }, "candidates_after_filter": 0, "restaurants": [],
  "note": "No 2026 Silver winners match Tokyo / Spanish." }

// Restaurant has no lunch service at all
{ "name": "...", "rating": 4.39, "lunch_budget": null,
  "dinner_budget": "JPY 30,000 - JPY 39,999",
  "excluded_reason": "no_lunch_service" }

// Restaurant has lunch but exceeds price ceiling
{ "name": "Bon.nu", "lunch_budget_max_jpy": 59999,
  "lunch_budget_passes_50k_ceiling": false,
  "excluded_reason": "lunch_over_50k" }
```
