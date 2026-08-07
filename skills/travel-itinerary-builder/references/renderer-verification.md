# Itinerary Renderer Verification

Use this reference when implementing or reviewing a structured-plan-to-HTML renderer. It captures the fail-closed checks that should remain stable across destinations and visual styles.

## Input boundary

Reject the input before writing output when any invariant fails:

- root, `trip`, each day, and each item have the expected object/array type;
- JSON contains no `NaN`, `Infinity`, or `-Infinity`;
- trip dates parse as ISO dates and `start <= end`;
- day dates are unique, sorted for output, and inside the trip range;
- required strings are non-empty strings rather than values coerced with `str()`;
- exact `HH:MM` end times do not precede exact start times;
- item type and status values belong to documented allowlists;
- external links are absolute HTTPS URLs;
- malformed optional fields are rejected or normalized explicitly, never passed through accidentally.

Write atomically: render completely to a sibling temporary file, then replace the destination only after validation and rendering succeed. A failed run must leave an existing good HTML file unchanged.

## Output safety

- Escape every data-derived text node and attribute.
- Construct links only from URLs that passed server-side validation.
- Add `rel="noopener noreferrer"` to new-tab links.
- Avoid required third-party scripts, fonts, styles, or maps.
- Keep essential content in semantic HTML so the plan remains readable with JavaScript disabled.
- Do not embed source paths, private repository names, traveler identities, or generator diagnostics.

## Deterministic content checks

Given the canonical input, assert:

- output begins with an HTML5 doctype and includes UTF-8 and viewport metadata;
- rendered day count equals input day count;
- each day title appears once;
- each itinerary item name appears once;
- date range and timezone match the canonical plan;
- optional/reserved/confirmed states remain visible;
- `javascript:` and insecure external URLs are absent;
- no generated timestamp is included unless the product requires one.

Prefer relation-based assertions over large HTML snapshots. They survive visual redesigns while protecting the data contract.

## Adversarial fixtures

At minimum test:

1. duplicate day date;
2. day outside the trip range;
3. end date before start date;
4. malformed/non-finite JSON;
5. wrong container types;
6. blank required fields;
7. unsupported type or status;
8. exact end time before exact start time;
9. `http:`, `javascript:`, relative, and hostless URLs;
10. text containing `<script>`, quotes, ampersands, and non-Latin characters;
11. empty day item list;
12. failed render while a known-good output already exists.

## Visual review

Inspect the generated file, not a hand-built mockup.

- Desktop: hierarchy, timeline alignment, card rhythm, contrast, and print preview.
- Phone at 360px: no horizontal overflow, readable type without zoom, wrapping for long names/notes, and 44px controls.
- Keyboard: visible focus and logical anchor order.
- Weak/no JavaScript: all essential days and items remain visible.
- Print: navigation may hide, but itinerary content must not.

A renderer is complete only when structural tests and an actual browser inspection both pass.
