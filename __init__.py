"""Hermes plugin that bundles the travel itinerary builder and Japan planning skills."""

from pathlib import Path


def register(ctx):
    """Register the bundled skills under this plugin's namespace."""
    skills_dir = Path(__file__).parent / "skills"
    for name in (
        "travel-itinerary-builder",
        "tabelog-budget-food-research",
        "japan-transit-routing",
        "jp-restaurant-search",
    ):
        skill_md = skills_dir / name / "SKILL.md"
        if skill_md.is_file():
            ctx.register_skill(name, skill_md)
