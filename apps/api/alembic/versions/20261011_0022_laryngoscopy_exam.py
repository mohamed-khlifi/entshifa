"""Create laryngoscopy_exam (P3-04).

Revision ID: 20261011_0022
Revises: 20261011_0021
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "20261011_0022"
down_revision: str | Sequence[str] | None = "20261011_0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")


def _in(column: str, values: str, *, nullable: bool) -> str:
    clause = f"{column} IN ({values})"
    if nullable:
        return f"{column} IS NULL OR {clause}"
    return clause


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


def upgrade() -> None:
    mobility = "'normal','hypomobile','immobile','paradoxical'"
    position = "'median','paramedian','intermediate','lateral'"
    glottic = (
        "'complete','anterior_gap','posterior_gap','spindle',"
        "'hourglass','irregular','incomplete'"
    )
    supraglottic = "'none','anteroposterior','mediolateral','sphincteric'"
    symmetry = "'symmetric','asymmetric'"
    periodicity = "'regular','irregular'"
    amplitude = "'normal','reduced','absent'"
    wave = "'normal','reduced','absent'"
    phase_close = "'normal','predominantly_open','predominantly_closed','always_open'"
    vertical = "'on_plane','off_plane_right_lower','off_plane_left_lower'"
    non_vib = "'none','right','left','bilateral'"
    scope = "'flexible_fiberoptic','flexible_distal_chip','rigid_70','rigid_90'"
    op.create_table(
        "laryngoscopy_exam",
        *_clinical_columns(),
        sa.Column("procedure_record_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("scope_type", sa.String(30), nullable=False),
        sa.Column("vf_mobility_right", sa.String(20), nullable=False),
        sa.Column("vf_mobility_left", sa.String(20), nullable=False),
        sa.Column("vf_position_right", sa.String(20), nullable=True),
        sa.Column("vf_position_left", sa.String(20), nullable=True),
        sa.Column("glottic_closure", sa.String(20), nullable=False),
        sa.Column("supraglottic_pattern", sa.String(20), nullable=True),
        sa.Column(
            "stroboscopy_performed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("symmetry", sa.String(20), nullable=True),
        sa.Column("periodicity", sa.String(20), nullable=True),
        sa.Column("amplitude_right", sa.String(20), nullable=True),
        sa.Column("amplitude_left", sa.String(20), nullable=True),
        sa.Column("mucosal_wave_right", sa.String(20), nullable=True),
        sa.Column("mucosal_wave_left", sa.String(20), nullable=True),
        sa.Column("phase_closure", sa.String(30), nullable=True),
        sa.Column("phase_symmetry", sa.String(20), nullable=True),
        sa.Column("vertical_level", sa.String(30), nullable=True),
        sa.Column("non_vibrating_segment", sa.String(20), nullable=True),
        sa.Column(
            "fees_performed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("rfs_score", sa.SmallInteger(), nullable=True),
        sa.Column("grbas_g", sa.SmallInteger(), nullable=True),
        sa.Column("grbas_r", sa.SmallInteger(), nullable=True),
        sa.Column("grbas_b", sa.SmallInteger(), nullable=True),
        sa.Column("grbas_a", sa.SmallInteger(), nullable=True),
        sa.Column("grbas_s", sa.SmallInteger(), nullable=True),
        sa.Column("pas_score", sa.SmallInteger(), nullable=True),
        sa.Column("conclusion_text", mysql.MEDIUMTEXT(), nullable=True),
        sa.CheckConstraint(
            _in("scope_type", scope, nullable=False),
            name="ck_laryngoscopy_exam__scope_type",
        ),
        sa.CheckConstraint(
            _in("vf_mobility_right", mobility, nullable=False),
            name="ck_laryngoscopy_exam__vf_mob_r",
        ),
        sa.CheckConstraint(
            _in("vf_mobility_left", mobility, nullable=False),
            name="ck_laryngoscopy_exam__vf_mob_l",
        ),
        sa.CheckConstraint(
            _in("vf_position_right", position, nullable=True),
            name="ck_laryngoscopy_exam__vf_pos_r",
        ),
        sa.CheckConstraint(
            _in("vf_position_left", position, nullable=True),
            name="ck_laryngoscopy_exam__vf_pos_l",
        ),
        sa.CheckConstraint(
            _in("glottic_closure", glottic, nullable=False),
            name="ck_laryngoscopy_exam__glottic",
        ),
        sa.CheckConstraint(
            _in("supraglottic_pattern", supraglottic, nullable=True),
            name="ck_laryngoscopy_exam__supraglottic",
        ),
        sa.CheckConstraint(
            _in("symmetry", symmetry, nullable=True),
            name="ck_laryngoscopy_exam__symmetry",
        ),
        sa.CheckConstraint(
            _in("periodicity", periodicity, nullable=True),
            name="ck_laryngoscopy_exam__periodicity",
        ),
        sa.CheckConstraint(
            _in("amplitude_right", amplitude, nullable=True),
            name="ck_laryngoscopy_exam__amp_r",
        ),
        sa.CheckConstraint(
            _in("amplitude_left", amplitude, nullable=True),
            name="ck_laryngoscopy_exam__amp_l",
        ),
        sa.CheckConstraint(
            _in("mucosal_wave_right", wave, nullable=True),
            name="ck_laryngoscopy_exam__wave_r",
        ),
        sa.CheckConstraint(
            _in("mucosal_wave_left", wave, nullable=True),
            name="ck_laryngoscopy_exam__wave_l",
        ),
        sa.CheckConstraint(
            _in("phase_closure", phase_close, nullable=True),
            name="ck_laryngoscopy_exam__phase_close",
        ),
        sa.CheckConstraint(
            _in("phase_symmetry", symmetry, nullable=True),
            name="ck_laryngoscopy_exam__phase_sym",
        ),
        sa.CheckConstraint(
            _in("vertical_level", vertical, nullable=True),
            name="ck_laryngoscopy_exam__vertical",
        ),
        sa.CheckConstraint(
            _in("non_vibrating_segment", non_vib, nullable=True),
            name="ck_laryngoscopy_exam__non_vib",
        ),
        sa.CheckConstraint(
            "rfs_score IS NULL OR rfs_score BETWEEN 0 AND 26",
            name="ck_laryngoscopy_exam__rfs",
        ),
        sa.CheckConstraint(
            "grbas_g IS NULL OR grbas_g BETWEEN 0 AND 3",
            name="ck_laryngoscopy_exam__grbas_g",
        ),
        sa.CheckConstraint(
            "grbas_r IS NULL OR grbas_r BETWEEN 0 AND 3",
            name="ck_laryngoscopy_exam__grbas_r",
        ),
        sa.CheckConstraint(
            "grbas_b IS NULL OR grbas_b BETWEEN 0 AND 3",
            name="ck_laryngoscopy_exam__grbas_b",
        ),
        sa.CheckConstraint(
            "grbas_a IS NULL OR grbas_a BETWEEN 0 AND 3",
            name="ck_laryngoscopy_exam__grbas_a",
        ),
        sa.CheckConstraint(
            "grbas_s IS NULL OR grbas_s BETWEEN 0 AND 3",
            name="ck_laryngoscopy_exam__grbas_s",
        ),
        sa.CheckConstraint(
            "pas_score IS NULL OR pas_score BETWEEN 1 AND 8",
            name="ck_laryngoscopy_exam__pas",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinic.id"],
            name="fk_laryngoscopy_exam__clinic",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["procedure_record_id"],
            ["procedure_record.id"],
            name="fk_laryngoscopy_exam__procedure",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_laryngoscopy_exam__public_id"),
        sa.UniqueConstraint(
            "procedure_record_id",
            name="uq_laryngoscopy_exam__procedure",
        ),
        sa.Index(
            "ix_laryngoscopy_exam__clinic_procedure",
            "clinic_id",
            "procedure_record_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("laryngoscopy_exam")
