-- =============================================================================
-- EntShifa Phase 1 database schema (MySQL 8)
-- Scope: architecture sections 25.1–25.4 only (24 tables).
-- Conventions: architecture section 23, AGENTS.md, .cursor/rules/database.mdc
--
-- Deferred foreign keys (columns present; constraints added in a later migration
-- when the referenced tables exist):
--   clinic.logo_attachment_id              -> attachment.id
--   user.signature_attachment_id           -> attachment.id
--   patient.insurance_scheme_id            -> insurance_scheme.id
--   patient_medication.drug_id             -> drug.id
--   patient_problem.first_encounter_id     -> encounter.id
--   patient_problem.last_encounter_id      -> encounter.id
--   appointment.created_from_recall_id     -> recall.id
--
-- code_system.release_version stores architecture 25.2 field "version" (VARCHAR);
-- column "version" is the optimistic-lock counter from section 23.
-- =============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- -----------------------------------------------------------------------------
-- 25.1 IDENTITY AND TENANCY
-- -----------------------------------------------------------------------------

CREATE TABLE clinic (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    name VARCHAR(160) NOT NULL,
    legal_name VARCHAR(160) NULL,
    slug VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    default_locale VARCHAR(10) NOT NULL,
    supported_locales JSON NOT NULL,
    timezone VARCHAR(64) NOT NULL,
    country_code CHAR(2) NOT NULL,
    currency CHAR(3) NOT NULL,
    address_line1 VARCHAR(160) NULL,
    address_line2 VARCHAR(160) NULL,
    city VARCHAR(80) NULL,
    postal_code VARCHAR(20) NULL,
    phone VARCHAR(32) NULL,
    email VARCHAR(160) NULL,
    website VARCHAR(160) NULL,
    tax_id VARCHAR(40) NULL,
    registration_number VARCHAR(40) NULL,
    logo_attachment_id BIGINT UNSIGNED NULL,
    settings JSON NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_clinic__public_id UNIQUE (public_id),
    CONSTRAINT uq_clinic__slug UNIQUE (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `user` (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    email VARCHAR(190) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    email_verified_at DATETIME(6) NULL,
    password_hash VARCHAR(255) NOT NULL,
    password_changed_at DATETIME(6) NOT NULL,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    title VARCHAR(40) NULL,
    specialty VARCHAR(80) NULL,
    license_number VARCHAR(60) NULL,
    signature_attachment_id BIGINT UNSIGNED NULL,
    preferred_locale VARCHAR(10) NOT NULL,
    timezone VARCHAR(64) NOT NULL,
    mfa_secret VARBINARY(255) NULL,
    mfa_enabled TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    last_login_at DATETIME(6) NULL,
    failed_login_count SMALLINT NOT NULL DEFAULT 0,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_user__public_id UNIQUE (public_id),
    CONSTRAINT uq_user__email UNIQUE (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE site (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    clinic_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(160) NOT NULL,
    address_line1 VARCHAR(160) NULL,
    address_line2 VARCHAR(160) NULL,
    city VARCHAR(80) NULL,
    postal_code VARCHAR(20) NULL,
    phone VARCHAR(32) NULL,
    is_primary TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_site__public_id UNIQUE (public_id),
    CONSTRAINT fk_site__clinic FOREIGN KEY (clinic_id) REFERENCES clinic (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    INDEX ix_site__clinic_id (clinic_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE permission (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    code VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    group_code VARCHAR(40) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_permission__public_id UNIQUE (public_id),
    CONSTRAINT uq_permission__code UNIQUE (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE role (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    clinic_id BIGINT UNSIGNED NULL,
    code VARCHAR(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    name_key VARCHAR(80) NOT NULL,
    is_system TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_role__public_id UNIQUE (public_id),
    CONSTRAINT fk_role__clinic FOREIGN KEY (clinic_id) REFERENCES clinic (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    INDEX ix_role__clinic_id__code (clinic_id, code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE role_permission (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    role_id BIGINT UNSIGNED NOT NULL,
    permission_id BIGINT UNSIGNED NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_role_permission__public_id UNIQUE (public_id),
    CONSTRAINT uq_role_permission__role_id__permission_id UNIQUE (role_id, permission_id),
    CONSTRAINT fk_role_permission__role FOREIGN KEY (role_id) REFERENCES role (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_role_permission__permission FOREIGN KEY (permission_id) REFERENCES permission (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE user_clinic_role (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    clinic_id BIGINT UNSIGNED NOT NULL,
    role_id BIGINT UNSIGNED NOT NULL,
    site_id BIGINT UNSIGNED NULL,
    starts_on DATE NOT NULL,
    ends_on DATE NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_user_clinic_role__public_id UNIQUE (public_id),
    CONSTRAINT uq_user_clinic_role__user_id__clinic_id__role_id UNIQUE (user_id, clinic_id, role_id),
    CONSTRAINT fk_user_clinic_role__user FOREIGN KEY (user_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_user_clinic_role__clinic FOREIGN KEY (clinic_id) REFERENCES clinic (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_user_clinic_role__role FOREIGN KEY (role_id) REFERENCES role (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_user_clinic_role__site FOREIGN KEY (site_id) REFERENCES site (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    INDEX ix_user_clinic_role__clinic_id__user_id (clinic_id, user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE user_session (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    refresh_token_hash CHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    device_label VARCHAR(120) NULL,
    ip_address VARBINARY(16) NULL,
    user_agent VARCHAR(255) NULL,
    issued_at DATETIME(6) NOT NULL,
    expires_at DATETIME(6) NOT NULL,
    revoked_at DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_user_session__public_id UNIQUE (public_id),
    CONSTRAINT fk_user_session__user FOREIGN KEY (user_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    INDEX ix_user_session__user_id__expires_at (user_id, expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------------------------------
-- 25.2 TERMINOLOGY
-- -----------------------------------------------------------------------------

CREATE TABLE code_system (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    code VARCHAR(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    name VARCHAR(120) NOT NULL,
    release_version VARCHAR(40) NOT NULL COMMENT 'architecture field: version',
    uri VARCHAR(255) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_code_system__public_id UNIQUE (public_id),
    CONSTRAINT uq_code_system__code UNIQUE (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE concept (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    code_system_id BIGINT UNSIGNED NOT NULL,
    code VARCHAR(60) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    kind VARCHAR(40) NOT NULL,
    parent_id BIGINT UNSIGNED NULL,
    numeric_value DECIMAL(10, 3) NULL,
    sort_order INT NOT NULL DEFAULT 0,
    properties JSON NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    clinic_id BIGINT UNSIGNED NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_concept__public_id UNIQUE (public_id),
    CONSTRAINT uq_concept__code_system_id__code UNIQUE (code_system_id, code),
    CONSTRAINT fk_concept__code_system FOREIGN KEY (code_system_id) REFERENCES code_system (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_concept__parent FOREIGN KEY (parent_id) REFERENCES concept (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_concept__clinic FOREIGN KEY (clinic_id) REFERENCES clinic (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    INDEX ix_concept__kind__parent_id (kind, parent_id),
    INDEX ix_concept__clinic_id__kind (clinic_id, kind)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE concept_translation (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    concept_id BIGINT UNSIGNED NOT NULL,
    locale VARCHAR(10) NOT NULL,
    display VARCHAR(255) NOT NULL,
    full_name VARCHAR(400) NULL,
    abbreviation VARCHAR(40) NULL,
    patient_friendly VARCHAR(400) NULL,
    synonyms JSON NULL,
    clinic_id BIGINT UNSIGNED NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_concept_translation__public_id UNIQUE (public_id),
    CONSTRAINT uq_concept_translation__concept_id__locale__clinic_id
        UNIQUE (concept_id, locale, clinic_id),
    CONSTRAINT fk_concept_translation__concept FOREIGN KEY (concept_id) REFERENCES concept (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_concept_translation__clinic FOREIGN KEY (clinic_id) REFERENCES clinic (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    FULLTEXT INDEX ft_concept_translation__display__full_name (display, full_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE concept_relationship (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    source_concept_id BIGINT UNSIGNED NOT NULL,
    target_concept_id BIGINT UNSIGNED NOT NULL,
    type VARCHAR(40) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_concept_relationship__public_id UNIQUE (public_id),
    CONSTRAINT fk_concept_relationship__source FOREIGN KEY (source_concept_id) REFERENCES concept (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_concept_relationship__target FOREIGN KEY (target_concept_id) REFERENCES concept (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    INDEX ix_concept_relationship__source_concept_id__type (source_concept_id, type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE value_set (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    code VARCHAR(60) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    name_key VARCHAR(80) NOT NULL,
    description_key VARCHAR(120) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_value_set__public_id UNIQUE (public_id),
    CONSTRAINT uq_value_set__code UNIQUE (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE value_set_member (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    value_set_id BIGINT UNSIGNED NOT NULL,
    concept_id BIGINT UNSIGNED NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    is_default TINYINT(1) NOT NULL DEFAULT 0,
    clinic_id BIGINT UNSIGNED NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_value_set_member__public_id UNIQUE (public_id),
    CONSTRAINT uq_value_set_member__value_set_id__concept_id__clinic_id
        UNIQUE (value_set_id, concept_id, clinic_id),
    CONSTRAINT fk_value_set_member__value_set FOREIGN KEY (value_set_id) REFERENCES value_set (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_value_set_member__concept FOREIGN KEY (concept_id) REFERENCES concept (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_value_set_member__clinic FOREIGN KEY (clinic_id) REFERENCES clinic (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    INDEX ix_value_set_member__value_set_id__sort_order (value_set_id, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------------------------------
-- 25.3 PATIENT
-- -----------------------------------------------------------------------------

CREATE TABLE patient (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    clinic_id BIGINT UNSIGNED NOT NULL,
    mrn VARCHAR(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    first_name_alt VARCHAR(80) NULL,
    last_name_alt VARCHAR(80) NULL,
    name_normalized VARCHAR(190) NOT NULL,
    birth_date DATE NOT NULL,
    birth_date_is_estimated TINYINT(1) NOT NULL DEFAULT 0,
    sex VARCHAR(10) NOT NULL,
    preferred_locale VARCHAR(10) NOT NULL,
    phone_primary VARCHAR(32) NULL,
    phone_secondary VARCHAR(32) NULL,
    email VARCHAR(190) NULL,
    address_line1 VARCHAR(160) NULL,
    address_line2 VARCHAR(160) NULL,
    city VARCHAR(80) NULL,
    postal_code VARCHAR(20) NULL,
    country_code CHAR(2) NULL,
    occupation VARCHAR(120) NULL,
    noise_exposure VARCHAR(40) NULL,
    smoking_status VARCHAR(30) NULL,
    alcohol_status VARCHAR(30) NULL,
    insurance_scheme_id BIGINT UNSIGNED NULL,
    insurance_number VARCHAR(60) NULL,
    referring_doctor_name VARCHAR(160) NULL,
    referring_doctor_phone VARCHAR(32) NULL,
    referring_doctor_email VARCHAR(190) NULL,
    referring_doctor_locale VARCHAR(10) NULL,
    guardian_name VARCHAR(160) NULL,
    guardian_relation VARCHAR(40) NULL,
    emergency_contact_name VARCHAR(160) NULL,
    emergency_contact_phone VARCHAR(32) NULL,
    consent_sms TINYINT(1) NOT NULL DEFAULT 0,
    consent_email TINYINT(1) NOT NULL DEFAULT 0,
    consent_teaching TINYINT(1) NOT NULL DEFAULT 0,
    is_deceased TINYINT(1) NOT NULL DEFAULT 0,
    deceased_date DATE NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_patient__public_id UNIQUE (public_id),
    CONSTRAINT uq_patient__clinic_id__mrn UNIQUE (clinic_id, mrn),
    CONSTRAINT fk_patient__clinic FOREIGN KEY (clinic_id) REFERENCES clinic (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT chk_patient__sex CHECK (sex IN ('male', 'female', 'other', 'unknown')),
    INDEX ix_patient__clinic_id__name_normalized (clinic_id, name_normalized),
    INDEX ix_patient__clinic_id__phone_primary (clinic_id, phone_primary),
    INDEX ix_patient__clinic_id__birth_date (clinic_id, birth_date),
    FULLTEXT INDEX ft_patient__names (first_name, last_name, first_name_alt, last_name_alt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE patient_identifier (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    clinic_id BIGINT UNSIGNED NOT NULL,
    patient_id BIGINT UNSIGNED NOT NULL,
    type VARCHAR(40) NOT NULL,
    value VARCHAR(80) NOT NULL,
    issuing_country CHAR(2) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_patient_identifier__public_id UNIQUE (public_id),
    CONSTRAINT fk_patient_identifier__clinic FOREIGN KEY (clinic_id) REFERENCES clinic (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_patient_identifier__patient FOREIGN KEY (patient_id) REFERENCES patient (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    INDEX ix_patient_identifier__clinic_id__patient_id (clinic_id, patient_id),
    INDEX ix_patient_identifier__clinic_id__type__value (clinic_id, type, value)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE patient_allergy (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    clinic_id BIGINT UNSIGNED NOT NULL,
    patient_id BIGINT UNSIGNED NOT NULL,
    substance_concept_id BIGINT UNSIGNED NOT NULL,
    category VARCHAR(30) NOT NULL,
    reaction_concept_id BIGINT UNSIGNED NULL,
    severity VARCHAR(20) NULL,
    onset_date DATE NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    note TEXT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_patient_allergy__public_id UNIQUE (public_id),
    CONSTRAINT fk_patient_allergy__clinic FOREIGN KEY (clinic_id) REFERENCES clinic (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_patient_allergy__patient FOREIGN KEY (patient_id) REFERENCES patient (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_patient_allergy__substance_concept FOREIGN KEY (substance_concept_id) REFERENCES concept (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_patient_allergy__reaction_concept FOREIGN KEY (reaction_concept_id) REFERENCES concept (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT chk_patient_allergy__category CHECK (category IN ('drug', 'food', 'other')),
    CONSTRAINT chk_patient_allergy__severity CHECK (
        severity IS NULL OR severity IN ('mild', 'moderate', 'severe')
    ),
    INDEX ix_patient_allergy__clinic_id__patient_id__is_active (clinic_id, patient_id, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE patient_medication (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    clinic_id BIGINT UNSIGNED NOT NULL,
    patient_id BIGINT UNSIGNED NOT NULL,
    drug_id BIGINT UNSIGNED NULL,
    free_text_name VARCHAR(160) NULL,
    dose VARCHAR(60) NULL,
    frequency VARCHAR(60) NULL,
    route VARCHAR(30) NULL,
    started_on DATE NULL,
    stopped_on DATE NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    is_anticoagulant TINYINT(1) NOT NULL DEFAULT 0,
    is_ototoxic TINYINT(1) NOT NULL DEFAULT 0,
    source VARCHAR(30) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_patient_medication__public_id UNIQUE (public_id),
    CONSTRAINT fk_patient_medication__clinic FOREIGN KEY (clinic_id) REFERENCES clinic (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_patient_medication__patient FOREIGN KEY (patient_id) REFERENCES patient (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT chk_patient_medication__source CHECK (
        source IN ('prescribed_here', 'reported', 'external')
    ),
    INDEX ix_patient_medication__clinic_id__patient_id__is_active (clinic_id, patient_id, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE patient_flag (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    clinic_id BIGINT UNSIGNED NOT NULL,
    patient_id BIGINT UNSIGNED NOT NULL,
    flag_code VARCHAR(60) NOT NULL,
    laterality VARCHAR(10) NULL,
    severity VARCHAR(20) NULL,
    detail JSON NULL,
    started_on DATE NOT NULL,
    ended_on DATE NULL,
    is_auto TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_patient_flag__public_id UNIQUE (public_id),
    CONSTRAINT fk_patient_flag__clinic FOREIGN KEY (clinic_id) REFERENCES clinic (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_patient_flag__patient FOREIGN KEY (patient_id) REFERENCES patient (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT chk_patient_flag__laterality CHECK (
        laterality IS NULL
        OR laterality IN ('right', 'left', 'bilateral', 'midline', 'na')
    ),
    INDEX ix_patient_flag__clinic_id__patient_id__ended_on (clinic_id, patient_id, ended_on)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE patient_problem (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    clinic_id BIGINT UNSIGNED NOT NULL,
    patient_id BIGINT UNSIGNED NOT NULL,
    diagnosis_concept_id BIGINT UNSIGNED NOT NULL,
    laterality VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL,
    onset_date DATE NULL,
    resolved_date DATE NULL,
    first_encounter_id BIGINT UNSIGNED NULL,
    last_encounter_id BIGINT UNSIGNED NULL,
    note TEXT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_patient_problem__public_id UNIQUE (public_id),
    CONSTRAINT fk_patient_problem__clinic FOREIGN KEY (clinic_id) REFERENCES clinic (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_patient_problem__patient FOREIGN KEY (patient_id) REFERENCES patient (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_patient_problem__diagnosis_concept FOREIGN KEY (diagnosis_concept_id) REFERENCES concept (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT chk_patient_problem__laterality CHECK (
        laterality IN ('right', 'left', 'bilateral', 'midline', 'na')
    ),
    CONSTRAINT chk_patient_problem__status CHECK (
        status IN ('active', 'resolved', 'suspected', 'ruled_out')
    ),
    INDEX ix_patient_problem__clinic_id__patient_id__status (clinic_id, patient_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE patient_history (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    clinic_id BIGINT UNSIGNED NOT NULL,
    patient_id BIGINT UNSIGNED NOT NULL,
    category VARCHAR(40) NOT NULL,
    concept_id BIGINT UNSIGNED NULL,
    free_text VARCHAR(400) NULL,
    laterality VARCHAR(10) NULL,
    occurred_year SMALLINT NULL,
    occurred_date DATE NULL,
    detail JSON NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_patient_history__public_id UNIQUE (public_id),
    CONSTRAINT fk_patient_history__clinic FOREIGN KEY (clinic_id) REFERENCES clinic (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_patient_history__patient FOREIGN KEY (patient_id) REFERENCES patient (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_patient_history__concept FOREIGN KEY (concept_id) REFERENCES concept (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT chk_patient_history__category CHECK (
        category IN (
            'ent_surgery', 'other_surgery', 'medical', 'family', 'social', 'obstetric'
        )
    ),
    CONSTRAINT chk_patient_history__laterality CHECK (
        laterality IS NULL
        OR laterality IN ('right', 'left', 'bilateral', 'midline', 'na')
    ),
    INDEX ix_patient_history__clinic_id__patient_id__category (clinic_id, patient_id, category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE patient_merge_log (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    clinic_id BIGINT UNSIGNED NOT NULL,
    surviving_patient_id BIGINT UNSIGNED NOT NULL,
    merged_patient_id BIGINT UNSIGNED NOT NULL,
    merged_by_id BIGINT UNSIGNED NOT NULL,
    reason TEXT NOT NULL,
    payload JSON NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_patient_merge_log__public_id UNIQUE (public_id),
    CONSTRAINT fk_patient_merge_log__clinic FOREIGN KEY (clinic_id) REFERENCES clinic (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_patient_merge_log__surviving_patient FOREIGN KEY (surviving_patient_id) REFERENCES patient (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_patient_merge_log__merged_patient FOREIGN KEY (merged_patient_id) REFERENCES patient (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_patient_merge_log__merged_by FOREIGN KEY (merged_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    INDEX ix_patient_merge_log__clinic_id__created_at (clinic_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------------------------------
-- 25.4 SCHEDULING
-- -----------------------------------------------------------------------------

CREATE TABLE appointment_type (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    clinic_id BIGINT UNSIGNED NOT NULL,
    code VARCHAR(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    name_key VARCHAR(80) NOT NULL,
    default_duration_min SMALLINT NOT NULL,
    color VARCHAR(12) NOT NULL,
    requires_room TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_appointment_type__public_id UNIQUE (public_id),
    CONSTRAINT uq_appointment_type__clinic_id__code UNIQUE (clinic_id, code),
    CONSTRAINT fk_appointment_type__clinic FOREIGN KEY (clinic_id) REFERENCES clinic (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE appointment (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs NOT NULL,
    clinic_id BIGINT UNSIGNED NOT NULL,
    site_id BIGINT UNSIGNED NOT NULL,
    patient_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    appointment_type_id BIGINT UNSIGNED NOT NULL,
    starts_at DATETIME(6) NOT NULL,
    ends_at DATETIME(6) NOT NULL,
    status VARCHAR(20) NOT NULL,
    reason_text VARCHAR(255) NULL,
    room VARCHAR(40) NULL,
    created_from_recall_id BIGINT UNSIGNED NULL,
    arrived_at DATETIME(6) NULL,
    started_at DATETIME(6) NULL,
    ended_at DATETIME(6) NULL,
    cancellation_reason VARCHAR(160) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    created_by_id BIGINT UNSIGNED NULL,
    updated_by_id BIGINT UNSIGNED NULL,
    deleted_at DATETIME(6) NULL,
    deleted_by_id BIGINT UNSIGNED NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_appointment__public_id UNIQUE (public_id),
    CONSTRAINT fk_appointment__clinic FOREIGN KEY (clinic_id) REFERENCES clinic (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_appointment__site FOREIGN KEY (site_id) REFERENCES site (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_appointment__patient FOREIGN KEY (patient_id) REFERENCES patient (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_appointment__user FOREIGN KEY (user_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_appointment__appointment_type FOREIGN KEY (appointment_type_id) REFERENCES appointment_type (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT chk_appointment__status CHECK (
        status IN (
            'scheduled', 'arrived', 'in_room', 'completed', 'no_show', 'cancelled'
        )
    ),
    INDEX ix_appointment__clinic_id__user_id__starts_at (clinic_id, user_id, starts_at),
    INDEX ix_appointment__clinic_id__patient_id__starts_at (clinic_id, patient_id, starts_at),
    INDEX ix_appointment__clinic_id__status__starts_at (clinic_id, status, starts_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------------------------------
-- Audit column foreign keys to user (deferred until user exists)
-- -----------------------------------------------------------------------------

ALTER TABLE clinic
    ADD CONSTRAINT fk_clinic__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_clinic__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_clinic__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE `user`
    ADD CONSTRAINT fk_user__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_user__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_user__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE site
    ADD CONSTRAINT fk_site__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_site__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_site__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE permission
    ADD CONSTRAINT fk_permission__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_permission__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_permission__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE role
    ADD CONSTRAINT fk_role__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_role__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_role__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE role_permission
    ADD CONSTRAINT fk_role_permission__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_role_permission__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_role_permission__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE user_clinic_role
    ADD CONSTRAINT fk_user_clinic_role__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_user_clinic_role__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_user_clinic_role__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE user_session
    ADD CONSTRAINT fk_user_session__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_user_session__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_user_session__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE code_system
    ADD CONSTRAINT fk_code_system__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_code_system__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_code_system__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE concept
    ADD CONSTRAINT fk_concept__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_concept__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_concept__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE concept_translation
    ADD CONSTRAINT fk_concept_translation__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_concept_translation__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_concept_translation__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE concept_relationship
    ADD CONSTRAINT fk_concept_relationship__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_concept_relationship__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_concept_relationship__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE value_set
    ADD CONSTRAINT fk_value_set__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_value_set__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_value_set__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE value_set_member
    ADD CONSTRAINT fk_value_set_member__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_value_set_member__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_value_set_member__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE patient
    ADD CONSTRAINT fk_patient__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_patient__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_patient__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE patient_identifier
    ADD CONSTRAINT fk_patient_identifier__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_patient_identifier__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_patient_identifier__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE patient_allergy
    ADD CONSTRAINT fk_patient_allergy__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_patient_allergy__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_patient_allergy__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE patient_medication
    ADD CONSTRAINT fk_patient_medication__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_patient_medication__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_patient_medication__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE patient_flag
    ADD CONSTRAINT fk_patient_flag__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_patient_flag__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_patient_flag__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE patient_problem
    ADD CONSTRAINT fk_patient_problem__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_patient_problem__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_patient_problem__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE patient_history
    ADD CONSTRAINT fk_patient_history__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_patient_history__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_patient_history__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE patient_merge_log
    ADD CONSTRAINT fk_patient_merge_log__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_patient_merge_log__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_patient_merge_log__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE appointment_type
    ADD CONSTRAINT fk_appointment_type__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_appointment_type__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_appointment_type__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE appointment
    ADD CONSTRAINT fk_appointment__created_by FOREIGN KEY (created_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_appointment__updated_by FOREIGN KEY (updated_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    ADD CONSTRAINT fk_appointment__deleted_by FOREIGN KEY (deleted_by_id) REFERENCES `user` (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT;

SET FOREIGN_KEY_CHECKS = 1;
