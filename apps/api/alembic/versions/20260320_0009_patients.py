"""Patient registry tables (architecture §25.3 / P1-05).

Revision ID: 20260320_0009
Revises: 20260320_0008
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "20260320_0009"
down_revision: str | Sequence[str] | None = "20260320_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
_CS = "utf8mb4_0900_as_cs"
_LATERALITY = "'right','left','bilateral','midline','na'"
_FLAGS = (
    "'only_hearing_ear','anticoagulant','ototoxic_therapy','difficult_airway',"
    "'tracheostomy','laryngeal_stenosis','cochlear_implant','pacemaker',"
    "'immunosuppressed','diabetes','pregnancy','breastfeeding',"
    "'pediatric_weight_missing'"
)


def _clinical_columns() -> list[sa.Column[object]]:
    return [
        sa.Column(
            "id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False
        ),
        sa.Column("public_id", _ULID, nullable=False),
        sa.Column("clinic_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
        ),
        sa.Column(
            "updated_at",
            mysql.DATETIME(fsp=6),
            nullable=False,
            server_default=sa.text(
                "CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"
            ),
        ),
        sa.Column("created_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("updated_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("deleted_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("deleted_by_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column(
            "version",
            mysql.INTEGER(unsigned=True),
            nullable=False,
            server_default="1",
        ),
    ]


def _table_keys(
    name: str,
) -> tuple[sa.PrimaryKeyConstraint, sa.UniqueConstraint, sa.ForeignKeyConstraint]:
    return (
        sa.PrimaryKeyConstraint("id", name=f"pk_{name}"),
        sa.UniqueConstraint("public_id", name=f"uq_{name}__public_id"),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name=f"fk_{name}__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
    )


def _patient_fk(name: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        ["patient_id"],
        ["patient.id"],
        name=f"fk_{name}__patient",
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )


def upgrade() -> None:
    pk, public, clinic = _table_keys("patient")
    op.create_table(
        "patient",
        *_clinical_columns(),
        sa.Column("mrn", sa.String(32, collation=_CS), nullable=False),
        sa.Column("first_name", sa.String(80), nullable=False),
        sa.Column("last_name", sa.String(80), nullable=False),
        sa.Column("first_name_alt", sa.String(80), nullable=True),
        sa.Column("last_name_alt", sa.String(80), nullable=True),
        sa.Column("name_normalized", sa.String(190), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column(
            "birth_date_is_estimated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("sex", sa.String(10), nullable=False),
        sa.Column("preferred_locale", sa.String(10), nullable=False),
        sa.Column("phone_primary", sa.String(32), nullable=True),
        sa.Column("phone_secondary", sa.String(32), nullable=True),
        sa.Column("email", sa.String(190), nullable=True),
        sa.Column("address_line1", sa.String(160), nullable=True),
        sa.Column("address_line2", sa.String(160), nullable=True),
        sa.Column("city", sa.String(80), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("country_code", sa.String(2), nullable=True),
        sa.Column("occupation", sa.String(120), nullable=True),
        sa.Column("noise_exposure", sa.String(40), nullable=True),
        sa.Column("smoking_status", sa.String(30), nullable=True),
        sa.Column("alcohol_status", sa.String(30), nullable=True),
        sa.Column("insurance_scheme_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("insurance_number", sa.String(60), nullable=True),
        sa.Column("referring_doctor_name", sa.String(160), nullable=True),
        sa.Column("referring_doctor_phone", sa.String(32), nullable=True),
        sa.Column("referring_doctor_email", sa.String(190), nullable=True),
        sa.Column("referring_doctor_locale", sa.String(10), nullable=True),
        sa.Column("guardian_name", sa.String(160), nullable=True),
        sa.Column("guardian_relation", sa.String(40), nullable=True),
        sa.Column("emergency_contact_name", sa.String(160), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(32), nullable=True),
        sa.Column(
            "consent_sms", sa.Boolean(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "consent_email", sa.Boolean(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "consent_teaching",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "is_deceased", sa.Boolean(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("deceased_date", sa.Date(), nullable=True),
        sa.CheckConstraint(
            "sex IN ('male','female','other','unknown')", name="ck_patient__sex"
        ),
        sa.UniqueConstraint("clinic_id", "mrn", name="uq_patient__clinic_id__mrn"),
        pk,
        public,
        clinic,
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_patient__clinic_id__name_normalized",
        "patient",
        ["clinic_id", "name_normalized"],
    )
    op.create_index(
        "ix_patient__clinic_id__phone_primary",
        "patient",
        ["clinic_id", "phone_primary"],
    )
    op.create_index(
        "ix_patient__clinic_id__birth_date", "patient", ["clinic_id", "birth_date"]
    )
    op.create_index(
        "ft_patient__names",
        "patient",
        ["first_name", "last_name", "first_name_alt", "last_name_alt"],
        mysql_prefix="FULLTEXT",
    )
    op.create_foreign_key(
        "fk_attachment__patient",
        "attachment",
        "patient",
        ["patient_id"],
        ["id"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )

    _child(
        "patient_identifier",
        sa.Column("type", sa.String(40), nullable=False),
        sa.Column("value", sa.String(80), nullable=False),
        sa.Column("issuing_country", sa.String(2), nullable=True),
        checks=[
            sa.CheckConstraint(
                "type IN ('national_id','passport','insurance')",
                name="ck_patient_identifier__type",
            )
        ],
    )
    op.create_index(
        "ix_patient_identifier__clinic_id__patient_id",
        "patient_identifier",
        ["clinic_id", "patient_id"],
    )
    op.create_index(
        "ix_patient_identifier__clinic_id__type__value",
        "patient_identifier",
        ["clinic_id", "type", "value"],
    )

    _child(
        "patient_allergy",
        sa.Column("substance_concept_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("reaction_concept_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("onset_date", sa.Date(), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")
        ),
        sa.Column("note", sa.Text(), nullable=True),
        checks=[
            sa.CheckConstraint(
                "category IN ('drug','food','other')",
                name="ck_patient_allergy__category",
            ),
            sa.CheckConstraint(
                "severity IS NULL OR severity IN ('mild','moderate','severe')",
                name="ck_patient_allergy__severity",
            ),
        ],
        extra_fks=[
            sa.ForeignKeyConstraint(
                ["substance_concept_id"],
                ["concept.id"],
                name="fk_patient_allergy__substance_concept",
                ondelete="RESTRICT",
                onupdate="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["reaction_concept_id"],
                ["concept.id"],
                name="fk_patient_allergy__reaction_concept",
                ondelete="RESTRICT",
                onupdate="RESTRICT",
            ),
        ],
    )
    op.create_index(
        "ix_patient_allergy__clinic_id__patient_id__is_active",
        "patient_allergy",
        ["clinic_id", "patient_id", "is_active"],
    )

    _child(
        "patient_medication",
        sa.Column("drug_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("free_text_name", sa.String(160), nullable=True),
        sa.Column("dose", sa.String(60), nullable=True),
        sa.Column("frequency", sa.String(60), nullable=True),
        sa.Column("route", sa.String(30), nullable=True),
        sa.Column("started_on", sa.Date(), nullable=True),
        sa.Column("stopped_on", sa.Date(), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")
        ),
        sa.Column(
            "is_anticoagulant",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "is_ototoxic", sa.Boolean(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("source", sa.String(30), nullable=False),
        checks=[
            sa.CheckConstraint(
                "source IN ('prescribed_here','reported','external')",
                name="ck_patient_medication__source",
            )
        ],
    )
    op.create_index(
        "ix_patient_medication__clinic_id__patient_id__is_active",
        "patient_medication",
        ["clinic_id", "patient_id", "is_active"],
    )

    _child(
        "patient_flag",
        sa.Column("flag_code", sa.String(60), nullable=False),
        sa.Column("laterality", sa.String(10), nullable=True),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("detail", mysql.JSON(), nullable=True),
        sa.Column("started_on", sa.Date(), nullable=False),
        sa.Column("ended_on", sa.Date(), nullable=True),
        sa.Column("is_auto", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        checks=[
            sa.CheckConstraint(
                f"flag_code IN ({_FLAGS})", name="ck_patient_flag__flag_code"
            ),
            sa.CheckConstraint(
                f"laterality IS NULL OR laterality IN ({_LATERALITY})",
                name="ck_patient_flag__laterality",
            ),
        ],
    )
    op.create_index(
        "ix_patient_flag__clinic_id__patient_id__ended_on",
        "patient_flag",
        ["clinic_id", "patient_id", "ended_on"],
    )
    op.create_index(
        "ix_patient_flag__clinic_id__flag_code__ended_on",
        "patient_flag",
        ["clinic_id", "flag_code", "ended_on"],
    )

    _child(
        "patient_problem",
        sa.Column("diagnosis_concept_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("laterality", sa.String(10), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("onset_date", sa.Date(), nullable=True),
        sa.Column("resolved_date", sa.Date(), nullable=True),
        sa.Column("first_encounter_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("last_encounter_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        checks=[
            sa.CheckConstraint(
                f"laterality IN ({_LATERALITY})",
                name="ck_patient_problem__laterality",
            ),
            sa.CheckConstraint(
                "status IN ('active','resolved','suspected','ruled_out')",
                name="ck_patient_problem__status",
            ),
        ],
        extra_fks=[
            sa.ForeignKeyConstraint(
                ["diagnosis_concept_id"],
                ["concept.id"],
                name="fk_patient_problem__diagnosis_concept",
                ondelete="RESTRICT",
                onupdate="RESTRICT",
            )
        ],
    )
    op.create_index(
        "ix_patient_problem__clinic_id__patient_id__status",
        "patient_problem",
        ["clinic_id", "patient_id", "status"],
    )

    _child(
        "patient_history",
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("concept_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("free_text", sa.String(400), nullable=True),
        sa.Column("laterality", sa.String(10), nullable=True),
        sa.Column("occurred_year", sa.SmallInteger(), nullable=True),
        sa.Column("occurred_date", sa.Date(), nullable=True),
        sa.Column("detail", mysql.JSON(), nullable=True),
        checks=[
            sa.CheckConstraint(
                "category IN ('ent_surgery','other_surgery','medical','family',"
                "'social','obstetric')",
                name="ck_patient_history__category",
            ),
            sa.CheckConstraint(
                f"laterality IS NULL OR laterality IN ({_LATERALITY})",
                name="ck_patient_history__laterality",
            ),
        ],
        extra_fks=[
            sa.ForeignKeyConstraint(
                ["concept_id"],
                ["concept.id"],
                name="fk_patient_history__concept",
                ondelete="RESTRICT",
                onupdate="RESTRICT",
            )
        ],
    )
    op.create_index(
        "ix_patient_history__clinic_id__patient_id__category",
        "patient_history",
        ["clinic_id", "patient_id", "category"],
    )

    pk, public, clinic = _table_keys("patient_merge_log")
    op.create_table(
        "patient_merge_log",
        *_clinical_columns(),
        sa.Column("surviving_patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("merged_patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("merged_by_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("payload", mysql.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["surviving_patient_id"],
            ["patient.id"],
            name="fk_patient_merge_log__surviving_patient",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["merged_patient_id"],
            ["patient.id"],
            name="fk_patient_merge_log__merged_patient",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["merged_by_id"],
            ["user.id"],
            name="fk_patient_merge_log__user",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        pk,
        public,
        clinic,
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_patient_merge_log__clinic_id__created_at",
        "patient_merge_log",
        ["clinic_id", "created_at"],
    )

    op.create_table(
        "patient_request_idempotency",
        sa.Column(
            "id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False
        ),
        sa.Column("public_id", _ULID, nullable=False),
        sa.Column("clinic_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("idempotency_key", sa.String(80, collation=_CS), nullable=False),
        sa.Column("request_hash", sa.String(64, collation=_CS), nullable=False),
        sa.Column("resource_type", sa.String(40), nullable=False),
        sa.Column("resource_public_id", _ULID, nullable=False),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
        ),
        sa.Column(
            "updated_at",
            mysql.DATETIME(fsp=6),
            nullable=False,
            server_default=sa.text(
                "CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"
            ),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_patient_request_idempotency"),
        sa.UniqueConstraint(
            "public_id", name="uq_patient_request_idempotency__public_id"
        ),
        sa.UniqueConstraint(
            "clinic_id",
            "idempotency_key",
            name="uq_patient_request_idempotency__clinic_id__idempotency_key",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_patient_request_idempotency__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )


def _child(
    name: str,
    *columns: sa.Column[object],
    checks: list[sa.CheckConstraint],
    extra_fks: list[sa.ForeignKeyConstraint] | None = None,
) -> None:
    pk, public, clinic = _table_keys(name)
    op.create_table(
        name,
        *_clinical_columns(),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        *columns,
        *checks,
        *(extra_fks or []),
        _patient_fk(name),
        pk,
        public,
        clinic,
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )


def downgrade() -> None:
    op.drop_table("patient_request_idempotency")
    op.drop_index(
        "ix_patient_merge_log__clinic_id__created_at", table_name="patient_merge_log"
    )
    op.drop_table("patient_merge_log")
    op.drop_index(
        "ix_patient_history__clinic_id__patient_id__category",
        table_name="patient_history",
    )
    op.drop_table("patient_history")
    op.drop_index(
        "ix_patient_problem__clinic_id__patient_id__status",
        table_name="patient_problem",
    )
    op.drop_table("patient_problem")
    op.drop_index(
        "ix_patient_flag__clinic_id__flag_code__ended_on", table_name="patient_flag"
    )
    op.drop_index(
        "ix_patient_flag__clinic_id__patient_id__ended_on", table_name="patient_flag"
    )
    op.drop_table("patient_flag")
    op.drop_index(
        "ix_patient_medication__clinic_id__patient_id__is_active",
        table_name="patient_medication",
    )
    op.drop_table("patient_medication")
    op.drop_index(
        "ix_patient_allergy__clinic_id__patient_id__is_active",
        table_name="patient_allergy",
    )
    op.drop_table("patient_allergy")
    op.drop_index(
        "ix_patient_identifier__clinic_id__type__value",
        table_name="patient_identifier",
    )
    op.drop_index(
        "ix_patient_identifier__clinic_id__patient_id",
        table_name="patient_identifier",
    )
    op.drop_table("patient_identifier")
    op.drop_constraint("fk_attachment__patient", "attachment", type_="foreignkey")
    op.drop_index("ft_patient__names", table_name="patient")
    op.drop_index("ix_patient__clinic_id__birth_date", table_name="patient")
    op.drop_index("ix_patient__clinic_id__phone_primary", table_name="patient")
    op.drop_index("ix_patient__clinic_id__name_normalized", table_name="patient")
    op.drop_table("patient")
