"""HTML snapshot rendering and Arabic PDF bytes."""

from __future__ import annotations

from ent.features.documents.catalog import patient_summary_versions
from ent.features.documents.html_render import (
    render_document_html,
    render_from_snapshot,
)
from ent.integrations.pdf import get_pdf_renderer
from ent.integrations.pdf.base import page_css


def _data() -> dict[str, object]:
    return {
        "patient": {
            "fullName": "Leila Ben Salem",
            "fullNameAlt": "ليلى بن سالم",
            "mrn": "DEMO-0001",
            "birthDate": "1975-03-12",
            "ageYears": 51,
            "ageMonths": 618,
            "sex": "female",
            "safetyAlerts": ["only_hearing_ear"],
            "allergies": [],
            "problems": ["Tympanic membrane perforation"],
            "medications": ["Aspirin"],
        },
        "clinic": {
            "name": "Cabinet EntShifa",
            "phone": "+216100000",
            "address": "Tunis",
        },
        "document": {"issuedOn": "2026-09-27"},
    }


def test_arabic_summary_html_is_rtl_and_unmirrored_numbers() -> None:
    version = next(row for row in patient_summary_versions() if row["locale"] == "ar")
    html = render_document_html(
        locale="ar",
        direction="rtl",
        header_html=version["header_html"],
        body_html=version["body_html"],
        footer_html=version["footer_html"],
        css=version["css"],
        data=_data(),
    )
    assert 'dir="rtl"' in html
    assert html.index("الاسم") < html.index("ليلى بن سالم")
    assert "أذن سمع وحيدة" in html
    assert 'class="num"' in html
    assert "DEMO-0001" in html
    assert "لا يوجد تسجيل" in html


def test_english_summary_keeps_ltr() -> None:
    version = next(row for row in patient_summary_versions() if row["locale"] == "en")
    html = render_document_html(
        locale="en",
        direction="ltr",
        header_html="",
        body_html=version["body_html"],
        footer_html=version["footer_html"],
        css=version["css"],
        data=_data(),
    )
    assert 'dir="ltr"' in html
    assert "Only hearing ear" in html
    assert "None recorded" in html


def test_render_uses_the_frozen_snapshot_only() -> None:
    html = render_from_snapshot(
        {
            "data": _data(),
            "template": {
                "locale": "ar",
                "direction": "rtl",
                "header_html": "",
                "body_html": "<p>{{ patient.fullNameAlt }}</p>",
                "footer_html": "",
                "css": "",
            },
        }
    )
    assert "ليلى بن سالم" in html
    assert 'dir="rtl"' in html


def test_page_css_uses_setup_margins() -> None:
    css = page_css(
        {"size": "A4", "orientation": "portrait", "margin_top_mm": 18},
        "rtl",
    )
    assert "18mm" in css
    assert "direction: rtl" in css


def test_arabic_pdf_is_a_real_pdf() -> None:
    version = next(row for row in patient_summary_versions() if row["locale"] == "ar")
    html = render_document_html(
        locale="ar",
        direction="rtl",
        header_html=version["header_html"],
        body_html=version["body_html"],
        footer_html=version["footer_html"],
        css=version["css"],
        data=_data(),
    )
    pdf = get_pdf_renderer().render_pdf(
        html=html,
        css=version["css"],
        page_setup=version["page_setup"],
        direction="rtl",
    )
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000
