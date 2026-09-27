"""PDF renderer factory."""

from __future__ import annotations

from ent.integrations.pdf.base import PdfRenderer
from ent.integrations.pdf.weasyprint import WeasyPrintRenderer


def get_pdf_renderer() -> PdfRenderer:
    return WeasyPrintRenderer()
