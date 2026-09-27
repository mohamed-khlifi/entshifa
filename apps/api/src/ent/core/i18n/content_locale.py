"""Resolve the content locale from HTTP Accept-Language."""

from __future__ import annotations

_DEFAULT = "fr"


def content_locale_from_accept_language(
    accept_language: str | None,
    *,
    fallback: str = _DEFAULT,
) -> str:
    if not accept_language:
        return fallback
    primary = accept_language.split(",", maxsplit=1)[0].strip()
    if not primary:
        return fallback
    tag = primary.split(";", maxsplit=1)[0].strip()
    if not tag:
        return fallback
    return tag.split("-", maxsplit=1)[0].lower()[:10] or fallback
