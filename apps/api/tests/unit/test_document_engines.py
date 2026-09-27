"""Known-answer tests for document template checks."""

from __future__ import annotations

from datetime import date

import pytest
from jinja2 import nodes

from ent.engines.documents.age import completed_age
from ent.engines.documents.content_hash import content_hash
from ent.engines.documents.placeholders import (
    _target_names,
    lookup_path,
    missing_required,
    referenced_paths,
    validate_placeholders,
)


def test_declared_paths_are_accepted() -> None:
    issue = validate_placeholders(
        ("<p>{{ patient.fullName }}</p>",),
        {"patient.fullName"},
    )
    assert issue is None


def test_undeclared_path_is_rejected() -> None:
    issue = validate_placeholders(("{{ patient.secret }}",), {"patient.fullName"})
    assert issue is not None
    assert issue.reason == "undeclared"
    assert issue.name == "patient.secret"


def test_syntax_error_reports_a_line() -> None:
    issue = validate_placeholders(("{{",), set())
    assert issue is not None
    assert issue.reason == "syntax"
    assert issue.line is not None


def test_dynamic_lookup_is_unsupported() -> None:
    issue = validate_placeholders(("{{ patient[name] }}",), {"patient"})
    assert issue is not None
    assert issue.reason == "unsupported"


def test_string_item_counts_as_a_path() -> None:
    found = referenced_paths("{{ patient['fullName'] }}")
    assert found == {"patient.fullName"}


def test_integer_item_is_unsupported() -> None:
    assert referenced_paths("{{ patient[0] }}") is None


def test_loop_names_are_not_placeholders() -> None:
    source = "{% for item in patient.allergies %}{{ item }}{% endfor %}"
    assert referenced_paths(source) == {"patient.allergies"}


def test_tuple_loop_targets_are_not_placeholders() -> None:
    source = "{% for left, right in patient.rows %}{{ left }}{{ right }}{% endfor %}"
    assert referenced_paths(source) == {"patient.rows"}


def test_nested_attribute_is_one_path() -> None:
    assert referenced_paths("{{ patient.address.city }}") == {"patient.address.city"}


def test_bare_name_is_a_placeholder() -> None:
    assert referenced_paths("{{ note }}") == {"note"}


def test_store_name_is_ignored() -> None:
    source = "{% set label = patient.fullName %}{{ patient.fullName }}"
    assert referenced_paths(source) == {"patient.fullName"}


def test_unknown_loop_target_adds_no_name() -> None:
    assert _target_names(nodes.Const("x")) == set()


def test_lookup_and_required_paths() -> None:
    data = {"patient": {"fullName": "A", "allergies": []}}
    assert lookup_path(data, "patient.fullName") == "A"
    assert lookup_path(data, "patient.missing") is None
    assert lookup_path(data, "other.name") is None
    assert lookup_path({"patient": "A"}, "patient.fullName") is None
    missing = missing_required(
        {
            "patient.fullName": {"required": True},
            "patient.note": {"required": False},
            "patient.allergies": {"required": True},
            "clinic.name": {"required": True},
        },
        data,
    )
    assert missing == ["clinic.name"]


def test_content_hash_is_stable() -> None:
    left = content_hash({"b": 1, "a": "ملخص"})
    right = content_hash({"a": "ملخص", "b": 1})
    assert left == right
    assert left != content_hash({"a": "ملخص", "b": 2})
    assert len(left) == 64


def test_completed_age_anniversary() -> None:
    assert completed_age(date(2000, 3, 12), date(2026, 3, 12)) == (26, 312)
    assert completed_age(date(2000, 3, 12), date(2026, 3, 11)) == (25, 311)
    assert completed_age(date(2000, 3, 12), date(2000, 3, 12)) == (0, 0)


def test_completed_age_rejects_an_earlier_date() -> None:
    with pytest.raises(ValueError, match="documents.age_before_birth"):
        completed_age(date(2020, 1, 2), date(2020, 1, 1))
