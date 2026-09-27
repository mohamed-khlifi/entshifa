"""WeasyPrint adapter. Native Pango is required for Arabic shaping."""

from __future__ import annotations

from typing import Any

from ent.integrations.pdf.base import page_css


class WeasyPrintRenderer:
    """HTML and CSS to PDF. Import of WeasyPrint is deferred until render."""

    def render_pdf(
        self,
        *,
        html: str,
        css: str,
        page_setup: dict[str, Any],
        direction: str,
    ) -> bytes:
        try:
            from weasyprint import CSS, HTML
        except OSError as exc:
            msg = "documents.pdf_runtime_missing"
            raise RuntimeError(msg) from exc

        stylesheets = [
            CSS(string=page_css(page_setup, direction)),
            CSS(string=css),
        ]
        document = HTML(string=html).render(stylesheets=stylesheets)
        payload = document.write_pdf()
        if not isinstance(payload, bytes) or not payload.startswith(b"%PDF"):
            msg = "documents.pdf_invalid"
            raise RuntimeError(msg)
        return payload
