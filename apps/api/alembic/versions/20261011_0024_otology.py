"""Otology exam, office procedure, ear device, follow-up setting (P3-06).

Revision ID: 20261011_0024
Revises: 20261011_0023
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "20261011_0024"
down_revision: str | Sequence[str] | None = "20261011_0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")
_FLAGS_NEXT = (
    "'only_hearing_ear','anticoagulant','ototoxic_therapy','difficult_airway',"
    "'tracheostomy','laryngeal_stenosis','cochlear_implant','pacemaker',"
    "'immunosuppressed','diabetes','pregnancy','breastfeeding',"
    "'pediatric_weight_missing','ventilation_tube','mastoid_cavity','cholesteatoma'"
)
_FLAGS_PREVIOUS = (
    "'only_hearing_ear','anticoagulant','ototoxic_therapy','difficult_airway',"
    "'tracheostomy','laryngeal_stenosis','cochlear_implant','pacemaker',"
    "'immunosuppressed','diabetes','pregnancy','breastfeeding',"
    "'pediatric_weight_missing'"
)
_FOLLOW_UP = {
    "tube_first_check_days": 21,
    "tube_first_window_days": 7,
    "tube_interval_window_days": 30,
    "wick_removal_days": 3,
    "wick_window_days": 1,
    "cavity_cleaning_months": 6,
    "cavity_window_days": 30,
    "canal_injury_window_days": 7,
}


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


def _in(column: str, values: str, *, nullable: bool) -> str:
    clause = f"{column} IN ({values})"
    if nullable:
        return f"{column} IS NULL OR {clause}"
    return clause


def upgrade() -> None:
    op.drop_constraint("ck_patient_flag__flag_code", "patient_flag", type_="check")
    op.create_check_constraint(
        "ck_patient_flag__flag_code",
        "patient_flag",
        f"flag_code IN ({_FLAGS_NEXT})",
    )
    op.drop_constraint("ck_recall__source_type", "recall", type_="check")
    op.create_check_constraint(
        "ck_recall__source_type",
        "recall",
        "source_type IN ('manual','procedure')",
    )
    _create_otology()
    _create_office()
    _create_device()
    _insert_setting()


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM setting WHERE public_id = '01JP1A00000000000000000006'")
    )
    op.drop_table("ear_device")
    op.drop_table("office_procedure")
    op.drop_table("otology_exam")
    op.drop_constraint("ck_recall__source_type", "recall", type_="check")
    op.create_check_constraint(
        "ck_recall__source_type",
        "recall",
        "source_type IN ('manual')",
    )
    op.execute(
        sa.text(
            "UPDATE patient_flag SET deleted_at = CURRENT_TIMESTAMP(6) "
            "WHERE flag_code IN ('ventilation_tube','mastoid_cavity','cholesteatoma') "
            "AND deleted_at IS NULL"
        )
    )
    op.drop_constraint("ck_patient_flag__flag_code", "patient_flag", type_="check")
    op.create_check_constraint(
        "ck_patient_flag__flag_code",
        "patient_flag",
        f"flag_code IN ({_FLAGS_PREVIOUS})",
    )


def _create_otology() -> None:
    method = "'otoscopy','microscopy'"
    weber = "'midline','lateralizes_right','lateralizes_left'"
    rinne = "'positive','negative'"
    mobility = "'normal','reduced','absent','hypermobile'"
    op.create_table(
        "otology_exam",
        *_clinical_columns(),
        sa.Column("procedure_record_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("method", sa.String(30), nullable=False),
        sa.Column("weber", sa.String(20), nullable=True),
        sa.Column("rinne_right", sa.String(10), nullable=True),
        sa.Column("rinne_left", sa.String(10), nullable=True),
        sa.Column("fork_frequency_hz", sa.SmallInteger(), nullable=True),
        sa.Column("mobility_right", sa.String(20), nullable=True),
        sa.Column("mobility_left", sa.String(20), nullable=True),
        sa.Column("conclusion_text", mysql.MEDIUMTEXT(), nullable=True),
        sa.CheckConstraint(
            _in("method", method, nullable=False), name="ck_otology_exam__method"
        ),
        sa.CheckConstraint(
            _in("weber", weber, nullable=True), name="ck_otology_exam__weber"
        ),
        sa.CheckConstraint(
            _in("rinne_right", rinne, nullable=True), name="ck_otology_exam__rinne_r"
        ),
        sa.CheckConstraint(
            _in("rinne_left", rinne, nullable=True), name="ck_otology_exam__rinne_l"
        ),
        sa.CheckConstraint(
            "fork_frequency_hz IS NULL OR fork_frequency_hz IN (256, 512)",
            name="ck_otology_exam__fork",
        ),
        sa.CheckConstraint(
            _in("mobility_right", mobility, nullable=True),
            name="ck_otology_exam__mob_r",
        ),
        sa.CheckConstraint(
            _in("mobility_left", mobility, nullable=True),
            name="ck_otology_exam__mob_l",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_otology_exam__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["procedure_record_id"],
            ["procedure_record.id"],
            name="fk_otology_exam__procedure",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_otology_exam"),
        sa.UniqueConstraint("public_id", name="uq_otology_exam__public_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "uq_otology_exam__procedure",
        "otology_exam",
        ["procedure_record_id"],
        unique=True,
    )
    op.create_index(
        "ix_otology_exam__clinic_procedure",
        "otology_exam",
        ["clinic_id", "procedure_record_id"],
    )


def _create_office() -> None:
    subtypes = (
        "'wax_removal','foreign_body','wick','tube_insertion','tube_removal',"
        "'intratympanic_injection','cavity_cleaning'"
    )
    op.create_table(
        "office_procedure",
        *_clinical_columns(),
        sa.Column("procedure_record_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("subtype", sa.String(40), nullable=False),
        sa.Column("payload", mysql.JSON(), nullable=False),
        sa.Column("removal_due_date", sa.Date(), nullable=True),
        sa.Column(
            "live_procedure_id",
            mysql.BIGINT(unsigned=True),
            sa.Computed(
                "CASE WHEN deleted_at IS NULL THEN procedure_record_id ELSE NULL END",
                persisted=True,
            ),
            nullable=True,
        ),
        sa.CheckConstraint(
            _in("subtype", subtypes, nullable=False),
            name="ck_office_procedure__subtype",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_office_procedure__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["procedure_record_id"],
            ["procedure_record.id"],
            name="fk_office_procedure__procedure",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_office_procedure"),
        sa.UniqueConstraint("public_id", name="uq_office_procedure__public_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "uq_office_procedure__live",
        "office_procedure",
        ["live_procedure_id"],
        unique=True,
    )
    op.create_index(
        "ix_office_procedure__clinic_procedure",
        "office_procedure",
        ["clinic_id", "procedure_record_id"],
    )


def _create_device() -> None:
    op.create_table(
        "ear_device",
        *_clinical_columns(),
        sa.Column("patient_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("laterality", sa.String(10), nullable=False),
        sa.Column("device_type", sa.String(40), nullable=False),
        sa.Column("inserted_at", sa.Date(), nullable=False),
        sa.Column("inserted_procedure_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("tube_model", sa.String(80), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("removed_at", sa.Date(), nullable=True),
        sa.Column("complication", sa.String(80), nullable=True),
        sa.Column("next_check_due", sa.Date(), nullable=False),
        sa.CheckConstraint(
            "laterality IN ('right','left','bilateral')",
            name="ck_ear_device__laterality",
        ),
        sa.CheckConstraint(
            "device_type IN ('ventilation_tube','mastoid_cavity')",
            name="ck_ear_device__device_type",
        ),
        sa.CheckConstraint(
            "status IN ('in_place','blocked','extruded','removed','retained')",
            name="ck_ear_device__status",
        ),
        sa.CheckConstraint(
            "tube_model IS NULL OR tube_model IN "
            "('shepard','armstrong','t_tube','bobbin','paparella')",
            name="ck_ear_device__tube_model",
        ),
        sa.CheckConstraint(
            "complication IS NULL OR complication IN "
            "('bleeding','otorrhea','vertigo','perforation')",
            name="ck_ear_device__complication",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_ear_device__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient.id"],
            name="fk_ear_device__patient",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["inserted_procedure_id"],
            ["procedure_record.id"],
            name="fk_ear_device__inserted_procedure",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ear_device"),
        sa.UniqueConstraint("public_id", name="uq_ear_device__public_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_ear_device__clinic_id__status__next_check_due",
        "ear_device",
        ["clinic_id", "status", "next_check_due"],
    )
    op.create_index(
        "ix_ear_device__clinic_id__patient_id",
        "ear_device",
        ["clinic_id", "patient_id"],
    )
    op.create_index(
        "ix_ear_device__clinic_inserted_procedure",
        "ear_device",
        ["clinic_id", "inserted_procedure_id"],
    )


def _insert_setting() -> None:
    now = datetime.now(UTC).replace(tzinfo=None)
    op.get_bind().execute(
        sa.text(
            "INSERT INTO setting "
            "(public_id, clinic_id, user_id, `key`, value, created_at, updated_at, version) "
            "VALUES (:public_id, NULL, NULL, :key, CAST(:value AS JSON), "
            ":created_at, :updated_at, 1)"
        ),
        {
            "public_id": "01JP1A00000000000000000006",
            "key": "otology_follow_up",
            "value": json.dumps(_FOLLOW_UP),
            "created_at": now,
            "updated_at": now,
        },
    )
