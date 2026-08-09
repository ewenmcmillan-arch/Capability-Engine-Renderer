"""layout.py — the automatic layout engine.

Owns: wrapping text to a width, shrinking a font until text fits,
stacking blocks of content vertically within a height budget, and
returning the coordinates panels should draw at.

Nothing in this module touches a PIL ImageDraw or writes a pixel.
Every function here is pure: given text/sizes/boxes in, it returns
lines/positions/coordinates out. graphics.py does the actual drawing
from what this module computes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from . import typography


@dataclass
class TextBlock:
    """A positioned, pre-wrapped piece of text ready for graphics.py."""
    lines: List[str]
    x: int
    y: int
    size: int
    bold: bool = False
    condensed: bool = False
    line_gap: int = 6

    @property
    def height(self) -> int:
        if not self.lines:
            return 0
        # Matches the original renderer's draw_wrapped(): y advances by
        # (size + line_gap) for every line including the last, so the
        # next block starts one full line_gap further down than a
        # "tight" bounding box would suggest. Kept deliberately for
        # pixel parity with the locked v1.2 layout — see CHANGELOG.
        return len(self.lines) * (self.size + self.line_gap)


def wrap_text(
    value: str,
    max_width: float,
    size: int,
    bold: bool = False,
    condensed: bool = False,
    max_lines: Optional[int] = None,
) -> List[str]:
    """Wrap value into lines that fit max_width at the given font size.

    Truncates with an ellipsis if max_lines is exceeded, same
    behaviour as the locked v1.2 renderer.
    """
    f = typography.get_font(size, bold, condensed)
    words = str(value).split()
    lines: List[str] = []
    current = ""
    for word in words:
        trial = (current + " " + word).strip()
        if typography.text_width(trial, f) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    if not lines:
        lines = [""]

    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines[-1] and typography.text_width(lines[-1] + "…", f) > max_width:
            lines[-1] = lines[-1][:-1]
        lines[-1] += "…"
    return lines


def fit_font_size(
    value: str,
    max_width: float,
    max_size: int,
    min_size: int = 10,
    bold: bool = False,
    condensed: bool = False,
) -> int:
    """Shrink a font size in steps of 1 until value fits on one line.

    Used for single-line fields (e.g. a score or a title) that must
    not wrap. Returns min_size if it still doesn't fit at the floor —
    callers should combine this with wrap_text as a second line of
    defence rather than assume a guaranteed fit.
    """
    size = max_size
    while size > min_size:
        f = typography.get_font(size, bold, condensed)
        if typography.text_width(value, f) <= max_width:
            return size
        size -= 1
    return min_size


def stack_blocks(
    items: Sequence[str],
    x: int,
    start_y: int,
    width: float,
    size: int,
    bold: bool = False,
    condensed: bool = False,
    line_gap: int = 6,
    block_gap: int = 5,
    max_lines_per_item: Optional[int] = None,
    max_items: Optional[int] = None,
) -> List[TextBlock]:
    """Lay out a vertical list of text items, each independently wrapped.

    Returns one TextBlock per item with its computed y position, so
    callers never do running-y bookkeeping by hand.
    """
    blocks: List[TextBlock] = []
    y = start_y
    for item in list(items)[: max_items or len(items)]:
        lines = wrap_text(item, width, size, bold, condensed, max_lines_per_item)
        block = TextBlock(lines=lines, x=x, y=y, size=size, bold=bold, condensed=condensed, line_gap=line_gap)
        blocks.append(block)
        y += block.height + block_gap
    return blocks


def budget_panel_height(blocks: Sequence[TextBlock], padding_bottom: int = 16) -> int:
    """Return the y-coordinate immediately below the last block.

    Panels use this to decide whether stacked content overflows
    their fixed box, or (in a future responsive layout) to size the
    box to its content.
    """
    if not blocks:
        return 0
    last = blocks[-1]
    return last.y + last.height + padding_bottom
