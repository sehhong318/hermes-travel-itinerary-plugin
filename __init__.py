"""Hermes plugin that bundles the travel itinerary builder skill."""

from pathlib import Path


def register(ctx):
    """Register the bundled skill under this plugin's namespace."""
    skill_md = Path(__file__).parent / "skills" / "travel-itinerary-builder" / "SKILL.md"
    ctx.register_skill("travel-itinerary-builder", skill_md)
