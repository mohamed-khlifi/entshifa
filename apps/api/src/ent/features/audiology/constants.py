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
