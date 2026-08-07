# Existing Itinerary Project Workflow

Use this procedure when the itinerary already lives inside an application, repository, generated site, or authenticated companion page.

## 1. Discover the authority boundary

Before editing, inspect project guidance and identify:

- the authoritative itinerary source and its format;
- whether the visible HTML is generated or intentionally hand-maintained;
- source, build output, and runtime/deployed copies;
- existing regression tests and render/deploy commands;
- authentication and allowed-user boundaries;
- adjacent tabs, APIs, manifests, and data stores that must remain intact.

Do not introduce `itinerary.json` merely because this skill recommends it for new projects. If the existing application intentionally stores itinerary facts in JavaScript, YAML, a database, or another tested structure, preserve that authority unless the user requests a migration.

**Completion criterion:** one source of truth is named, every derived/runtime copy is identified, and no competing plan file has been created.

## 2. Synchronize safely

When version control is present:

1. inspect the branch, worktree, and remote state;
2. preserve unrelated local changes;
3. fast-forward before editing when project policy permits;
4. re-read affected files after any pull or background synchronization;
5. obtain required approval before commit, push, publication, or production deployment.

Runtime directories may be overwritten by scheduled synchronization. Never treat a writable deployed copy as authoritative without evidence.

**Completion criterion:** edits start from the latest permitted source revision and no unrelated change is overwritten.

## 3. Add a relation-based regression first

Protect behavior rather than HTML formatting. For the affected day assert:

- the exact venue and user-provided map URL are present;
- ordered stops appear in the intended sequence;
- replaced generic meals or duplicate venues are absent;
- same-station continuity and service-time uncertainty remain explicit;
- adjacent days retain their intended anchors.

Keep project-specific tests in the project, not in this reusable skill.

**Completion criterion:** the regression fails before the implementation and passes only after the requested source change.

## 4. Edit the authoritative source

Make the smallest coherent change:

- update route summary, notes, ordered stops, map waypoints, and translated labels together;
- shift following times when dining, transport, fitting, pickup, or queue duration changes;
- keep dynamic text escaped and external links HTTPS-only;
- preserve unrelated navigation, authenticated APIs, expense views, and companion features;
- avoid silently moving records between independent data stores.

**Completion criterion:** visible text, structured ordering, links, and fallback guidance all describe the same plan.

## 5. Build and synchronize derived artifacts

Run the repository's existing generation or install command. If source and runtime are separate:

1. regenerate or copy using the documented mechanism;
2. compare hashes or normalized content;
3. wait through any known synchronization interval when overwrite risk exists;
4. confirm the runtime still matches the authoritative source.

Do not hand-edit both copies independently.

**Completion criterion:** every derived copy is reproducibly sourced from the authoritative file and remains synchronized.

## 6. Verify the real protected page

A successful HTTP status alone is insufficient. Using an approved authenticated session:

- fetch or open the actual route;
- select the changed day or tab;
- assert the exact new content and ordered markers;
- confirm replaced content is absent;
- inspect at phone width when layout changed;
- verify unauthenticated access remains denied when the page is private;
- never print session secrets, cookies, tokens, or allowlists.

**Completion criterion:** the authenticated live artifact contains the requested order, privacy controls still hold, and verification exposes no credentials.

## 7. Report evidence

Report:

- the chosen date/time and resulting sequence;
- uncertainty that still requires reconfirmation;
- authoritative and runtime artifacts changed;
- tests, script checks, visual checks, and live read-back performed;
- version-control or deployment actions actually completed.

Never claim commit, push, synchronization, or production success without the corresponding tool evidence.
