"""Audiogram entry constants (feature spec §8.1)."""

from __future__ import annotations

EARS = ("right", "left")
CONDUCTION_TYPES = ("air", "bone")
STANDARD_FREQUENCIES_HZ = (
    125,
    250,
    500,
    750,
    1000,
    1500,
    2000,
    3000,
    4000,
    6000,
    8000,
)
EXTENDED_HIGH_FREQUENCIES_HZ = (10000, 12500, 14000, 16000)
ALL_FREQUENCIES_HZ = STANDARD_FREQUENCIES_HZ + EXTENDED_HIGH_FREQUENCIES_HZ
BONE_FREQUENCIES_HZ = (
    250,
    500,
    750,
    1000,
    1500,
    2000,
    3000,
    4000,
    6000,
    8000,
)
TRANSDUCERS = ("headphones", "inserts", "free_field", "bone_oscillator")
TEST_METHODS = ("standard", "play", "vra", "boa", "soundfield")
RELIABILITY_VALUES = ("good", "fair", "poor")
AUDIOGRAM_STATUSES = ("draft", "final")
PTA_FORMULAS = ("3freq", "4freq_who", "high_freq", "fletcher")
MIN_LEVEL_DB = -10
MAX_LEVEL_DB = 130

PROBE_TONE_HZ = (226, 1000)
JERGER_TYPES = ("A", "As", "Ad", "B", "C")
ETF_RESULTS = ("intact", "impaired", "patulous", "not_performed")
ACOUSTIC_REFLEX_FREQUENCIES_HZ = (500, 1000, 2000, 4000)
ACOUSTIC_REFLEX_MODES = ("ipsi", "contra")
ACOUSTIC_REFLEX_STATUSES = ("present", "absent", "elevated", "not_tested")
OAE_TYPES = ("teoae", "dpoae")
OAE_OVERALL_RESULTS = ("pass", "refer", "partial", "not_testable")
OAE_SCREENING_STAGES = ("first", "second", "diagnostic")
OAE_BAND_STATUSES = ("present", "absent", "partial")
ABR_STIMULI = ("click", "tone_burst", "assr")
ABR_MORPHOLOGIES = ("normal", "poor", "absent", "reproducible")

SPEECH_RESOURCE_CREATE = "speech_audiometry.create"
TYMPANOMETRY_RESOURCE_CREATE = "tympanometry.create"
OAE_RESOURCE_CREATE = "oae_result.create"
ABR_RESOURCE_CREATE = "abr_result.create"

HEARING_DEVICE_TYPES = (
    "bte",
    "ric",
    "ite",
    "cros",
    "bone_conduction",
    "cochlear_implant",
    "middle_ear_implant",
)
HEARING_DEVICE_STATUSES = ("active", "trial", "inactive", "replaced", "removed")
NEWBORN_SCREEN_RESULTS = ("pass", "refer", "not_tested")
DIAGNOSTIC_ABR_RESULTS = ("normal", "elevated", "absent", "not_tested")
INTERVENTION_TYPES = (
    "hearing_aid",
    "cochlear_implant",
    "speech_therapy",
    "early_intervention",
    "monitoring",
)
EHDI_BENCHMARK_STATUSES = (
    "not_applicable",
    "pending",
    "met",
    "late",
    "overdue",
)
OME_STATUSES = (
    "watchful_waiting",
    "resolved",
    "persisted_tubes_proposed",
    "tubes_inserted",
)
CANDIDACY_KINDS = ("hearing_aid", "cochlear_implant")

HEARING_DEVICE_RESOURCE_CREATE = "hearing_device.create"
OME_EPISODE_RESOURCE_CREATE = "ome_episode.create"
