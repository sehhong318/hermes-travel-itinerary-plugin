# Travel Expense Integration

Use this optional module when the traveler wants trip-specific expenses visible inside an itinerary or private companion page.

This is not a general accounting system. Its job is to keep travel expenses correctly isolated, summarized, rendered, and verified alongside the itinerary.

## 1. Define the ledger boundary

Before writing data, identify:

- the ordinary or household expense ledger;
- the trip-specific ledger or namespace;
- the trip expense API or generated snapshot;
- whether traveler attribution is required or the trip uses a unified group view;
- supported currencies and any explicit conversion policy;
- who may submit, view, edit, or delete records.

Never implement a “trip view” as a filter over the ordinary ledger when the user requires real separation. A derived category is not an independent ledger.

**Completion criterion:** ordinary and trip records have distinct persistence boundaries, ownership rules, and totals.

## 2. Use a minimal auditable record

A trip expense should normally preserve:

- stable unique ID;
- expense date in the trip timezone;
- decimal amount stored without binary floating-point arithmetic;
- ISO currency code;
- category;
- purpose or note;
- payment method when supplied;
- reporter and recorded timestamp when auditability requires them.

Traveler attribution may be omitted from the visible trip view when the user wants a unified group total. Do not remove attribution from an unrelated ordinary ledger merely because the itinerary view is unified.

Treat examples and hypothetical fixtures as non-production data. Only write a real record when the user clearly reports an actual expense.

**Completion criterion:** every persisted row is attributable to an actual report, has an unambiguous currency, and can be deduplicated.

## 3. Route expense messages safely

Route a message to the trip ledger only when both are true:

1. it is clearly an expense report with an amount or structured expense context; and
2. it explicitly identifies the trip, destination, or trip-expense scope according to the project's rule.

Do not scan itinerary prose for destination words and turn it into spending. Do not infer currency solely from a payment brand. If currency or ledger scope is materially ambiguous and cannot be retrieved, ask before writing.

When identity is known, apply the project's reporter mapping. Ask only for reimbursements, reports on another person's behalf, forwarded receipts, or genuinely ambiguous ownership.

**Completion criterion:** ordinary messages do not enter the trip ledger, trip expenses do not alter ordinary totals, and duplicate submissions are rejected.

## 4. Keep currencies honest

- Sum each currency independently.
- Never add unlike currencies into one grand total.
- Do not convert without an explicit exchange-rate source, effective date, and rounding policy.
- If conversion is requested, preserve both original and converted values plus the policy used.

Use decimal arithmetic and serialize monetary values consistently, normally to two decimal places unless the currency or project requires otherwise.

**Completion criterion:** every displayed total names its currency and can be recomputed exactly from the ledger.

## 5. Integrate the itinerary UI

When requested, add an expense tab or section inside the existing itinerary navigation rather than creating an unrelated public page. Preserve the project's authentication and mobile design.

The view should support:

- totals grouped by currency;
- record count;
- date, amount, currency, category, purpose, and payment method;
- unified or per-traveler presentation according to the brief;
- a clear empty state;
- safe HTML escaping for all record-derived text;
- readable phone layout and no horizontal overflow.

Do not display reporter, traveler, internal IDs, or audit fields unless the user needs them.

**Completion criterion:** the expense view is reachable where the traveler requested, renders zero and non-zero states safely, and does not expose internal data unnecessarily.

## 6. Generate and synchronize snapshots

If CSV, JSON, API output, or runtime copies coexist:

1. update the authoritative trip ledger;
2. regenerate the snapshot using the project service;
3. synchronize runtime copies through the documented mechanism;
4. compare normalized business data while ignoring intentionally variable generation timestamps;
5. keep ordinary and trip snapshots independently testable.

Do not hand-maintain derived totals or edit source/runtime ledgers independently.

**Completion criterion:** source and runtime business data match, and all totals are generated rather than manually typed.

## 7. Regression tests

At minimum prove:

- a trip expense changes only the trip ledger and trip totals;
- an ordinary expense changes only the ordinary ledger and totals;
- unified views do not expose traveler fields;
- currencies remain separate;
- decimal totals and daily/monthly groupings are exact;
- duplicate IDs and malformed amounts are rejected;
- record text is escaped against HTML injection;
- the itinerary expense tab has a safe empty state;
- authenticated API/page access succeeds for approved users;
- unauthenticated private access remains denied;
- source and runtime snapshots agree apart from approved metadata fields.

Use fixtures for non-empty UI tests instead of polluting the real ledger.

**Completion criterion:** a regression would fail if records crossed ledger boundaries, currencies were mixed, or private expense data became public.

## 8. Verify the real artifact

After synchronization:

- fetch the authenticated expense API and locate the exact new record;
- recompute and assert the affected daily, monthly, traveler/group, and currency totals;
- open the itinerary expense tab at phone width when its layout changed;
- confirm ordinary totals and record counts changed only when expected;
- confirm trip record counts remain unchanged after ordinary expenses, and vice versa;
- verify unauthenticated access is denied;
- never print credentials or session material.

**Completion criterion:** the live record, totals, placement, isolation, and privacy boundary are all verified with real output.

## Common pitfalls

1. **Filtered ordinary ledger:** a trip category is presented as separation. Use independent persistence when separation is required.
2. **Mixed-currency grand total:** MYR, JPY, and other currencies are added directly. Keep distinct totals.
3. **Unified UI destroys attribution:** hiding traveler names also removes ordinary-ledger ownership. Limit unification to the requested trip view.
4. **Example pollution:** sample records are written to production to demonstrate the UI. Use fixtures or temporary preview data.
5. **Substring ingestion:** every sentence containing a destination name becomes an expense. Require expense intent and structured amount context.
6. **Unsafe rendering:** notes are inserted with `innerHTML` without escaping. Escape all record-derived values.
7. **Timestamp equality trap:** source/runtime JSON comparisons fail only because `generated_at` differs. Compare normalized business data while still validating timestamp format separately.
8. **Runtime-only record:** the live CSV changes but the authoritative ledger does not. Write the authority and regenerate.
