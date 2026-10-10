"""Create the prescription and formulary tables (P2-08).

Revision ID: 20261010_0017
Revises: 20261004_0016
Create Date: 2026-10-10 00:00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "20261010_0017"
down_revision: str | Sequence[str] | None = "20261004_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ULID = sa.CHAR(26, collation="utf8mb4_0900_as_cs")


def upgrade() -> None:
    op.create_table('prescription_request_idempotency',
    sa.Column('public_id', _ULID, nullable=False),
    sa.Column('clinic_id', mysql.BIGINT(unsigned=True), nullable=False),
    sa.Column('idempotency_key', sa.String(length=80, collation='utf8mb4_0900_as_cs'), nullable=False),
    sa.Column('request_hash', sa.String(length=64, collation='utf8mb4_0900_as_cs'), nullable=False),
    sa.Column('resource_type', sa.String(length=40), nullable=False),
    sa.Column('resource_public_id', _ULID, nullable=False),
    sa.Column('id', mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
    sa.Column('created_at', mysql.DATETIME(fsp=6), server_default=sa.text('CURRENT_TIMESTAMP(6)'), nullable=False),
    sa.Column('updated_at', mysql.DATETIME(fsp=6), server_default=sa.text('CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)'), nullable=False),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinic.id'], name=op.f('fk_prescription_request_idempotency__clinic'), onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_prescription_request_idempotency')),
    sa.UniqueConstraint('public_id', name=op.f('uq_prescription_request_idempotency__public_id'))
    )
    op.create_index('uq_rx_idempotency__clinic_id__idempotency_key', 'prescription_request_idempotency', ['clinic_id', 'idempotency_key'], unique=True)
    op.create_table('prescription_template',
    sa.Column('user_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('code', sa.String(length=60, collation='utf8mb4_0900_as_cs'), nullable=False),
    sa.Column('name_key', sa.String(length=80), nullable=False),
    sa.Column('complaint_concept_ids', mysql.JSON(), nullable=True),
    sa.Column('items', mysql.JSON(), nullable=False),
    sa.Column('is_pediatric', sa.Boolean(), server_default=sa.text('0'), nullable=False),
    sa.Column('id', mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
    sa.Column('public_id', _ULID, nullable=False),
    sa.Column('clinic_id', mysql.BIGINT(unsigned=True), nullable=False),
    sa.Column('created_at', mysql.DATETIME(fsp=6), server_default=sa.text('CURRENT_TIMESTAMP(6)'), nullable=False),
    sa.Column('updated_at', mysql.DATETIME(fsp=6), server_default=sa.text('CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)'), nullable=False),
    sa.Column('created_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('updated_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('deleted_at', mysql.DATETIME(fsp=6), nullable=True),
    sa.Column('deleted_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('version', mysql.INTEGER(unsigned=True), server_default='1', nullable=False),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinic.id'], name=op.f('fk_prescription_template__clinic'), onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_prescription_template__user'), onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_prescription_template')),
    sa.UniqueConstraint('clinic_id', 'code', name='uq_prescription_template__clinic_id__code'),
    sa.UniqueConstraint('public_id', name=op.f('uq_prescription_template__public_id'))
    )
    op.create_index(op.f('ix_prescription_template__clinic_id'), 'prescription_template', ['clinic_id'], unique=False)
    op.create_index('ix_prescription_template__clinic_id__user_id', 'prescription_template', ['clinic_id', 'user_id'], unique=False)
    op.create_table('drug',
    sa.Column('code', sa.String(length=60, collation='utf8mb4_0900_as_cs'), nullable=False),
    sa.Column('inn_name', sa.String(length=160), nullable=False),
    sa.Column('atc_code', sa.String(length=20), nullable=True),
    sa.Column('drug_class', sa.String(length=80), nullable=True),
    sa.Column('is_ototoxic', sa.Boolean(), server_default=sa.text('0'), nullable=False),
    sa.Column('is_anticoagulant', sa.Boolean(), server_default=sa.text('0'), nullable=False),
    sa.Column('pregnancy_category', sa.String(length=10), nullable=True),
    sa.Column('concept_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('id', mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
    sa.Column('public_id', _ULID, nullable=False),
    sa.Column('created_at', mysql.DATETIME(fsp=6), server_default=sa.text('CURRENT_TIMESTAMP(6)'), nullable=False),
    sa.Column('updated_at', mysql.DATETIME(fsp=6), server_default=sa.text('CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)'), nullable=False),
    sa.Column('created_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('updated_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('deleted_at', mysql.DATETIME(fsp=6), nullable=True),
    sa.Column('deleted_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('version', mysql.INTEGER(unsigned=True), server_default='1', nullable=False),
    sa.CheckConstraint("pregnancy_category IS NULL OR pregnancy_category IN ('caution','contraindicated','compatible')", name=op.f('ck_drug__ck_drug__pregnancy_category')),
    sa.ForeignKeyConstraint(['concept_id'], ['concept.id'], name=op.f('fk_drug__concept'), onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_drug')),
    sa.UniqueConstraint('code', name='uq_drug__code'),
    sa.UniqueConstraint('public_id', name=op.f('uq_drug__public_id'))
    )
    op.create_index('ix_drug__drug_class', 'drug', ['drug_class'], unique=False)
    op.create_table('drug_form',
    sa.Column('drug_id', mysql.BIGINT(unsigned=True), nullable=False),
    sa.Column('form', sa.String(length=40), nullable=False),
    sa.Column('strength_value', sa.Numeric(precision=10, scale=3), nullable=True),
    sa.Column('strength_unit', sa.String(length=20), nullable=True),
    sa.Column('concentration_mg_per_ml', sa.Numeric(precision=10, scale=3), nullable=True),
    sa.Column('package_description', sa.String(length=120), nullable=True),
    sa.Column('id', mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
    sa.Column('public_id', _ULID, nullable=False),
    sa.Column('created_at', mysql.DATETIME(fsp=6), server_default=sa.text('CURRENT_TIMESTAMP(6)'), nullable=False),
    sa.Column('updated_at', mysql.DATETIME(fsp=6), server_default=sa.text('CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)'), nullable=False),
    sa.Column('created_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('updated_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('deleted_at', mysql.DATETIME(fsp=6), nullable=True),
    sa.Column('deleted_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('version', mysql.INTEGER(unsigned=True), server_default='1', nullable=False),
    sa.CheckConstraint("form IN ('tablet','syrup','spray','drops','injection')", name=op.f('ck_drug_form__ck_drug_form__form')),
    sa.CheckConstraint('concentration_mg_per_ml IS NULL OR concentration_mg_per_ml > 0', name=op.f('ck_drug_form__ck_drug_form__concentration')),
    sa.CheckConstraint('strength_value IS NULL OR strength_value > 0', name=op.f('ck_drug_form__ck_drug_form__strength_value')),
    sa.ForeignKeyConstraint(['drug_id'], ['drug.id'], name=op.f('fk_drug_form__drug'), onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_drug_form')),
    sa.UniqueConstraint('public_id', name=op.f('uq_drug_form__public_id'))
    )
    op.create_index('ix_drug_form__drug_id', 'drug_form', ['drug_id'], unique=False)
    op.create_table('calculation_result',
    sa.Column('patient_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('encounter_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('calculator_code', sa.String(length=60), nullable=False),
    sa.Column('engine_version', sa.String(length=20), nullable=False),
    sa.Column('inputs', mysql.JSON(), nullable=False),
    sa.Column('value', sa.String(length=80), nullable=False),
    sa.Column('unit', sa.String(length=20), nullable=True),
    sa.Column('flags', mysql.JSON(), nullable=False),
    sa.Column('reference', sa.String(length=255), nullable=False),
    sa.Column('computed_at', mysql.DATETIME(fsp=6), nullable=False),
    sa.Column('computed_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('id', mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
    sa.Column('public_id', _ULID, nullable=False),
    sa.Column('clinic_id', mysql.BIGINT(unsigned=True), nullable=False),
    sa.Column('created_at', mysql.DATETIME(fsp=6), server_default=sa.text('CURRENT_TIMESTAMP(6)'), nullable=False),
    sa.Column('updated_at', mysql.DATETIME(fsp=6), server_default=sa.text('CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)'), nullable=False),
    sa.Column('created_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('updated_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('deleted_at', mysql.DATETIME(fsp=6), nullable=True),
    sa.Column('deleted_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('version', mysql.INTEGER(unsigned=True), server_default='1', nullable=False),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinic.id'], name=op.f('fk_calculation_result__clinic'), onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['computed_by_id'], ['user.id'], name=op.f('fk_calculation_result__user'), onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['encounter_id'], ['encounter.id'], name=op.f('fk_calculation_result__encounter'), onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['patient_id'], ['patient.id'], name=op.f('fk_calculation_result__patient'), onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_calculation_result')),
    sa.UniqueConstraint('public_id', name=op.f('uq_calculation_result__public_id'))
    )
    op.create_index(op.f('ix_calculation_result__clinic_id'), 'calculation_result', ['clinic_id'], unique=False)
    op.create_index('ix_calculation_result__clinic_id__calculator_code', 'calculation_result', ['clinic_id', 'calculator_code'], unique=False)
    op.create_index('ix_calculation_result__clinic_id__patient_id__computed_at', 'calculation_result', ['clinic_id', 'patient_id', 'computed_at'], unique=False)
    op.create_table('formulary_entry',
    sa.Column('drug_form_id', mysql.BIGINT(unsigned=True), nullable=False),
    sa.Column('brand_name', sa.String(length=120), nullable=False),
    sa.Column('is_available', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.Column('local_code', sa.String(length=40), nullable=True),
    sa.Column('price', sa.Numeric(precision=12, scale=3), nullable=True),
    sa.Column('currency_code', sa.String(length=3), nullable=True),
    sa.Column('notes', sa.String(length=255), nullable=True),
    sa.Column('dosing_rules', mysql.JSON(), nullable=True),
    sa.Column('id', mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
    sa.Column('public_id', _ULID, nullable=False),
    sa.Column('clinic_id', mysql.BIGINT(unsigned=True), nullable=False),
    sa.Column('created_at', mysql.DATETIME(fsp=6), server_default=sa.text('CURRENT_TIMESTAMP(6)'), nullable=False),
    sa.Column('updated_at', mysql.DATETIME(fsp=6), server_default=sa.text('CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)'), nullable=False),
    sa.Column('created_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('updated_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('deleted_at', mysql.DATETIME(fsp=6), nullable=True),
    sa.Column('deleted_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('version', mysql.INTEGER(unsigned=True), server_default='1', nullable=False),
    sa.CheckConstraint('price IS NULL OR (currency_code IS NOT NULL AND price >= 0)', name=op.f('ck_formulary_entry__ck_formulary_entry__price')),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinic.id'], name=op.f('fk_formulary_entry__clinic'), onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['drug_form_id'], ['drug_form.id'], name=op.f('fk_formulary_entry__drug_form'), onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_formulary_entry')),
    sa.UniqueConstraint('clinic_id', 'drug_form_id', name='uq_formulary_entry__clinic_id__drug_form_id'),
    sa.UniqueConstraint('public_id', name=op.f('uq_formulary_entry__public_id'))
    )
    op.create_index(op.f('ix_formulary_entry__clinic_id'), 'formulary_entry', ['clinic_id'], unique=False)
    op.create_index('ix_formulary_entry__clinic_id__is_available', 'formulary_entry', ['clinic_id', 'is_available'], unique=False)
    op.create_table('prescription',
    sa.Column('patient_id', mysql.BIGINT(unsigned=True), nullable=False),
    sa.Column('encounter_id', mysql.BIGINT(unsigned=True), nullable=False),
    sa.Column('prescriber_id', mysql.BIGINT(unsigned=True), nullable=False),
    sa.Column('issued_at', mysql.DATETIME(fsp=6), nullable=True),
    sa.Column('locale', sa.String(length=10), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('document_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('weight_kg_at_issue', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('is_pediatric', sa.Boolean(), server_default=sa.text('0'), nullable=False),
    sa.Column('safety_alerts', mysql.JSON(), nullable=True),
    sa.Column('id', mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
    sa.Column('public_id', _ULID, nullable=False),
    sa.Column('clinic_id', mysql.BIGINT(unsigned=True), nullable=False),
    sa.Column('created_at', mysql.DATETIME(fsp=6), server_default=sa.text('CURRENT_TIMESTAMP(6)'), nullable=False),
    sa.Column('updated_at', mysql.DATETIME(fsp=6), server_default=sa.text('CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)'), nullable=False),
    sa.Column('created_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('updated_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('deleted_at', mysql.DATETIME(fsp=6), nullable=True),
    sa.Column('deleted_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('version', mysql.INTEGER(unsigned=True), server_default='1', nullable=False),
    sa.CheckConstraint("status IN ('draft','issued','cancelled')", name=op.f('ck_prescription__ck_prescription__status')),
    sa.CheckConstraint('weight_kg_at_issue IS NULL OR weight_kg_at_issue > 0', name=op.f('ck_prescription__ck_prescription__weight')),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinic.id'], name=op.f('fk_prescription__clinic'), onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['document_id'], ['document.id'], name=op.f('fk_prescription__document'), onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['encounter_id'], ['encounter.id'], name=op.f('fk_prescription__encounter'), onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['patient_id'], ['patient.id'], name=op.f('fk_prescription__patient'), onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['prescriber_id'], ['user.id'], name=op.f('fk_prescription__user'), onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_prescription')),
    sa.UniqueConstraint('public_id', name=op.f('uq_prescription__public_id'))
    )
    op.create_index(op.f('ix_prescription__clinic_id'), 'prescription', ['clinic_id'], unique=False)
    op.create_index('ix_prescription__clinic_id__encounter_id', 'prescription', ['clinic_id', 'encounter_id'], unique=False)
    op.create_index('ix_prescription__clinic_id__patient_id__issued_at', 'prescription', ['clinic_id', 'patient_id', 'issued_at'], unique=False)
    op.create_table('prescription_item',
    sa.Column('prescription_id', mysql.BIGINT(unsigned=True), nullable=False),
    sa.Column('drug_form_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('free_text_name', sa.String(length=160), nullable=True),
    sa.Column('dose_amount', sa.Numeric(precision=10, scale=3), nullable=True),
    sa.Column('dose_unit', sa.String(length=20), nullable=True),
    sa.Column('volume_ml', sa.Numeric(precision=8, scale=2), nullable=True),
    sa.Column('route', sa.String(length=30), nullable=False),
    sa.Column('frequency_per_day', sa.SmallInteger(), nullable=False),
    sa.Column('interval_hours', sa.SmallInteger(), nullable=True),
    sa.Column('duration_days', sa.SmallInteger(), nullable=False),
    sa.Column('quantity', sa.String(length=60), nullable=True),
    sa.Column('instructions_text', sa.String(length=400), nullable=True),
    sa.Column('taper_schedule', mysql.JSON(), nullable=True),
    sa.Column('is_renewable', sa.Boolean(), server_default=sa.text('0'), nullable=False),
    sa.Column('substitution_allowed', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.Column('safety_overrides', mysql.JSON(), nullable=True),
    sa.Column('sort_order', sa.SmallInteger(), nullable=False),
    sa.Column('dosing_engine_version', sa.String(length=20), nullable=True),
    sa.Column('id', mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
    sa.Column('public_id', _ULID, nullable=False),
    sa.Column('clinic_id', mysql.BIGINT(unsigned=True), nullable=False),
    sa.Column('created_at', mysql.DATETIME(fsp=6), server_default=sa.text('CURRENT_TIMESTAMP(6)'), nullable=False),
    sa.Column('updated_at', mysql.DATETIME(fsp=6), server_default=sa.text('CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)'), nullable=False),
    sa.Column('created_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('updated_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('deleted_at', mysql.DATETIME(fsp=6), nullable=True),
    sa.Column('deleted_by_id', mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column('version', mysql.INTEGER(unsigned=True), server_default='1', nullable=False),
    sa.CheckConstraint("route IN ('oral','nasal','otic','topical','injection')", name=op.f('ck_prescription_item__ck_prescription_item__route')),
    sa.CheckConstraint('(drug_form_id IS NOT NULL AND free_text_name IS NULL) OR (drug_form_id IS NULL AND free_text_name IS NOT NULL)', name=op.f('ck_prescription_item__ck_prescription_item__identity')),
    sa.CheckConstraint('dose_amount IS NULL OR dose_amount > 0', name=op.f('ck_prescription_item__ck_prescription_item__dose_amount')),
    sa.CheckConstraint('duration_days >= 1', name=op.f('ck_prescription_item__ck_prescription_item__duration')),
    sa.CheckConstraint('frequency_per_day >= 1', name=op.f('ck_prescription_item__ck_prescription_item__frequency')),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinic.id'], name=op.f('fk_prescription_item__clinic'), onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['drug_form_id'], ['drug_form.id'], name=op.f('fk_prescription_item__drug_form'), onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['prescription_id'], ['prescription.id'], name=op.f('fk_prescription_item__prescription'), onupdate='RESTRICT', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_prescription_item')),
    sa.UniqueConstraint('public_id', name=op.f('uq_prescription_item__public_id'))
    )
    op.create_index(op.f('ix_prescription_item__clinic_id'), 'prescription_item', ['clinic_id'], unique=False)
    op.create_index('ix_prescription_item__clinic_id__prescription_id__sort_order', 'prescription_item', ['clinic_id', 'prescription_id', 'sort_order'], unique=False)

    op.add_column(
        "patient_medication",
        sa.Column("prescription_item_id", mysql.BIGINT(unsigned=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_patient_medication__prescription_item",
        "patient_medication",
        "prescription_item",
        ["prescription_item_id"],
        ["id"],
        onupdate="RESTRICT",
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_patient_medication__drug",
        "patient_medication",
        "drug",
        ["drug_id"],
        ["id"],
        onupdate="RESTRICT",
        ondelete="RESTRICT",
    )

def downgrade() -> None:
    op.drop_constraint(
        "fk_patient_medication__drug", "patient_medication", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_patient_medication__prescription_item",
        "patient_medication",
        type_="foreignkey",
    )
    op.drop_column("patient_medication", "prescription_item_id")
    op.drop_table("prescription_item")
    op.drop_table("prescription")
    op.drop_table("formulary_entry")
    op.drop_table("calculation_result")
    op.drop_table("prescription_template")
    op.drop_table("prescription_request_idempotency")
    op.drop_table("drug_form")
    op.drop_table("drug")
