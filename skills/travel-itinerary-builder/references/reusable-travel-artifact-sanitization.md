# Reusable travel artifact sanitation

Use this release gate when a trip-planning skill, template, renderer, test suite, or example repository will be public.

## Scope

Scan every text file intended for publication, including:

- `SKILL.md` and linked references;
- templates and generated examples;
- scripts, fixtures, and test assertions;
- README, manifests, CI files, and install commands;
- filenames, repository metadata, and sample URLs.

Scanning only the main skill file is insufficient: private details often survive in fixtures, tests, README examples, or session-reference files.

## Replace

Replace real values with internally consistent fictional values:

- traveler names and group identities;
- destinations and detailed routes from the originating trip;
- exact current/future travel dates;
- hotels, booking references, reservation numbers, and QR identifiers;
- private repository names, deployment apps, hostnames, chat IDs, and allowlists;
- account-specific URLs unless they are intentionally required public install URLs.

Do not merely redact fields into unusable examples. Preserve the schema and relationships with neutral sample data so users can still run the renderer and tests.

## Scan discipline

1. Build a case-insensitive forbidden-term list from the originating private project.
2. Scan the complete publishable tree while excluding only binary files and `.git` internals.
3. Review every hit manually; test code can contain the forbidden literal solely to assert absence, which still means the public tree contains that literal.
4. Remove or generalize such tests rather than globally exempting the file.
5. Treat a required public owner/namespace in install URLs as an explicit reviewed exception, not a reason to remove that identifier from the scan everywhere.
6. Run a separate credential-pattern scan for tokens, private keys, passwords, and bot-token shapes.
7. Clone the published repository into a clean directory and repeat the tests and tree scan against the remote artifact.

## Completion criteria

- No private-trip or destination-specific term remains in the public tree.
- No credential-pattern hit remains.
- Fictional examples still validate and render successfully.
- Required public namespaces are limited to installation/attribution locations and are documented.
- A clean remote clone passes the same tests as the local source.
