# Hermes Travel Itinerary Plugin

A destination-neutral Hermes plugin for two jobs:

1. turn travel requirements into a realistic canonical itinerary; and
2. render that itinerary as a self-contained, phone-friendly HTML page.

It contains **no private trip data**, destination-specific instructions, hosting setup, authentication logic, or expense tracking.

## What is included

```text
plugin.yaml
__init__.py
skills/travel-itinerary-builder/
├── SKILL.md
├── scripts/render_itinerary.py
└── templates/itinerary.example.json
```

The renderer uses only the Python standard library. It validates dates, required fields, item types/statuses, time ordering, duplicate days, trip-range boundaries, finite JSON, and HTTPS-only links before writing HTML atomically.

## Install as a Hermes plugin

```bash
hermes plugins install https://github.com/sehhong318/hermes-travel-itinerary-plugin.git
hermes plugins enable travel-itinerary
```

Start a fresh Hermes session, then load the bundled skill explicitly:

```text
/skill travel-itinerary:travel-itinerary-builder
```

Plugin-bundled skills are namespaced and read-only. This avoids collisions with local or built-in skills.

## Install only the skill

```bash
hermes skills install https://raw.githubusercontent.com/sehhong318/hermes-travel-itinerary-plugin/main/skills/travel-itinerary-builder/SKILL.md
```

The plugin package is useful when you want versioned distribution. Installing only the skill is simpler when no plugin namespace is needed.

## Generate an itinerary

```bash
cp skills/travel-itinerary-builder/templates/itinerary.example.json itinerary.json
python3 skills/travel-itinerary-builder/scripts/render_itinerary.py itinerary.json itinerary.html
python3 -m http.server 8000
```

Open `http://localhost:8000/itinerary.html` and inspect both desktop and phone widths.

## Development

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile __init__.py skills/travel-itinerary-builder/scripts/render_itinerary.py
```

## Privacy

The examples are fictional. Keep real traveler names, exact movements, reservation references, and accommodation details out of a public repository unless the travelers explicitly approve publication.

## License

MIT
