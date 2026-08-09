"""capability_renderer — the Capability Engine report-rendering package.

A reusable Python package (not just "the renderer") that produces
mission cards today and is architected to produce nutrition reports,
blood-pressure summaries, race previews, and any future Capability
Engine report type using the same panel-based architecture. See
render.py for the top-level entry point and panels/ for how to add a
new report section.
"""
from .theme import VERSION, CARD_LAYOUT_VERSION

__version__ = VERSION
__all__ = ["VERSION", "CARD_LAYOUT_VERSION"]
