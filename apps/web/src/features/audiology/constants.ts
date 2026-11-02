/** Audiogram display constants (feature spec §8.1, backend constants.py). */

export const STANDARD_FREQUENCIES_HZ = [
  125, 250, 500, 750, 1000, 1500, 2000, 3000, 4000, 6000, 8000,
] as const;

export const EXTENDED_HIGH_FREQUENCIES_HZ = [
  10000, 12500, 14000, 16000,
] as const;

export const BONE_FREQUENCIES_HZ = [
  250, 500, 750, 1000, 1500, 2000, 3000, 4000, 6000, 8000,
] as const;

export const MIN_LEVEL_DB = -10;
export const MAX_LEVEL_DB = 130;
export const LEVEL_STEP_DB = 5;

export const CHART_DB_TICKS = [
  -10, 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130,
] as const;

export const TRANSDUCERS = [
  "headphones",
  "inserts",
  "free_field",
  "bone_oscillator",
] as const;

export const TEST_METHODS = [
  "standard",
  "play",
  "vra",
  "boa",
  "soundfield",
] as const;

export const RELIABILITY_VALUES = ["good", "fair", "poor"] as const;

export const EARS = ["right", "left"] as const;
export const CONDUCTIONS = ["air", "bone"] as const;

export const RIGHT_COLOR = "#dc2626";
export const LEFT_COLOR = "#2563eb";

export const CHART_PADDING = { top: 24, right: 24, bottom: 40, left: 48 };
export const CHART_WIDTH = 720;
export const CHART_HEIGHT = 420;

export const GRID_ROWS = [
  { ear: "right", conduction: "air", isMasked: false },
  { ear: "right", conduction: "air", isMasked: true },
  { ear: "left", conduction: "air", isMasked: false },
  { ear: "left", conduction: "air", isMasked: true },
  { ear: "right", conduction: "bone", isMasked: false },
  { ear: "right", conduction: "bone", isMasked: true },
  { ear: "left", conduction: "bone", isMasked: false },
  { ear: "left", conduction: "bone", isMasked: true },
] as const;
