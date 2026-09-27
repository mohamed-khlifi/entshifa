"""PDF renderer port (architecture §4)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class PdfRenderer(Protocol):
    def render_pdf(
        self,
        *,
        html: str,
        css: str,
        page_setup: dict[str, Any],
        direction: str,
    ) -> bytes:
        """Return PDF bytes. Must not perform database or storage I/O."""


def page_css(page_setup: dict[str, Any], direction: str) -> str:
    """@page rules from the frozen page setup. Units stay in millimetres."""

    size = str(page_setup.get("size") or "A4")
    orientation = str(page_setup.get("orientation") or "portrait")
    top = int(page_setup.get("margin_top_mm") or 16)
    bottom = int(page_setup.get("margin_bottom_mm") or 16)
    left = int(page_setup.get("margin_left_mm") or 14)
    right = int(page_setup.get("margin_right_mm") or 14)
    return (
        f"@page {{ size: {size} {orientation}; "
        f"margin: {top}mm {right}mm {bottom}mm {left}mm; }}\n"
        f"html {{ direction: {direction}; }}\n"
    )
