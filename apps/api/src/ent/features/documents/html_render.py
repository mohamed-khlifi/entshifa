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
) -> str:
    """Fill header, body, and footer. Caller validates placeholders first."""

    header = _ENVIRONMENT.from_string(header_html).render(**data)
    body = _ENVIRONMENT.from_string(body_html).render(**data)
    footer = _ENVIRONMENT.from_string(footer_html).render(**data)
    return (
        "<!DOCTYPE html>"
        f'<html lang="{locale}" dir="{direction}">'
        '<head><meta charset="utf-8">'
        f"<style>{css}</style></head><body>{header}{body}{footer}</body></html>"
    )


def render_from_snapshot(snapshot: dict[str, Any]) -> str:
    """Render only the frozen snapshot. Live template rows are not read."""

    template = snapshot["template"]
    data = snapshot["data"]
    if not isinstance(template, dict) or not isinstance(data, dict):
        msg = "documents.snapshot_shape"
        raise ValueError(msg)
    return render_document_html(
        locale=str(template["locale"]),
        direction=str(template["direction"]),
        header_html=str(template["header_html"]),
        body_html=str(template["body_html"]),
        footer_html=str(template["footer_html"]),
        css=str(template["css"]),
        data=data,
    )
