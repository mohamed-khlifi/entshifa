"""Unit tests for Accept-Language parsing."""

from __future__ import annotations

from ent.core.i18n.content_locale import content_locale_from_accept_language


def test_primary_tag_is_lowercased() -> None:
    assert content_locale_from_accept_language("en-US,fr;q=0.9") == "en"


def test_missing_header_uses_fallback() -> None:
    assert content_locale_from_accept_language(None, fallback="fr") == "fr"
