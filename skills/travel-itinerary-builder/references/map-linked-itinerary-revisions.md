# Map-Linked Itinerary Revisions

Use this procedure when a traveler sends a Google Maps short link and asks where or when to add it.

## 1. Resolve before planning

Open the short link and capture the canonical place name, local-language name, category, exact branch, address, current hours, last order/admission time, reservation signal, and map URL. Never infer the branch from the brand name alone.

Treat owner posts and map listings as current-but-changeable facts: record the checked-at context and tell the traveler to reconfirm near departure.

## 2. Compare against the actual itinerary

Read the current canonical day blocks before recommending a date. Choose by geographic clustering and sequence, not merely by city name. Compare:

- same station, station-connected building, or adjacent attraction;
- existing meal at that time;
- luggage/check-in constraints;
- opening/last-order time;
- walking and transfer direction;
- the next fixed activity.

A venue beside an already planned attraction normally belongs on that attraction's day.

## 3. Preserve physical continuity

Do not invent a second train ride when a venue is connected to the same station. Say explicitly:

- arrive at station;
- use the connected building or concourse;
- after the visit, continue within the same station area to the required exit;
- no extra transit is needed.

If Maps returns multiple branches or duplicate-looking results, retain the user's landmark instructions and label the unresolved branch/signage detail instead of asserting false precision.

## 4. Make the schedule substitution complete

When adding a restaurant at a meal time:

1. remove or replace the old generic meal;
2. add realistic travel and dining duration;
3. shift the following attraction if needed;
4. check closing/last-order constraints;
5. keep only one committed meal in that slot.

When the user's wording can reasonably mean both a day and a clock time (for example, “first day” versus “one o'clock”), use the intersection only when it is safe and coherent, state the interpretation, and otherwise clarify.

## 5. Handle time-variable service stops

For opticians, salons, clinics, repairs, fittings, and similar service venues, opening hours alone do not prove the visit is feasible. Capture or explicitly leave unresolved:

- last acceptance time, not just closing time;
- appointment or walk-in requirements;
- expected consultation, fitting, or processing duration;
- inventory or parts availability;
- same-day completion and pickup cutoff;
- whether a return visit is required.

Schedule the service before flexible shopping or sightseeing, reserve a realistic block, and make downstream retail stops removable. Never promise same-day completion when only the storefront hours are known. If the service is on an arrival day, preserve the fixed dinner/transport anchor and shorten optional shopping first when delays occur.

## 6. Encode useful route instructions

A map link should not be the only instruction. Store the text sequence as well: station/exit, turn direction, landmark, ordered shopping or food anchors, destination, and fallback if delayed. A full walking link may use origin, destination, and ordered waypoints. When inserting a new stop, update both the textual order and waypoint order; verify that the visible text remains usable if the link changes.

## 7. Regression and deployment checks

Test the affected day as an ordered block:

- new venue and exact map URL are present;
- replaced generic meal is absent;
- venue precedes/follows the intended attraction;
- station continuity wording is present where relevant;
- current-hours claims are qualified;
- adjacent days do not retain a duplicate venue unintentionally.

Then validate embedded JavaScript, synchronize the runtime artifact, and read the authenticated live page back to confirm content and ordering—not just HTTP 200.
