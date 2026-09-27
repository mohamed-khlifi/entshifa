"""Render a frozen template snapshot to HTML. No storage and no PDF."""

from __future__ import annotations

from typing import Any

from jinja2 import StrictUndefined
from jinja2.sandbox import SandboxedEnvironment

_ENVIRONMENT = SandboxedEnvironment(autoescape=True, undefined=StrictUndefined)


def render_document_html(
    *,
    locale: str,
    direction: str,
    header_html: str,
    body_html: str,
    footer_html: str,
    css: str,
    data: dict[str, Any],
    page_setup: dict[str, Any] | None = None,
) -> str:
    """Fill header, body, and footer. Caller validates placeholders first."""

    from ent.integrations.pdf.base import page_css

    header = _ENVIRONMENT.from_string(header_html).render(**data)
    body = _ENVIRONMENT.from_string(body_html).render(**data)
    footer = _ENVIRONMENT.from_string(footer_html).render(**data)
    sheet = css
    if page_setup is not None:
        sheet = page_css(page_setup, direction) + css
    return (
        "<!DOCTYPE html>"
        f'<html lang="{locale}" dir="{direction}">'
        '<head><meta charset="utf-8">'
        f"<style>{sheet}</style></head><body>{header}{body}{footer}</body></html>"
    )


def render_from_snapshot(snapshot: dict[str, Any]) -> str:
    """Render only the frozen snapshot. Live template rows are not read."""

    template = snapshot["template"]
    data = snapshot["data"]
    if not isinstance(template, dict) or not isinstance(data, dict):
        msg = "documents.snapshot_shape"
        raise ValueError(msg)
    page_setup = template.get("page_setup")
    return render_document_html(
        locale=str(template["locale"]),
        direction=str(template["direction"]),
        header_html=str(template["header_html"]),
        body_html=str(template["body_html"]),
        footer_html=str(template["footer_html"]),
        css=str(template["css"]),
        data=data,
        page_setup=page_setup if isinstance(page_setup, dict) else None,
    )
